# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.postgresql import JSON

from exam_app.models import db
from exam_app import app


class AttemptedMockTest(db.Model):
    __tablename__ = 'attempted_mock_tests'
    id = db.Column(db.Integer, primary_key=True)
    pushed_mock_test_id = db.Column(db.Integer, db.ForeignKey('pushed_mock_tests.id', ondelete="CASCADE"))      # null when independently test chosen
    mock_test_id = db.Column(db.Integer, db.ForeignKey('mock_tests.id', ondelete="CASCADE"))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete="CASCADE"))
    answers = db.Column(JSON)                           # pg json with question id as key and chosen options, time, is_correct, marks as values
    analysis = db.Column(JSON)                          # pg json with static analysis data
    score = db.Column(db.Float)
    attempted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    pdf_report_url = db.Column(db.String)

from exam_app.models.pushed_mock_test import PushedMockTest
from exam_app.models.mock_test import MockTest
from exam_app.models.student import Student
