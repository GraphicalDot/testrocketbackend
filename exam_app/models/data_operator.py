# -*- coding: utf-8 -*-

from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

from exam_app.models import db
from exam_app.models.users import User
from exam_app.models.question import Question
from exam_app.models.solution_submission import SolutionSubmission
from exam_app.exceptions import InvalidDataOperatorId, EmailAlreadyRegistered


class DataOperator(User, db.Model):
    __tablename__ = 'data_operators'
    type = db.Column(db.Integer, db.ForeignKey('user_types.id'), nullable=False)

    @classmethod
    def get_list(cls, page=1, limit=10):
        """
        Get a list of active data operators with their stats

        :param page:
        :param limit:
        :return:
        """
        result = {}

        pag_obj = cls.query.filter_by(is_active=True).paginate(page, limit)
        data_operators = pag_obj.items
        total = pag_obj.total
        if total == 0:
            return [], 0

        for op in data_operators:
            result[op.id] = {'data_operator': op}
        data_operator_type = data_operators[0].type
        data_operator_ids = result.keys()

        ques_counts = db.session.query(Question.created_by_id, func.count(Question.id)).filter(
            Question.created_by_type == data_operator_type, Question.created_by_id.in_(data_operator_ids)).group_by(Question.created_by_id)
        for id, count in ques_counts:
            result[id]['questions_added'] = count

        text_sol_counts = db.session.query(Question.text_solution_by_id, func.count(Question.id)).filter(
            Question.text_solution_by_type == data_operator_type, Question.text_solution_by_id.in_(data_operator_ids))\
            .group_by(Question.text_solution_by_id)
        for id, count in text_sol_counts:
            result[id]['text_solutions_added'] = count

        video_sol_counts = db.session.query(Question.video_solution_by_id, func.count(Question.id)).filter(
            Question.video_solution_by_type == data_operator_type, Question.video_solution_by_id.in_(data_operator_ids))\
            .group_by(Question.video_solution_by_id)
        for id, count in video_sol_counts:
            result[id]['video_solutions_added'] = count

        return result.values(), total

    @classmethod
    def get(cls, id):
        """
        Get a single data operator with his stats

        :param id:
        :return:
        """

        data_operator = cls.query.get(id)
        if data_operator is None:
            raise InvalidDataOperatorId

        ques_count = Question.query.filter(Question.created_by_type == data_operator.type,
                                           Question.created_by_id == data_operator.id).count()
        text_sol_count = Question.query.filter(Question.text_solution_by_type == data_operator.type,
                                               Question.text_solution_by_id == data_operator.id).count()
        video_sol_count = Question.query.filter(Question.video_solution_by_type == data_operator.type,
                                               Question.video_solution_by_id == data_operator.id).count()

        return {
            'data_operator': data_operator,
            'questions_added': ques_count,
            'text_solutions_added': text_sol_count,
            'video_solutions_added': video_sol_count
        }

    @classmethod
    def create(cls, name, email, password):
        """
        Create a data operator. If need encrypted password, then provide one. No encryption is done in this function.

        :param name:
        :param email:
        :param password: encrypted/unencrypted password
        :return:
        """
        user_type = UserTypes.query.filter_by(name='data_operator').first()
        data_operator = cls(name=name, email=email, password=password, type=user_type.id)
        db.session.add(data_operator)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rolback()
            raise EmailAlreadyRegistered
        return data_operator


from exam_app.models.users import UserTypes
