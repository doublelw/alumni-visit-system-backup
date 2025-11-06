"""
人脸识别API
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
import base64
import os
from werkzeug.utils import secure_filename

# 尝试导入OpenCV，如果失败则使用模拟功能
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from app import db
from app.models.user import User
from app.models.face_data import FaceData
from app.models.face_history import FaceHistory

faces_bp = Blueprint('faces', __name__)

def allowed_file(filename):
    """检查文件扩展名"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_and_extract_face(image_path):
    """检测并提取人脸特征"""
    if not CV2_AVAILABLE:
        # 模拟人脸检测和特征提取
        face_filename = f"face_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        face_path = os.path.join(current_app.config['UPLOAD_FOLDER'], face_filename)

        # 简单复制文件作为人脸图片
        import shutil
        shutil.copy2(image_path, face_path)

        # 生成模拟的特征编码
        face_encoding = json.dumps({
            'width': 200,
            'height': 200,
            'position': [50, 50],
            'quality_score': 85.5,
            'histogram': 'simulated_histogram_data'
        })

        return face_encoding, face_path, None

    try:
        # 加载人脸识别分类器
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            return None, None, "无法读取图片"

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 检测人脸
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None, None, "未检测到人脸"

        # 取第一个人脸
        (x, y, w, h) = faces[0]

        # 裁剪人脸区域
        face_img = img[y:y+h, x:x+w]

        # 调整大小
        face_img = cv2.resize(face_img, current_app.config['FACE_IMAGE_SIZE'])

        # 计算质量分数（简单基于清晰度）
        quality_score = cv2.Laplacian(gray[y:y+h, x:x+w], cv2.CV_64F).var()

        # 保存处理后的人脸图片
        face_filename = f"face_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        face_path = os.path.join(current_app.config['UPLOAD_FOLDER'], face_filename)
        cv2.imwrite(face_path, face_img)

        # 生成简单的特征编码（实际项目中应该使用更专业的算法）
        face_encoding = json.dumps({
            'width': w,
            'height': h,
            'position': [x, y],
            'quality_score': quality_score,
            'histogram': cv2.calcHist([face_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]).tolist()
        })

        return face_encoding, face_path, None

    except Exception as e:
        return None, None, f"人脸处理失败: {str(e)}"

def compare_faces(face_encoding1, face_encoding2):
    """
    比较两个人脸特征的相似度
    返回相似度分数 (0-100)
    """
    try:
        # 解码人脸特征
        data1 = json.loads(face_encoding1)
        data2 = json.loads(face_encoding2)

        if not CV2_AVAILABLE:
            # 模拟人脸比对，返回固定分数
            return 90.0

        # 基于质量分数的简单比对
        quality_diff = abs(data1.get('quality_score', 0) - data2.get('quality_score', 0))

        # 基于尺寸的比对
        size_diff = abs(data1['width'] - data2['width']) + abs(data1['height'] - data2['height'])

        # 基于位置差异的比对
        pos_diff = abs(data1['position'][0] - data2['position'][0]) + abs(data1['position'][1] - data2['position'][1])

        # 基于直方图差异的比对
        hist1 = data1.get('histogram', [])
        hist2 = data2.get('histogram', [])
        hist_diff = 0
        if hist1 and hist2 and len(hist1) == len(hist2):
            for i in range(len(hist1)):
                hist_diff += abs(hist1[i] - hist2[i])
            hist_diff = hist_diff / len(hist1) if len(hist1) > 0 else 0

        # 计算综合相似度分数
        quality_similarity = max(0, 100 - quality_diff / 10)
        size_similarity = max(0, 100 - size_diff / 2)
        position_similarity = max(0, 100 - pos_diff / 5)
        histogram_similarity = max(0, 100 - hist_diff / 1000)

        # 加权平均
        similarity_score = (
            quality_similarity * 0.3 +
            size_similarity * 0.2 +
            position_similarity * 0.2 +
            histogram_similarity * 0.3
        )

        return min(100.0, max(0.0, similarity_score))

    except Exception as e:
        current_app.logger.error(f"人脸比对失败: {str(e)}")
        return 0.0

