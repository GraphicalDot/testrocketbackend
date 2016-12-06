# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import not_

from exam_app.models import db
from exam_app import app


class ReportedQuestion(db.Model):
    __tablename__ = 'reported_questions'
    id = db.Column(db.Integer, primary_key=True)
    reported_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    reported_by_id = db.Column(db.Integer)
    is_resolved = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'))
    reported_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resolved_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    resolved_by_id = db.Column(db.Integer)
    resolved_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


    @classmethod
    def create(cls, reported_by_type, reported_by_id, question_id):
        """
        Report a question

        :param reported_by_type:
        :param reported_by_id:
        :param question_id:
        :return:
        """
        report = cls(reported_by_type=reported_by_type, reported_by_id=reported_by_id, question_id=question_id)
        question = Question.query.get(question_id)
        question.status['error_reported'] = '1'
        db.session.add(report)
        db.session.commit()
        return report


    @classmethod
    def get(cls, nature=None, type=None, difficulty=None, average_time=None, ontology=None, page=1, limit=10):
        """
        Get reported questions

        :param nature:
        :param type:
        :param difficulty:
        :param average_time:
        :param ontology:
        :param page:
        :param limit:
        :return:
        """

        exprs = []

        if nature is not None:
            exprs.append(Question.nature == nature)

        if type is not None:
            exprs.append(Question.type == type)

        if difficulty is not None:
            exprs.append(Question.difficulty == difficulty)

        if average_time is not None:
            exprs.append(Question.average_time == average_time)

        if ontology is not None:
            exprs.append(Question.ontology.contains(ontology))

        result = db.session.query(cls, Question).filter(cls.is_resolved == False, cls.question_id == Question.id, *exprs).order_by(Question.created_at.desc())
        total = result.count()
        reported_questions = []
        for row in result.offset((page-1)*limit).limit(limit):
            reported_questions.append({
                'question': row[1],
                'report_id': row[0].id
            })

        return reported_questions, total

    @classmethod
    def delete(cls, id):
        report = cls.query.get(id)
        if report is not None:
            Question.query.filter_by(id=report.question_id).delete()
            cls.query.filter_by(id=id).delete()
            db.session.commit()

from exam_app.models.users import UserTypes
from exam_app.models.question import Question
