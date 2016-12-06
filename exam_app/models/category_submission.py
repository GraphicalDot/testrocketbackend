# -*- coding: utf-8 -*-

import datetime
import json
from collections import OrderedDict

from sqlalchemy.dialects.postgresql import JSON

from exam_app.models import db
from exam_app import app


class CategorySubmission(db.Model):
    __tablename__ = 'category_submissions'
    id = db.Column(db.Integer, primary_key=True)
    submitted_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    submitted_by_id = db.Column(db.Integer)

    # JSON in the form of {"ontology": [1,10,13], "type": "", "nature": , ...}
    category = db.Column(JSON)

    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'))
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.Enum(*app.config['SUBMISSION_STATUS'], name='submission_status_enum'))

    @classmethod
    def create(cls, submitted_by_type, submitted_by_id, question_id, ontology=None, nature=None, type=None, difficulty=None,
               average_time=None, status=None):
        """
        Create a new categorization submission

        :param submitted_by_type: the user type who submitted
        :param submitted_by_id: the user id who submitted
        :param question_id: the question id this submission corresponds too
        :param ontology: the ontology node's complete path
        :param type:
        :param difficulty:
        :param average_time:
        :param status:
        :return:
        """
        category = {
            'ontology': ontology,
            'type': type,
            'difficulty': difficulty,
            'average_time': average_time,
            'nature': nature
        }
        submission = cls(submitted_by_type=submitted_by_type, submitted_by_id=submitted_by_id, question_id=question_id,
                         category=json.dumps(category), status=status)
        db.session.add(submission)
        db.session.commit()
        return submission

    @classmethod
    def get(cls, nature=None, type=None, difficulty=None, average_time=None, ontology=None, page=1, limit=10):
        """
        Get filtered category submissions

        :param nature:
        :param type:
        :param difficulty:
        :param average_time:
        :param ontology:
        :return:
        """

        data = Question.get_filtertered_list(nature=nature, type=type, difficulty=difficulty, average_time=average_time,
                                              ontology=ontology, categorized='1', proof_read_categorization='0', page=page,
                                              limit=limit)
        if data['total'] > 0:
            temp = OrderedDict()
            for q in data['questions']:
                temp[q.id] = {'question': q}

            submissions = cls.query.filter(cls.question_id.in_(temp.keys()), cls.status == None).all()
            for submission in submissions:
                temp[submission.question_id]['submission_id'] = submission.id
            return temp.values(), data['total']
        else:
            return [], 0


from exam_app.models.users import UserTypes
from exam_app.models.question import Question