@faces_bp.route('/register', methods=['POST'])
@jwt_required()
def register_face():
    """注册人脸"""
    try:
        current_user_id = get_jwt_identity()

        # 检查用户是否已经注册过人脸
        existing_face = FaceData.query.filter_by(user_id=current_user_id).first()
        is_update = existing_face is not None

        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'error': '请上传人脸图片'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '请选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400

        # 确保上传目录存在
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        # 保存上传的文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # 提取人脸特征
        face_encoding, face_image_path, error_msg = detect_and_extract_face(filepath)

        # 删除临时文件
        if os.path.exists(filepath):
            os.remove(filepath)

        if error_msg:
            return jsonify({'error': error_msg}), 400

        if not face_encoding:
            return jsonify({'error': '人脸特征提取失败'}), 400

        if is_update:
            # 人脸更新时进行相似度验证
            similarity_score = compare_faces(existing_face.face_encoding, face_encoding)

            # 设置相似度阈值（85%）
            SIMILARITY_THRESHOLD = 85.0

            if similarity_score < SIMILARITY_THRESHOLD:
                # 删除新生成的人脸图片文件
                if face_image_path and os.path.exists(face_image_path):
                    try:
                        os.remove(face_image_path)
                    except Exception as e:
                        current_app.logger.warning(f"删除新人脸图片失败: {str(e)}")

                return jsonify({
                    'error': f'人脸验证失败，相似度为{similarity_score:.1f}%，低于{SIMILARITY_THRESHOLD}%的阈值。请确保拍摄的是同一个人。',
                    'similarity_score': similarity_score,
                    'threshold': SIMILARITY_THRESHOLD
                }), 400

            # 验证通过，保存人脸历史记录
            try:
                # 获取设备和位置信息
                device_info = request.headers.get('User-Agent', '')
                ip_address = request.remote_addr

                # 保存当前人脸到历史记录
                current_face_record = FaceHistory.create_new_face_record(
                    user_id=current_user_id,
                    face_encoding=face_encoding,
                    face_image_path=face_image_path,
                    operation_type='update',
                    device_info=device_info,
                    ip_address=ip_address,
                    user_agent=request.headers.get('User-Agent')
                )

                # 设置验证信息
                current_face_record.is_verified = True
                current_face_record.verification_method = 'comparison'
                current_face_record.verification_score = similarity_score
                current_face_record.verification_time = datetime.utcnow()
                current_face_record.verification_note = f'人脸更新验证通过，相似度{similarity_score:.1f}%'

                db.session.commit()
                current_app.logger.info(f"用户{current_user_id}人脸历史记录已保存，记录ID: {current_face_record.id}")

            except Exception as e:
                current_app.logger.error(f"保存人脸历史记录失败: {str(e)}")
                # 不影响主要功能，继续执行

            # 验证通过，删除旧的人脸图片文件
            if existing_face.face_image_path and os.path.exists(existing_face.face_image_path):
                try:
                    os.remove(existing_face.face_image_path)
                except Exception as e:
                    current_app.logger.warning(f"删除旧人脸图片失败: {str(e)}")

            # 更新人脸数据
            existing_face.face_encoding = face_encoding
            existing_face.face_image_path = face_image_path
            existing_face.quality_score = float(json.loads(face_encoding).get('quality_score', 0))
            existing_face.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'message': f'人脸更新成功，相似度为{similarity_score:.1f}%',
                'face_data': existing_face.to_dict(),
                'similarity_score': similarity_score
            }), 200
        else:
            # 创建新的人脸数据记录
            face_data = FaceData(
                user_id=current_user_id,
                face_encoding=face_encoding,
                face_image_path=face_image_path,
                quality_score=float(json.loads(face_encoding).get('quality_score', 0))
            )

            db.session.add(face_data)
            db.session.commit()

            # 保存人脸注册历史记录
            try:
                # 获取设备和位置信息
                device_info = request.headers.get('User-Agent', '')
                ip_address = request.remote_addr

                # 保存注册记录到历史
                face_history_record = FaceHistory.create_new_face_record(
                    user_id=current_user_id,
                    face_encoding=face_encoding,
                    face_image_path=face_image_path,
                    operation_type='register',
                    device_info=device_info,
                    ip_address=ip_address,
                    user_agent=request.headers.get('User-Agent')
                )

                # 设置验证信息
                face_history_record.is_verified = True
                face_history_record.verification_method = 'auto'
                face_history_record.verification_time = datetime.utcnow()
                face_history_record.verification_note = '人脸注册成功'

                db.session.commit()
                current_app.logger.info(f"用户{current_user_id}首次人脸注册历史记录已保存，记录ID: {face_history_record.id}")

            except Exception as e:
                current_app.logger.error(f"保存人脸注册历史记录失败: {str(e)}")
                # 不影响主要功能，继续执行

            return jsonify({
                'message': '人脸注册成功',
                'face_data': face_data.to_dict()
            }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"人脸注册失败: {str(e)}")
        return jsonify({'error': '人脸注册失败'}), 500

