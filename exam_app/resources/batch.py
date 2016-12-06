# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app.models import db
from exam_app import app
from exam_app.models.batch import Batch as BatchModel
from exam_app.resources.batch_list import BatchList
from exam_app.models.student_batches import StudentBatches
from exam_app.exceptions import BatchNotEmpty


class Batch(AuthorizedResource):

    response = {
        'error': fields.Boolean(default=False),
        'batch': fields.Nested(BatchList.batch_obj),
    }

    @marshal_with(response)
    def get(self, *args, **kwargs):
        batch = BatchModel.get(kwargs['id'])
        return {'batch': batch}

    @marshal_with(response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('on_weekdays', type=int, required=True, choices=[0,1])
        parser.add_argument('on_weekends', type=int, required=True, choices=[0,1])
        parser.add_argument('clazz', type=str, choices=['11', '12'])
        parser.add_argument('target_year', type=int, required=True)
        parser.add_argument('target_exam', type=str, required=True, choices=app.config['TARGET_EXAMS'].keys())
        parser.add_argument('type', type=str, required=True, choices=app.config['BATCH_TYPE'].keys())
        parser.add_argument('other', type=str)
        parser.add_argument('batch_timings', type=BatchList.batch_timings)
        parser.add_argument('status', type=int)
        args = parser.parse_args()

        batch = BatchModel.get(kwargs['id'])
        if args['status'] is not None and args['status'] == 1:
            batch.status = 1
        else:
            batch.on_weekdays = bool(args['on_weekdays'])
            batch.on_weekends = bool(args['on_weekends'])
            if args['clazz'] is not None:
                batch.clazz = args['clazz']
            batch.target_year = args['target_year']
            batch.target_exam = args['target_exam']
            batch.type = args['type']
            if args['other'] is not None:
                batch.other = args['other']
            if args['batch_timings'] is not None:
                batch.batch_timings = args['batch_timings']

        db.session.commit()

        return {'batch': batch}

    def delete(self, *args, **kwargs):
        sbs = StudentBatches.query.filter(StudentBatches.batch_id == kwargs['id'], StudentBatches.left_at == None).count()
        if sbs > 0:
            raise BatchNotEmpty
        batch = BatchModel.get(kwargs['id'])
        batch.status = 0
        db.session.commit()
        return {'error': False}