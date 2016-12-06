# -*- coding: utf-8 -*-
import datetime, json

from sqlalchemy.dialects.postgresql import JSON

from exam_app.models import db
from exam_app import app
from exam_app.models.mock_test import MockTest


class QuestionUploadSet(db.Model):
    
    __tablename__ = 'upload_sets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column( db.String(app.config['QUESTION_UPLOAD_SET_NAME_MAX_LENGTH']) )
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    errors_exist = db.Column(db.Boolean, default=False)
    mock_test_id = db.Column(db.Integer, db.ForeignKey('mock_tests.id'))
    questions_added = db.Column(db.Boolean, default=False)
    parsed_questions = db.Column(JSON)
    parsed_comprehensions = db.Column(JSON)

    @property
    def parsed_questions_decoded(self):
        questions = json.loads(self.parsed_questions)
        return questions

    @property
    def parsed_comprehensions_decoded(self):
        comprehensions = json.loads(self.parsed_comprehensions)
        return comprehensions

    @property
    def mock_test(self):
        mock_test = MockTest.query.get(self.mock_test_id)
        return mock_test

    @classmethod
    def create(cls, name, errors_exist, mock_test_id, parsed_questions, parsed_comprehensions):
        upload_set = cls(
            name=name,
            errors_exist=errors_exist,
            mock_test_id=mock_test_id,
            parsed_questions=parsed_questions,
            parsed_comprehensions=parsed_comprehensions
        )
        db.session.add(upload_set)
        db.session.commit()

        return upload_set

    @classmethod
    def delete(cls, id):
        upload_set = cls.query.get(id)
        if upload_set is not None:
            cls.query.filter_by(id=id).delete()
            db.session.commit()
