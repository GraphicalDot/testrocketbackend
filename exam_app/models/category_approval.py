# -*- coding: utf-8 -*-

import datetime

from exam_app.models import db


class CategoryApproval(db.Model):
    __tablename__ = 'category_approvals'
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('category_submissions.id', ondelete='CASCADE'))
    approved_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    approved_by_id = db.Column(db.Integer)
    approved_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def create(cls, submission_id, approved_by_type, approved_by_id):
        approval = cls(submission_id=submission_id, approved_by_type=approved_by_type, approved_by_id=approved_by_id)
        db.session.add(approval)
        db.session.commit()

from exam_app.models.users import UserTypes
from exam_app.models.category_submission import CategorySubmission
