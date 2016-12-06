# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.postgresql import JSON

from exam_app.models import db
from exam_app import app


class MockTest(db.Model):
    __tablename__ = 'mock_tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(app.config['TEST_NAME_MAX_LENGTH']))
    created_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    created_by_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    question_ids = db.Column(JSON)
    target_exam = db.Column(db.Enum(*app.config['TARGET_EXAMS'].keys(), name='target_exams_enum'))
    difficulty = db.Column(db.Enum(*app.config['MOCK_TEST_DIFFICULTY_LEVEL'].keys(), name='mock_test_difficulty_enum'))
    description = db.Column(db.Text)
    for_institutes = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    type = db.Column(db.Enum(*app.config['MOCK_TEST_TYPES'].keys(), name='mock_test_types_enum'))
    type_id = db.Column(db.Integer, db.ForeignKey('ontology.id', ondelete='CASCADE'))
    prerequisite_id = db.Column(db.Integer, db.ForeignKey('mock_tests.id', ondelete='CASCADE'))
    duration = db.Column(db.Integer)
    syllabus = db.Column(db.Text)
    cutoff = db.Column(db.Float)
    date_closed = db.Column(db.Boolean, default=False) # will the test open on a date or is it by default open
    opening_date = db.Column(db.Date, nullable=True)

    @classmethod
    def create(cls, name, difficulty, target_exam, for_institutes, question_ids, type, type_id, prerequisite_id, duration,
               created_by_type, created_by_id, date_closed, description=None, syllabus=None, cutoff=None, opening_date=None):
        mock_test = cls(name=name, difficulty=difficulty, target_exam=target_exam, for_institutes=for_institutes,
                        question_ids=question_ids, description=description, syllabus=syllabus, type=type, type_id=type_id,
                        prerequisite_id=prerequisite_id, duration=duration, cutoff=cutoff, created_by_type=created_by_type,
                        created_by_id=created_by_id, date_closed=date_closed, opening_date=opening_date)

        db.session.add(mock_test)
        db.session.commit()
        return mock_test


from exam_app.models.users import UserTypes
from exam_app.models.ontology import Ontology
