# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse

from exam_app.resources.common import AuthorizedResource
from exam_app.models import db
from exam_app.models.solution_submission import SolutionSubmission as SolutionSubmissionModel
from exam_app.models.solution_approval import SolutionApproval
from exam_app.models.question import Question


class SolutionSubmission(AuthorizedResource):
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('action', type=str, required=True, choices=['approve', 'reject'])
        args = parser.parse_args()
        if args['action'] == 'reject':
            sub = SolutionSubmissionModel.query.get(kwargs['id'])
            if sub is not None:
                sub.status = 'rejected'
                Question.reset_solution(sub.question_id, sub.solution_type)
                db.session.commit()
        if args['action'] == 'approve':
            sub = SolutionSubmissionModel.query.get(kwargs['id'])
            if sub is not None:
                sub.status = 'accepted'
                # create approval entry
                SolutionApproval.create(sub.id, kwargs['user_type'].id, kwargs['user'].id)
                Question.approve_solution(sub.question_id, sub.solution_type)
                db.session.commit()
        return {'error': False}
