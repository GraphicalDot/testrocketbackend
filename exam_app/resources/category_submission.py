# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse

from exam_app.resources.common import AuthorizedResource
from exam_app.models import db
from exam_app.models.category_submission import CategorySubmission as CategorySubmissionModel
from exam_app.models.question import Question
from exam_app.models.category_approval import CategoryApproval


class CategorySubmission(AuthorizedResource):
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('action', type=str, required=True, choices=['approve', 'reject'])
        args = parser.parse_args()
        if args['action'] == 'reject':
            sub = CategorySubmissionModel.query.get(kwargs['id'])
            if sub is not None:
                sub.status = 'rejected'
                Question.reset_categorization(sub.question_id)
                db.session.commit()
        if args['action'] == 'approve':
            sub = CategorySubmissionModel.query.get(kwargs['id'])
            if sub is not None:
                sub.status = 'accepted'
                # create approval entry
                CategoryApproval.create(sub.id, kwargs['user_type'].id, kwargs['user'].id)
                Question.approve_categorization(sub.question_id)
                db.session.commit()
        return {'error': False}
