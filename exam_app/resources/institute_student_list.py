# -*- coding: utf-8 -*-

import datetime
from hashlib import md5
import itertools

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app import app
from exam_app.models import db
from exam_app.models.student import Student
from exam_app.models.batch import Batch
from exam_app.models.student_batches import StudentBatches


class InstituteStudentList(AuthorizedResource):

    student_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'email': fields.String,
        'target_year': fields.Integer,
        'institute': fields.Integer,
        'type': fields.Integer,
        'mobile_no': fields.String,
        'city': fields.String,
        'area': fields.String,
        'pin': fields.String,
        'school': fields.String,
        'ntse_score': fields.Float,
        'branches': fields.List(fields.String),
        'target_exams': fields.List(fields.String),
        'roll_no': fields.String,
        'father_name': fields.String,
        'father_mobile_no': fields.String,
        'father_email': fields.String,
        'payment_plan_id': fields.String,
        'registered_from': fields.String,
        'batches': fields.List(fields.Nested({
            'id': fields.Integer,
            'name': fields.String
        }))
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'students': fields.List(fields.Nested(student_obj)),
        'total': fields.Integer
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'student': fields.Nested(student_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('batch_id', type=int)
        parser.add_argument('batch_type', type=str, choices=app.config['BATCH_TYPE'].keys())
        parser.add_argument('target_year', type=int)
        parser.add_argument('target_exam', type=str, choices=app.config['TARGET_EXAMS'].keys())
        parser.add_argument('branches', type=comma_separated_ints_type)
        parser.add_argument('query', type=str)
        parser.add_argument('offset', type=int, default=0)
        parser.add_argument('limit', type=int, default=20)
        args = parser.parse_args()
        
        if args['branches'] is not None:
            args['branches'] = map(str, args['branches'])

        if args['batch_id'] is not None:
            batch = Batch.get(args['batch_id'])
            if args['batch_type'] is not None and batch.type != args['batch_type']:
                return {'students': []}
            if args['target_year'] is not None and batch.target_year != args['target_year']:
                return {'students': []}
            if args['target_exam'] is not None and batch.target_exam != args['target_exam']:
                return {'students': []}
            student_ids = [sb.student_id for sb in StudentBatches.query.filter(StudentBatches.batch_id == batch.id,
                                                                               StudentBatches.left_at == None).all()]
        else:
            batches = {b.id: b for b in Batch.get_filtered(type=args['batch_type'], target_year=args['target_year'],
                                                           target_exam=args['target_exam'], institute_id=kwargs['user'].id, branches=args['branches'])}
            student_ids = list({sb.student_id for sb in StudentBatches.query.filter(StudentBatches.batch_id.in_(batches.keys()),
                                                                               StudentBatches.left_at == None).all()})

        # for pagination
        if args['query'] is not None:
            students = Student.query.filter(Student.id.in_(student_ids), Student.name.ilike('%' + args['query'] + '%')).all()
            total = len(students)
            student_ids = [s.id for s in students][args['offset']:args['offset']+args['limit']]
        else:
            total = len(student_ids)
            student_ids = sorted(student_ids)[args['offset']:args['offset']+args['limit']]
            students = Student.query.filter(Student.id.in_(student_ids)).all()
        student_batches = {}
        # get all students whose id is present `student_ids` and have not left the batch and all their batches too
        for sb in StudentBatches.query.filter(StudentBatches.student_id.in_(student_ids), StudentBatches.left_at == None).all():
            if sb.student_id not in student_batches:
                student_batches[sb.student_id] = [sb.batch_id]
            else:
                student_batches[sb.student_id].append(sb.batch_id)

        # need to make one more batch query because i need all the batches that any student in the result set is part of
        batches = {b.id: b for b in Batch.get_filtered(include_ids=list(itertools.chain(*student_batches.values())))}
        for student in students:
            student.batches = [{'id': b_id, 'name': batches[b_id].name} for b_id in student_batches.get(student.id, [])]
        return {'students': students, 'total': total}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('mobile_no', type=str, required=True)
        parser.add_argument('city', type=str)
        parser.add_argument('area', type=str)
        parser.add_argument('pin', type=str)
        parser.add_argument('school', type=str)
        parser.add_argument('ntse_score', type=float)
        parser.add_argument('roll_no', type=str, required=True)
        parser.add_argument('father_name', type=str)
        parser.add_argument('father_mobile_no', type=str)
        parser.add_argument('father_email', type=str)
        parser.add_argument('batch_ids', type=comma_separated_ints_type, required=True)
        args = parser.parse_args()
        student = Student.create(name=args['name'], email=args['email'], password=md5(args['password']).hexdigest(),
                                 mobile_no=args['mobile_no'], city=args['city'], area=args['area'], pin=args['pin'],
                                 school=args['school'], ntse_score=args['ntse_score'], roll_no=args['roll_no'],
                                 father_name=args['father_name'], father_mobile_no=args['father_mobile_no'],
                                 father_email=args['father_email'], registered_from='institute')
        target_exams = set()
        target_year = None
        batches = Batch.get_filtered(include_ids=args['batch_ids'])

        engineering_exams = {'1', '2', '3'}
        medical_exams = {'4', '5'}
        for batch in batches:
            if batch.target_exam in engineering_exams:
                target_exams.update(engineering_exams)
            if batch.target_exam in medical_exams:
                target_exams.update(medical_exams)
            if target_year is None or target_year > batch.target_year:
                target_year = batch.target_year
            sb = StudentBatches(batch_id=batch.id, student_id=student.id, joined_at=datetime.datetime.utcnow())
            db.session.add(sb)

        branches = []
        if len(target_exams.intersection(engineering_exams)) > 0:
            branches.append('1')
        if len(target_exams.intersection(medical_exams)) > 0:
            branches.append('2')

        student.target_year = target_year
        student.target_exams = list(target_exams)
        student.branches = branches
        db.session.commit()
        student.batches = [{'id': b.id, 'name': b.name} for b in batches]
        return {'student': student}