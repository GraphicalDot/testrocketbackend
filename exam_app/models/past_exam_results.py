# -*- coding: utf-8 -*-

import json

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.exc import IntegrityError

from exam_app.models import db
from exam_app import app


class PastExamResult(db.Model):
    __tablename__ = 'past_exam_results'
    __table_args__ = (db.UniqueConstraint('year', 'exam'), )
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    exam = db.Column(db.Enum(*app.config['TARGET_EXAMS'].keys(), name='target_exams_enum'))
    data = db.Column(JSON)          # json containing cutoff, marks-rank map, rank-college map

    @classmethod
    def insert(cls, year, exam, data):
        try:
            exam_result = cls(year=year, exam=exam, data=json.dumps(data))
            db.session.add(exam_result)
            db.session.commit()
        except IntegrityError:
            exam_result = cls.query.filter(cls.year == year, cls.exam == exam).first()
            exam_result.data = json.dumps(data)
            db.session.commit()
        return exam_result.id