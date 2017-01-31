# -*- coding: utf-8 -*-

from hashlib import md5
import datetime
from copy import deepcopy

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app.models import db
from exam_app import app
from exam_app.resources.institute_student_list import InstituteStudentList
from exam_app.models.student import Student
from exam_app.models.student_batches import StudentBatches
from exam_app.models.batch import Batch
from exam_app.models.pushed_mock_test import PushedMockTest
from exam_app.models.attempted_mock_test import AttemptedMockTest
from exam_app.models.mock_test import MockTest


class InstituteStudent(AuthorizedResource):

    student_obj = deepcopy(InstituteStudentList.student_obj)
    student_obj['mock_tests'] = fields.List(fields.Nested({
        'id': fields.Integer,
        'name': fields.String,
        'attempted': fields.Boolean
    }))

    response = {
        'error': fields.Boolean(default=False),
        'student': fields.Nested(student_obj),
    }

    @marshal_with(response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('profile', type=int, choices=[0,1], default=0)
        args = parser.parse_args()
        student = Student.get(kwargs['id'])

        ## Get all the entries from student+batches tables where student_id is same as this student_id and get correponding
        ##batch_id's list
        batch_ids = [sb.batch_id for sb in StudentBatches.query.filter(StudentBatches.student_id == student.id, StudentBatches.left_at == None).all()]
        
        ##Get all the bacthes in which this student is enrolled and also batches which belong to this institute
        batches = Batch.get_filtered(include_ids=batch_ids, institute_id=kwargs['user'].id)
        
        ##this will have name and id of all the batches to which this student has already been enrolled.

        ## Now PushedMockTest is a table which have mock_test_id and batch_id, which implies that whichall mock test has 
        ## been pushed to which batches.
        ## So if a student was pushed to a batch, and then later a mock test has been pushed to that batch (entries in pushed_mock_test), 
        ##then the status of this mock_test is not attempted for this student till he attempts it, Which will happend when student logs
        ##into student panel, take the test and then submit it.

        ##pushed_mock_test_ids is the list of all the mock_ids which belongs to all the batches to which the student has been enrolled.
        ##  mock_tests: will have list of dict with keys as the mock_test ids and values as mock_test itself.

        ## So if a new student is added  with batches, Then all the tests for all these batches will be unattempted for
        ## this student

        ## Get student batches from StudentBatches
        ## Gte details of these batches from batch
        ## Get all the mock_test ids for these batches
        ##
        ## Get Batches | Get bacthes on which student is enrolled > get all the mock tests for these filter bathes
        student.batches = [{'id': b.id, 'name': b.name} for b in batches]
        if args['profile'] == 1:
            pushed_mock_test_ids = {p.id: p.mock_test_id for p in PushedMockTest.query.filter(PushedMockTest.batch_id.in_([b.id for b in batches])).all()}
            mock_tests = {m.id: m for m in MockTest.query.filter(MockTest.id.in_(pushed_mock_test_ids.values()))}
            amts = AttemptedMockTest.query.filter(AttemptedMockTest.student_id == student.id, AttemptedMockTest.pushed_mock_test_id.in_(pushed_mock_test_ids.keys())).all()
            attempted_mock_test_ids = {amt.mock_test_id for amt in amts}
            student.mock_tests = []
            seen_mock_test_ids = set()
            for pushed_id, mock_test_id in pushed_mock_test_ids.items():
                mt = {
                    'id': mock_test_id,
                    'name': mock_tests[mock_test_id].name,
                    'attempted': False
                }
                for amt in amts:
                    if pushed_id == amt.pushed_mock_test_id:
                        mt['attempted'] = True
                        break

                # if current mock test is not attempted
                if mt['attempted'] is False:
                    # a similar attempted mock test exists then dont push this entry into the result
                    if mock_test_id in attempted_mock_test_ids:
                        continue
                    # if similar mock test has already been pushed into the result
                    if mock_test_id in seen_mock_test_ids:
                        continue
                student.mock_tests.append(mt)
                seen_mock_test_ids.add(mock_test_id)
        return {'student': student}

    @marshal_with(response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('password', type=str)
        parser.add_argument('mobile_no', type=str, required=True)
        parser.add_argument('city', type=str)
        parser.add_argument('area', type=str)
        parser.add_argument('pin', type=str)
        parser.add_argument('school', type=str)
        parser.add_argument('ntse_score', type=float)
        parser.add_argument('roll_no', type=str)
        parser.add_argument('father_name', type=str)
        parser.add_argument('father_mobile_no', type=str)
        parser.add_argument('father_email', type=str)
        parser.add_argument('batch_ids', type=comma_separated_ints_type, required=True)
        args = parser.parse_args()
        student = Student.get(kwargs['id'])
        if args['password'] is not None:
            student.password = md5(args['password']).hexdigest()
        student.name = args['name']
        student.mobile_no = args['mobile_no']
        student.city = args['city']
        student.area = args['area']
        student.pin = args['pin']
        student.school = args['school']
        student.ntse_score = args['ntse_score']
        student.roll_no = args['roll_no']
        student.father_name = args['father_name']
        student.father_mobile_no = args['father_mobile_no']
        student.father_email = args['father_email']
        unow = datetime.datetime.utcnow()

        # new batches that the student may join. ids from this will be removed in a loop later
        new_batch_ids = args['batch_ids'][:]

        for sb in StudentBatches.query.filter(StudentBatches.student_id == student.id).all():
            # if any old batch_id not in newly supplied batch ids then student will leave that batch
            if sb.batch_id not in args['batch_ids']:
                sb.left_at = unow
            # old batch_id also in newly supplied batch ids so remove this batch_id from new_batch_ids
            else:
                new_batch_ids.remove(sb.batch_id)
                # if student rejoining
                if sb.left_at is not None:
                    sb.left_at = None

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
            # if a new batch id encountered
            if batch.id in new_batch_ids:
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