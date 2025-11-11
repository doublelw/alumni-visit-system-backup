"""
问卷调查管理API
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import func, and_, or_

from app import db
from app.models.survey import Survey, SurveyQuestion, SurveyResponse
from app.models.school_calendar import SchoolCalendar
from app.models.user import User

survey_bp = Blueprint('survey', __name__)

@survey_bp.before_request
@jwt_required()
def admin_required():
    """管理员权限检查"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.user_type != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403

@survey_bp.route('/surveys', methods=['GET'])
def get_surveys():
    """获取问卷列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        event_id = request.args.get('event_id', type=int)

        query = Survey.query

        # 状态筛选
        if status:
            query = query.filter_by(status=status)

        # 搜索筛选
        if search:
            query = query.filter(
                or_(
                    Survey.title.contains(search),
                    Survey.description.contains(search)
                )
            )

        # 事件筛选
        if event_id:
            query = query.filter_by(event_id=event_id)

        # 排序
        query = query.order_by(Survey.created_at.desc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        surveys_list = [survey.to_dict() for survey in pagination.items]

        return jsonify({
            'surveys': surveys_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取问卷列表失败: {str(e)}")
        return jsonify({'error': '获取问卷列表失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>', methods=['GET'])
def get_survey(survey_id):
    """获取单个问卷详情"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        # 获取问题列表
        questions = survey.questions.order_by(SurveyQuestion.order_index).all()
        questions_list = [question.to_dict() for question in questions]

        survey_dict = survey.to_dict()
        survey_dict['questions'] = questions_list

        return jsonify({
            'survey': survey_dict
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取问卷详情失败: {str(e)}")
        return jsonify({'error': '获取问卷详情失败'}), 500

@survey_bp.route('/surveys', methods=['POST'])
def create_survey():
    """创建问卷"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['title']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}不能为空'}), 400

        current_user_id = int(get_jwt_identity())

        # 解析时间
        start_time = datetime.utcnow()
        if data.get('start_time'):
            try:
                start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return jsonify({'error': '开始时间格式错误'}), 400

        end_time = None
        if data.get('end_time'):
            try:
                end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
                if end_time <= start_time:
                    return jsonify({'error': '结束时间必须晚于开始时间'}), 400
            except ValueError:
                return jsonify({'error': '结束时间格式错误'}), 400

        # 创建问卷
        survey = Survey(
            title=data['title'],
            description=data.get('description', ''),
            event_id=data.get('event_id') if data.get('event_id') else None,
            is_anonymous=data.get('is_anonymous', False),
            is_public=data.get('is_public', True),
            require_login=data.get('require_login', True),
            start_time=start_time,
            end_time=end_time,
            status=data.get('status', 'draft'),
            created_by=current_user_id
        )

        db.session.add(survey)
        db.session.commit()

        # 添加问题
        questions_data = data.get('questions', [])
        for question_data in questions_data:
            question = SurveyQuestion(
                survey_id=survey.id,
                question_text=question_data['question_text'],
                question_type=question_data['question_type'],
                is_required=question_data.get('is_required', True),
                order_index=question_data.get('order_index', 0)
            )

            # 设置选项
            if question_data.get('options'):
                question.set_options(question_data['options'])

            db.session.add(question)

        db.session.commit()

        return jsonify({
            'message': '问卷创建成功',
            'survey': survey.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建问卷失败: {str(e)}")
        return jsonify({'error': '创建问卷失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>', methods=['PUT'])
def update_survey(survey_id):
    """更新问卷"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        data = request.get_json()

        # 更新基本信息
        if 'title' in data:
            survey.title = data['title']
        if 'description' in data:
            survey.description = data['description']
        if 'event_id' in data:
            survey.event_id = data['event_id']
        if 'is_anonymous' in data:
            survey.is_anonymous = data['is_anonymous']
        if 'is_public' in data:
            survey.is_public = data['is_public']
        if 'require_login' in data:
            survey.require_login = data['require_login']

        # 更新时间
        if 'start_time' in data:
            if data['start_time']:
                try:
                    survey.start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return jsonify({'error': '开始时间格式错误'}), 400
            else:
                survey.start_time = None

        if 'end_time' in data:
            if data['end_time']:
                try:
                    survey.end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return jsonify({'error': '结束时间格式错误'}), 400
            else:
                survey.end_time = None

        if 'status' in data:
            survey.status = data['status']

        # 验证时间逻辑
        if survey.start_time and survey.end_time and survey.end_time <= survey.start_time:
            return jsonify({'error': '结束时间必须晚于开始时间'}), 400

        survey.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': '问卷更新成功',
            'survey': survey.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新问卷失败: {str(e)}")
        return jsonify({'error': '更新问卷失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>', methods=['DELETE'])
def delete_survey(survey_id):
    """删除问卷"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        # 检查是否有回答记录
        if survey.responses.count() > 0:
            return jsonify({'error': '该问卷已有回答记录，无法删除'}), 400

        db.session.delete(survey)
        db.session.commit()

        return jsonify({
            'message': '问卷删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除问卷失败: {str(e)}")
        return jsonify({'error': '删除问卷失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>/publish', methods=['POST'])
def publish_survey(survey_id):
    """发布问卷"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        if survey.status == 'published':
            return jsonify({'error': '问卷已经发布'}), 400

        # 检查是否有问题
        if survey.questions.count() == 0:
            return jsonify({'error': '问卷至少需要一个问题才能发布'}), 400

        survey.status = 'published'
        survey.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '问卷发布成功',
            'survey': survey.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发布问卷失败: {str(e)}")
        return jsonify({'error': '发布问卷失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>/questions', methods=['GET'])
def get_survey_questions(survey_id):
    """获取问卷问题列表"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        questions = survey.questions.order_by(SurveyQuestion.order_index).all()
        questions_list = [question.to_dict() for question in questions]

        return jsonify({
            'questions': questions_list
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取问卷问题列表失败: {str(e)}")
        return jsonify({'error': '获取问卷问题列表失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>/questions', methods=['POST'])
def add_survey_question(survey_id):
    """添加问卷问题"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        data = request.get_json()

        # 验证必填字段
        required_fields = ['question_text', 'question_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field}不能为空'}), 400

        # 验证问题类型
        valid_types = ['single_choice', 'multiple_choice', 'text', 'textarea', 'rating', 'number']
        if data['question_type'] not in valid_types:
            return jsonify({'error': f'问题类型无效，有效值: {", ".join(valid_types)}'}), 400

        # 对于选择题，验证选项
        if data['question_type'] in ['single_choice', 'multiple_choice']:
            if not data.get('options') or len(data['options']) < 2:
                return jsonify({'error': '选择题至少需要2个选项'}), 400

        # 获取当前最大排序索引
        max_order = db.session.query(func.max(SurveyQuestion.order_index)).filter_by(survey_id=survey_id).scalar() or 0

        question = SurveyQuestion(
            survey_id=survey_id,
            question_text=data['question_text'],
            question_type=data['question_type'],
            is_required=data.get('is_required', True),
            order_index=data.get('order_index', max_order + 1)
        )

        # 设置选项
        if data.get('options'):
            question.set_options(data['options'])

        db.session.add(question)
        db.session.commit()

        return jsonify({
            'message': '问题添加成功',
            'question': question.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加问卷问题失败: {str(e)}")
        return jsonify({'error': '添加问卷问题失败'}), 500

@survey_bp.route('/questions/<int:question_id>', methods=['PUT'])
def update_survey_question(question_id):
    """更新问卷问题"""
    try:
        question = SurveyQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': '问题不存在'}), 404

        data = request.get_json()

        # 更新基本信息
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'question_type' in data:
            question.question_type = data['question_type']
        if 'is_required' in data:
            question.is_required = data['is_required']
        if 'order_index' in data:
            question.order_index = data['order_index']

        # 更新选项
        if 'options' in data:
            if data['question_type'] in ['single_choice', 'multiple_choice']:
                if not data['options'] or len(data['options']) < 2:
                    return jsonify({'error': '选择题至少需要2个选项'}), 400
            question.set_options(data['options'])

        db.session.commit()

        return jsonify({
            'message': '问题更新成功',
            'question': question.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新问卷问题失败: {str(e)}")
        return jsonify({'error': '更新问卷问题失败'}), 500

@survey_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_survey_question(question_id):
    """删除问卷问题"""
    try:
        question = SurveyQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': '问题不存在'}), 404

        # 检查是否有回答记录
        # 这里可以添加更复杂的检查逻辑

        db.session.delete(question)
        db.session.commit()

        return jsonify({
            'message': '问题删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除问卷问题失败: {str(e)}")
        return jsonify({'error': '删除问卷问题失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>/responses', methods=['GET'])
def get_survey_responses(survey_id):
    """获取问卷回答列表"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')

        query = survey.responses

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(SurveyResponse.created_at.desc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        responses_list = [response.to_dict() for response in pagination.items]

        return jsonify({
            'responses': responses_list,
            'survey': survey.to_dict(),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取问卷回答列表失败: {str(e)}")
        return jsonify({'error': '获取问卷回答列表失败'}), 500

@survey_bp.route('/surveys/<int:survey_id>/statistics', methods=['GET'])
def get_survey_statistics(survey_id):
    """获取问卷统计信息"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': '问卷不存在'}), 404

        # 基础统计
        total_responses = survey.responses.filter_by(status='completed').count()
        draft_responses = survey.responses.filter_by(status='draft').count()

        # 获取问题和统计
        questions = survey.questions.order_by(SurveyQuestion.order_index).all()
        statistics = []

        for question in questions:
            question_stats = {
                'id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'is_required': question.is_required,
                'answer_count': 0,
                'answers': []
            }

            if question.question_type in ['single_choice', 'multiple_choice']:
                # 选择题统计
                options = question.get_options()
                option_counts = {option: 0 for option in options}

                for response in survey.responses.filter_by(status='completed'):
                    answers = response.get_answers()
                    if str(question.id) in answers:
                        user_answers = answers[str(question.id)]
                        if isinstance(user_answers, list):
                            # 多选题
                            for answer in user_answers:
                                if answer in option_counts:
                                    option_counts[answer] += 1
                        else:
                            # 单选题
                            if user_answers in option_counts:
                                option_counts[user_answers] += 1

                question_stats['answer_count'] = sum(option_counts.values())
                question_stats['option_counts'] = option_counts

            elif question.question_type in ['text', 'textarea']:
                # 文本题统计
                text_answers = []
                for response in survey.responses.filter_by(status='completed'):
                    answers = response.get_answers()
                    if str(question.id) in answers:
                        text_answers.append(answers[str(question.id)])

                question_stats['answer_count'] = len(text_answers)
                question_stats['text_answers'] = text_answers

            elif question.question_type in ['rating', 'number']:
                # 数字题统计
                numbers = []
                for response in survey.responses.filter_by(status='completed'):
                    answers = response.get_answers()
                    if str(question.id) in answers:
                        try:
                            value = float(answers[str(question.id)])
                            numbers.append(value)
                        except:
                            pass

                if numbers:
                    question_stats['answer_count'] = len(numbers)
                    question_stats['average'] = sum(numbers) / len(numbers)
                    question_stats['min'] = min(numbers)
                    question_stats['max'] = max(numbers)

            statistics.append(question_stats)

        return jsonify({
            'survey': survey.to_dict(),
            'total_responses': total_responses,
            'draft_responses': draft_responses,
            'completion_rate': (total_responses / max(total_responses + draft_responses, 1)) * 100,
            'statistics': statistics
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取问卷统计信息失败: {str(e)}")
        return jsonify({'error': '获取问卷统计信息失败'}), 500