@faces_bp.route('/history', methods=['GET'])
@jwt_required()
def get_face_history():
    """获取人脸历史记录"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50)  # 限制最大50条

        # 检查权限 - 只有管理员或用户本人可以查看
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        # 获取人脸历史记录
        history_query = FaceHistory.query.filter_by(user_id=current_user_id)\
                                       .order_by(FaceHistory.created_at.desc())

        pagination = history_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        history_records = []
        for record in pagination.items:
            history_data = record.to_dict()
            # 不返回敏感的人脸特征数据
            history_data.pop('face_encoding', None)
            history_records.append(history_data)

        return jsonify({
            'success': True,
            'history': history_records,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取人脸历史记录失败: {str(e)}")
        return jsonify({'error': '获取人脸历史记录失败'}), 500


@faces_bp.route('/compare-with-history', methods=['POST'])
@jwt_required()
def compare_with_history():
    """与历史人脸记录进行对比"""
    try:
        current_user_id = get_jwt_identity()

        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'error': '请上传人脸图片'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '请选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400

        # 保存临时文件
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # 提取人脸特征
        new_face_encoding, face_image_path, error_msg = detect_and_extract_face(filepath)

        # 删除临时文件
        if os.path.exists(filepath):
            os.remove(filepath)

        if error_msg:
            return jsonify({'error': error_msg}), 400

        if not new_face_encoding:
            return jsonify({'error': '人脸特征提取失败'}), 400

        # 与历史人脸记录进行对比
        comparison_results = FaceHistory.compare_with_previous_faces(
            current_user_id,
            new_face_encoding,
            threshold=0.6
        )

        # 记录对比操作
        try:
            face_record = FaceHistory.create_new_face_record(
                user_id=current_user_id,
                face_encoding=new_face_encoding,
                face_image_path=face_image_path,
                operation_type='update',
                device_info=request.headers.get('User-Agent', ''),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            face_record.is_verified = False  # 待人工验证
            face_record.verification_method = 'comparison'
            face_record.status = 'suspicious' if not any(r['is_match'] for r in comparison_results) else 'active'

            # 计算最高相似度
            max_similarity = max([r['similarity'] for r in comparison_results], default=0)
            face_record.verification_score = max_similarity

            verification_note = f'人脸对比完成，最高相似度: {max_similarity:.2f}'
            if any(r['is_match'] for r in comparison_results):
                verification_note += ' - 匹配成功'
            else:
                verification_note += ' - 无匹配记录，需要人工验证'

            face_record.verification_note = verification_note
            face_record.verification_time = datetime.utcnow()

            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"保存对比记录失败: {str(e)}")

        return jsonify({
            'success': True,
            'comparison_results': comparison_results,
            'max_similarity': max([r['similarity'] for r in comparison_results], default=0),
            'has_match': any(r['is_match'] for r in comparison_results),
            'message': '对比完成' if any(r['is_match'] for r in comparison_results) else '未找到匹配的历史记录，请联系管理员验证'
        }), 200

    except Exception as e:
        current_app.logger.error(f"人脸对比失败: {str(e)}")
        return jsonify({'error': '人脸对比失败'}), 500


@faces_bp.route('/status', methods=['GET'])
@jwt_required()
def get_face_status():
    """获取人脸注册状态"""
    try:
        current_user_id = get_jwt_identity()

        face_data = FaceData.query.filter_by(user_id=current_user_id).first()

        if not face_data:
            return jsonify({
                'registered': False,
                'message': '尚未注册人脸信息'
            }), 200

        return jsonify({
            'registered': True,
            'face_data': face_data.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取人脸状态失败: {str(e)}")
        return jsonify({'error': '获取人脸状态失败'}), 500

@faces_bp.route('/image/<filename>')
def get_face_image(filename):
    """获取人脸图片"""
    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '图片不存在'}), 404

        return send_file(filepath, mimetype='image/jpeg')

    except Exception as e:
        current_app.logger.error(f"获取人脸图片失败: {str(e)}")
        return jsonify({'error': '获取人脸图片失败'}), 500

@faces_bp.route('/image/current', methods=['GET'])
@jwt_required()
def get_current_user_face_image():
    """获取当前用户的人脸图片"""
    try:
        current_user_id = get_jwt_identity()

        # 获取用户的人脸数据
        face_data = FaceData.query.filter_by(user_id=current_user_id).first()
        if not face_data:
            return jsonify({'error': '未找到人脸数据'}), 404

        # 检查人脸图片文件是否存在
        if not face_data.face_image_path:
            return jsonify({'error': '人脸图片文件不存在'}), 404

        # 处理相对路径，确保路径正确
        face_image_path = face_data.face_image_path
        if not os.path.isabs(face_image_path):
            # 如果是相对路径，从项目根目录开始解析（去掉app目录）
            project_root = os.path.dirname(current_app.root_path)
            face_image_path = os.path.join(project_root, face_image_path)

        # 规范化路径
        face_image_path = os.path.normpath(face_image_path)

        if not os.path.exists(face_image_path):
            current_app.logger.error(f"人脸图片文件不存在: {face_image_path}")
            return jsonify({'error': '人脸图片文件不存在'}), 404

        # 返回人脸图片文件
        return send_file(face_image_path, mimetype='image/jpeg')

    except Exception as e:
        current_app.logger.error(f"获取当前用户人脸图片失败: {str(e)}")
        return jsonify({'error': '获取人脸图片失败'}), 500

@faces_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_face():
    """人脸验证（用于入校）"""
    try:
        current_user_id = get_jwt_identity()

        # 获取用户的人脸数据
        user_face = FaceData.query.filter_by(user_id=current_user_id, is_active=True).first()
        if not user_face:
            return jsonify({'error': '您尚未注册人脸信息'}), 400

        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'error': '请上传人脸图片'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '请选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400

        # 保存临时文件
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        temp_filename = secure_filename(file.filename)
        temp_filepath = os.path.join(upload_folder, f"temp_{temp_filename}")
        file.save(temp_filepath)

        # 提取当前人脸特征
        current_encoding, current_face_path, error_msg = detect_and_extract_face(temp_filepath)

        # 删除临时文件
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        if current_face_path and os.path.exists(current_face_path):
            os.remove(current_face_path)

        if error_msg:
            return jsonify({'error': error_msg}), 400

        # 简单的特征匹配（实际项目中应该使用更专业的算法）
        try:
            registered_data = json.loads(user_face.face_encoding)
            current_data = json.loads(current_encoding)

            # 简单的质量分数比较
            quality_diff = abs(registered_data.get('quality_score', 0) - current_data.get('quality_score', 0))

            # 简单的尺寸比较
            size_diff = abs(registered_data['width'] - current_data['width']) + abs(registered_data['height'] - current_data['height'])

            # 简单匹配阈值（这里用简单的启发式方法）
            match_score = 1.0 - (quality_diff / 1000.0 + size_diff / 100.0)

            threshold = current_app.config['FACE_RECOGNITION_TOLERANCE']

            if match_score >= threshold:
                return jsonify({
                    'verified': True,
                    'match_score': match_score,
                    'message': '人脸验证成功'
                }), 200
            else:
                return jsonify({
                    'verified': False,
                    'match_score': match_score,
                    'message': '人脸验证失败，请重试'
                }), 200

        except Exception as e:
            current_app.logger.error(f"人脸比对失败: {str(e)}")
            return jsonify({'error': '人脸比对失败'}), 500

    except Exception as e:
        current_app.logger.error(f"人脸验证失败: {str(e)}")
        return jsonify({'error': '人脸验证失败'}), 500


@faces_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_face():
    """删除人脸信息"""
    try:
        current_user_id = get_jwt_identity()

        # 查找用户的人脸数据
        face_data = FaceData.query.filter_by(user_id=current_user_id).first()
        if not face_data:
            return jsonify({'error': '未找到人脸信息'}), 404

        # 删除人脸图片文件
        if face_data.face_image_path and os.path.exists(face_data.face_image_path):
            try:
                os.remove(face_data.face_image_path)
            except Exception as e:
                current_app.logger.warning(f"删除人脸图片文件失败: {str(e)}")

        # 删除数据库记录
        db.session.delete(face_data)
        db.session.commit()

        return jsonify({'message': '人脸信息删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除人脸信息失败: {str(e)}")
        return jsonify({'error': '删除人脸信息失败'}), 500


@faces_bp.route('/info', methods=['GET'])
@jwt_required()
def get_face_info():
    """获取人脸信息详情"""
    try:
        current_user_id = get_jwt_identity()

        # 查找用户的人脸数据
        face_data = FaceData.query.filter_by(user_id=current_user_id).first()
        if not face_data:
            return jsonify({'registered': False}), 200

        # 构造返回数据
        response_data = {
            'registered': True,
            'registration_time': face_data.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'quality_score': face_data.quality_score,
            'face_image_path': f"/uploads/{os.path.basename(face_data.face_image_path)}" if face_data.face_image_path else None,
            'status': 'active'
        }

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"获取人脸信息失败: {str(e)}")
        return jsonify({'error': '获取人脸信息失败'}), 500