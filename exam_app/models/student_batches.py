# -*- coding: utf-8 -*-

import datetime

from exam_app.models import db


class StudentBatches(db.Model):
    __tablename__ = 'student_batches'
    __table_args__ = (db.UniqueConstraint('student_id', 'batch_id'), )
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    joined_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    left_at = db.Column(db.DateTime)

from exam_app.models.student import Student
from exam_app.models.batch import Batch
