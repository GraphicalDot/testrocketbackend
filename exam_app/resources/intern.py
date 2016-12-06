# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with
from sqlalchemy.exc import IntegrityError

from exam_app.resources.common import AuthorizedResource
from exam_app import app
from exam_app.models import db
from exam_app.models.intern import Intern as InternModel
from exam_app.exceptions import InvalidInternId, EmailAlreadyRegistered
from exam_app.resources.intern_list import InternList


class Intern(AuthorizedResource):

    get_response = {
        'error': fields.Boolean(default=False),
        'intern': fields.Nested({
            'intern': fields.Nested(InternList.intern_obj),
            'reported_questions': fields.Integer,
            'questions_categorized': fields.Integer,
            'questions_approved': fields.Integer,
            'text_solutions_submitted': fields.Integer,
            'text_solutions_approved': fields.Integer,
            'video_solutions_submitted': fields.Integer,
            'video_solutions_approved': fields.Integer,
        })
    }

    put_response = {
        'error': fields.Boolean(default=False),
        'intern': fields.Nested(InternList.intern_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        intern = InternModel.get(kwargs['id'])
        return {'intern': intern}

    @marshal_with(put_response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str)
        args = parser.parse_args()

        intern = InternModel.query.get(kwargs['id'])
        if intern is None:
            raise InvalidInternId

        intern.name = args['name']
        intern.email = args['email']

        if args['password'] is not None:
            intern.password = md5(args['password']).hexdigest()

        try:
            db.session.commit()
        except IntegrityError:
            raise EmailAlreadyRegistered

        return {'intern': intern}

    def delete(self, id):
        return {'error': False}
