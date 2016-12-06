# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app import app
from exam_app.models.batch import Batch


class BatchList(AuthorizedResource):

    @classmethod
    def batch_timings(cls, data):
        """
        Validate batch timing format. It should be ``h1:m1-h2:m2``

        :param data:
        :return:
        """
        timings = data.split('-')
        if len(timings) != 2:
            raise ValueError('Timing format incorrect')
        for timing in timings:
            try:
                hour, minute = timing.split(':')
            except Exception:
                raise ValueError('Timing format incorrect')
            try:
                hour, minute = int(hour), int(minute)
            except Exception:
                raise ValueError('Hour and minute should be integer')
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError('Out of range values for hour and minute')
        return data

    batch_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'on_weekdays': fields.Boolean,
        'on_weekends': fields.Boolean,
        'clazz': fields.String,
        'target_year': fields.Integer,
        'target_exam': fields.String,
        'type': fields.String,
        'other': fields.String,
        'batch_timings': fields.String,
        'institute_id': fields.Integer,
        'status': fields.Integer
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'batches': fields.List(fields.Nested(batch_obj))
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'batch': fields.Nested(batch_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('days', type=str, choices=['weekdays', 'weekends'])
        parser.add_argument('type', type=str, choices=app.config['BATCH_TYPE'].keys())
        parser.add_argument('target_year', type=int)
        parser.add_argument('target_exam', type=str, choices=app.config['TARGET_EXAMS'].keys())
        parser.add_argument('branch', type=str, choices=app.config['BATCH_FIELD'].keys())
        parser.add_argument('status', type=int, default=-1)
        args = parser.parse_args()

        if args['branch'] is not None:
            args['branches'] = [args['branch'], ]
        args.pop('branch', None)

        batches = Batch.get_filtered(institute_id=kwargs['user'].id, **args)
        return {'batches': batches}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('on_weekdays', type=int, required=True, choices=[0,1])
        parser.add_argument('on_weekends', type=int, required=True, choices=[0,1])
        parser.add_argument('clazz', type=str, choices=['11', '12'])
        parser.add_argument('target_year', type=int, required=True)
        parser.add_argument('target_exam', type=str, required=True, choices=app.config['TARGET_EXAMS'].keys())
        parser.add_argument('type', type=str, required=True, choices=app.config['BATCH_TYPE'].keys())
        parser.add_argument('other', type=str)
        parser.add_argument('batch_timings', type=self.__class__.batch_timings)
        args = parser.parse_args()

        batch = Batch.create(name=args['name'], on_weekdays=bool(args['on_weekdays']), on_weekends=bool(args['on_weekends']),
                             clazz=args['clazz'], target_year=args['target_year'], target_exam=args['target_exam'],
                             type=args['type'], other=args['other'], batch_timings=args['batch_timings'], institute_id=kwargs['user'].id)
        return {'batch': batch}