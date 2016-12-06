# -*- coding: utf-8 -*-

from exam_app.models import db
from exam_app import app
import datetime


class PushedMockTest(db.Model):
    __tablename__ = 'pushed_mock_tests'
    id = db.Column(db.Integer, primary_key=True)
    mock_test_id = db.Column(db.Integer, db.ForeignKey('mock_tests.id'))
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    pushed_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime)

from exam_app.models.mock_test import MockTest
from exam_app.models.batch import Batch
