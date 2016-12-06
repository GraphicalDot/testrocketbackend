# -*- coding: utf-8 -*-

import datetime
from collections import OrderedDict

from exam_app.models import db
from exam_app import app


class SolutionSubmission(db.Model):
    __tablename__ = 'solution_submissions'
    id = db.Column(db.Integer, primary_key=True)
    submitted_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    submitted_by_id = db.Column(db.Integer)
    solution_type = db.Column(db.Enum('text', 'video', name='solution_types_enum'))
    solution = db.Column(db.Text)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'))
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.Enum(*app.config['SUBMISSION_STATUS'], name='submission_status_enum'))

    @classmethod
    def create(cls, submitted_by_type, submitted_by_id, question_id, solution_type, solution, status=None):
        """
        Create a new solution submission

        :param submitted_by_type: the user type who submitted
        :param submitted_by_id: the user id who submitted
        :param question_id: the question id this submission corresponds too
        :param solution_type: text/video
        :param solution:
        :param status:
        :return:
        """
        submission = cls(submitted_by_type=submitted_by_type, submitted_by_id=submitted_by_id, question_id=question_id,
                   solution_type=solution_type, solution=solution, status=status)
        db.session.add(submission)
        db.session.commit()
        return submission

    @classmethod
    def get(cls, nature=None, type=None, difficulty=None, average_time=None, ontology=None, sol_type='text', page=1, limit=10):
        """
        Get filtered category submissions

        :param nature:
        :param type:
        :param difficulty:
        :param average_time:
        :param ontology:
        :return:
        """
        if sol_type == 'text':
            data = Question.get_filtertered_list(nature=nature, type=type, difficulty=difficulty, average_time=average_time,
                                              ontology=ontology, text_solution_added='1', proof_read_text_solution='0', page=page,
                                              limit=limit)
        else:
            data = Question.get_filtertered_list(nature=nature, type=type, difficulty=difficulty, average_time=average_time,
                                              ontology=ontology, video_solution_added='1', proof_read_video_solution='0', page=page,
                                              limit=limit)
        if data['total'] > 0:
            temp = OrderedDict()
            for q in data['questions']:
                temp[q.id] = {'question': q}

            submissions = cls.query.filter(cls.question_id.in_(temp.keys()), cls.status == None, cls.solution_type == sol_type).all()
            for submission in submissions:
                temp[submission.question_id]['submission_id'] = submission.id
            return temp.values(), data['total']
        else:
            return [], 0

from exam_app.models.users import UserTypes
from exam_app.models.question import Question
