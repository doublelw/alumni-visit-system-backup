@wechat_bp.route('/teacher/add-visitor', methods=['POST'])
@wechat_auth_required
def teacher_add_visitor():
    """
    老师添加访客（从外网获取访客信息后创建内网账号）

    新架构：外网/内网分离
    - 外网：只存储访客码+手机号（模拟腾讯云托管）
    - 内网：存储完整的访客信息和访问记录

    流程：
    1. 老师输入访客码
    2. 从外网获取访客基本信息（手机号）
    3. 老师补充详细信息（姓名、身份证等）
    4. 在内网创建完整的访客账号
    5. 标记外网码已使用

    请求体:
    {
        "access_code": "123456",  # 访客码（必填）
        "name": "张三",            # 姓名（必填）
        "id_card": "110101...",    # 身份证（可选）
        "visit_purpose": "meeting", # 访问目的（可选）
        "visit_reason": "商务洽谈"  # 访问说明（可选）
    }

    返回:
    {
        "success": true,
        "data": {
            "visitor": {
                "name": "张三",
                "phone": "13800138000"
            },
            "access_code": "123456",
            "message": "访客添加成功"
        }
    }
    """
    try:
        from app.models.user import User
        from app.models.visit_application import VisitApplication
        import requests

        data = request.get_json()
        access_code = data.get('access_code', '').strip()
        name = data.get('name', '').strip()
        id_card = data.get('id_card', '').strip()
        visit_purpose = data.get('visit_purpose', 'other')
        visit_reason = data.get('visit_reason', '').strip()

        current_app.logger.info(f"📝 老师验证访客码: {access_code}")

        # ========== 第一步：验证访问码格式 ==========
        if not access_code:
            return jsonify({'error': '缺少访客码'}), 400

        if not re.match(r'^\d{6}$', access_code):
            return jsonify({'error': '访客码格式不正确，必须是6位数字'}), 400

        # ========== 第二步：从外网获取访客基本信息 ==========
        try:
            # 调用外网API获取访客信息
            external_url = f"http://localhost:5000/external/visitor/info/{access_code}"
            current_app.logger.info(f"  🔍 从外网查询访客信息: {external_url}")

            response = requests.get(external_url, timeout=5)
            external_data = response.json()

            if not external_data.get('exists'):
                current_app.logger.warning(f"  ❌ 外网中不存在此访客码: {access_code}")
                return jsonify({
                    'error': '访客码无效或已过期',
                    'details': '请确认访客已在系统中登记，且访客码在24小时有效期内'
                }), 404

            visitor_basic_info = external_data.get('visitor_info', {})
            phone = visitor_basic_info.get('phone', '')

            if not phone:
                current_app.logger.error(f"  ❌ 外网数据异常：缺少手机号")
                return jsonify({'error': '外网数据异常：缺少手机号'}), 500

            current_app.logger.info(f"  ✅ 从外网获取到手机号: {phone}")

        except requests.RequestException as e:
            current_app.logger.error(f"  ❌ 外网请求失败: {e}")
            return jsonify({
                'error': '无法连接到外网服务',
                'details': '请检查网络连接或稍后重试'
            }), 503
        except Exception as e:
            current_app.logger.error(f"  ❌ 外网查询异常: {e}")
            return jsonify({
                'error': '外网查询失败',
                'details': str(e)
            }), 500

        # ========== 第三步：验证老师输入的详细信息 ==========
        if not name:
            return jsonify({'error': '请输入访客姓名'}), 400

        # 手机号格式验证（外网已验证，这里再次确认）
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'error': f'手机号格式不正确: {phone}'}), 400

        # ========== 第四步：检查内网是否已有此访客 ==========
        existing_visitor = User.query.filter_by(phone=phone).first()
        if existing_visitor:
            current_app.logger.info(f"  ℹ️ 内网中访客已存在: {existing_visitor.real_name}")

            # 创建新的访问记录
            application = VisitApplication(
                applicant_id=existing_visitor.id,
                visit_date=datetime.now().date(),
                visit_time_start=time(8, 0),
                visit_time_end=time(20, 0),
                visit_purpose=visit_purpose,
                target_person=name,
                qr_code=access_code,
                application_status='approved',
                approved_by=request.current_user_id,
                approval_time=datetime.now(),
                access_code=access_code,
                notes=visit_reason
            )

            db.session.add(application)
            db.session.commit()

            # 标记外网码已使用
            try:
                requests.post(f"http://localhost:5000/external/visitor/mark-used",
                            json={'code': access_code}, timeout=5)
                current_app.logger.info(f"  ✅ 已标记外网码使用")
            except:
                pass  # 标记失败不影响主流程

            return jsonify({
                'success': True,
                'data': {
                    'visitor': {
                        'name': existing_visitor.real_name,
                        'phone': existing_visitor.phone
                    },
                    'access_code': access_code,
                    'message': '访客已存在，已创建新的访问记录'
                }
            })

        # ========== 第五步：在内网创建新访客账号 ==========
        # 查找最大用户ID
        max_user = User.query.order_by(User.id.desc()).first()
        new_id = (max_user.id + 1) if max_user else 1

        # 生成默认密码（手机号后6位）
        default_password = phone[-6:] if len(phone) >= 6 else phone

        # 创建访客账号（内网存储完整信息）
        visitor = User(
            id=new_id,
            real_name=name,
            phone=phone,
            id_card=id_card if id_card else None,
            user_type='visitor',
            status='active',
            wechat_password=default_password,
            organization_id=1  # 默认组织
        )

        db.session.add(visitor)
        db.session.flush()  # 获取visitor.id

        current_app.logger.info(f"  ✅ 创建内网访客账号: ID={visitor.id}, 姓名={name}, 手机={phone}")

        # ========== 第六步：创建访问申请记录 ==========
        application = VisitApplication(
            applicant_id=visitor.id,
            visit_date=datetime.now().date(),
            visit_time_start=time(8, 0),
            visit_time_end=time(20, 0),
            visit_purpose=visit_purpose,
            target_person=name,
            qr_code=access_code,
            application_status='approved',
            approved_by=request.current_user_id,
            approval_time=datetime.now(),
            access_code=access_code,
            notes=visit_reason
        )

        db.session.add(application)
        db.session.commit()

        current_app.logger.info(f"  ✅ 内网访客添加成功: 访客码={access_code}")

        # ========== 第七步：标记外网码已使用 ==========
        try:
            requests.post(f"http://localhost:5000/external/visitor/mark-used",
                        json={'code': access_code}, timeout=5)
            current_app.logger.info(f"  ✅ 已标记外网码使用，访客信息已从外网迁移到内网")
        except Exception as e:
            current_app.logger.warning(f"  ⚠️ 标记外网码使用失败: {e}（不影响主流程）")

        # ========== 第八步：返回成功结果 ==========
        return jsonify({
            'success': True,
            'data': {
                'visitor': {
                    'name': visitor.real_name,
                    'phone': visitor.phone
                },
                'access_code': access_code,
                'message': f'访客添加成功（从外网迁移到内网）'
            }
        })

    except Exception as e:
        current_app.logger.error(f"添加访客失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': '添加失败',
            'details': str(e)
        }), 500
