# -*- coding: utf-8 -*-

from collections import Counter
import json

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import InvalidStudentId
from exam_app.models.student import Student
from exam_app.models.mock_test import MockTest
from exam_app import app
from exam_app.models.batch import Batch
from exam_app.models.institute import Institute


class StudentMockTestList(AuthorizedResource):

    """
    class JSObject(fields.Raw):
        def format(self, value):
            print value
            return json.dumps(value)
    """

    get_response = {
        'error': fields.Boolean(default=False),
        'institute_name': fields.String,
        'mock_tests': fields.Nested({
            '0': fields.Raw,
            '1': fields.Raw,
            '2': fields.Raw,
            '3': fields.Raw,
            '4': fields.Raw,
        })
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):

        result = {
            '0': {                                      # institute mock tests

            },
            '1': {                                          # full mock tests

            },
            '2': {                                          # part mock tests

            },
            '3': {                                          # subject mock tests

            },
            '4': {                                          # chapter mock tests

            },
        }

        student = Student.query.get(kwargs['user'].id)
        if student is None:
            raise InvalidStudentId

        attempted_mock_tests = Student.get_attempted_mock_tests(student.id)

        ##pushed_mock_test_ids entries filtered with student id and the batches to which he is enrolled to
        #  id | mock_test_id | batch_id |         pushed_at          | expires_at 
        # ----+--------------+----------+----------------------------+------------
        #  1 |            4 |        1 | 2017-01-28 20:49:29.714396 | 
        #  2 |            5 |        1 | 2017-01-28 21:05:51.978209 | 
        #  3 |            4 |        2 | 2017-01-30 21:29:06.667906 | 
        #  4 |            4 |        3 | 2017-01-30 21:29:06.668013 | 

        pushed_mock_tests = Student.get_pushed_mock_tests(student.id)

        institute_name = None

        ##this next block of code is the pathetic i have seen just to get institute name
        if len(pushed_mock_tests) > 0:
            batch_id = pushed_mock_tests[0].batch_id
            batch = Batch.get(batch_id)
            institute = Institute.get(batch.institute_id)
            institute_name = institute.name

        attempted_pushed_mock_test_ids = [t.pushed_mock_test_id for t in attempted_mock_tests if t.pushed_mock_test_id is not None]
        attempted_pushed_mock_test_ids_1 = [t.mock_test_id for t in attempted_mock_tests if t.pushed_mock_test_id is not None]
        attempted_independent_mock_test_ids = [t.mock_test_id for t in attempted_mock_tests if t.pushed_mock_test_id is None]
        available_mock_tests_for_student = {mock_test.id: mock_test for mock_test in MockTest.query.filter(MockTest.is_locked == True, MockTest.target_exam.in_(
            student.target_exams)).all()}

        for pushed_mock_test in pushed_mock_tests:
            is_attempted = pushed_mock_test.id in attempted_pushed_mock_test_ids
            mock_test = available_mock_tests_for_student[pushed_mock_test.mock_test_id]
            if mock_test.target_exam not in result['0']:
                result['0'][mock_test.target_exam] = {
                    'attempted': [],
                    'not_attempted': [],
                }

            # if mock test has already been attempted
            if mock_test.id in result['0'][mock_test.target_exam]['attempted']:
                continue

            # if current mock test is attempted
            if is_attempted:
                result['0'][mock_test.target_exam]['attempted'].append(mock_test.id)
            # if current mock test is not attempted
            else:
                # if a similar mock test has already been attempted, dont make the student attempt this test again
                if mock_test.id in attempted_pushed_mock_test_ids_1:
                    continue
		# if a similar mock test has already been pushed into not_attempted list
		if mock_test.id in result['0'][mock_test.target_exam]['not_attempted']:
		    continue
                result['0'][mock_test.target_exam]['not_attempted'].append(mock_test.id)

        attempted_independent_mock_test_ids_by_type = Counter()
        for mock_test_id in attempted_independent_mock_test_ids:
            mock_test = available_mock_tests_for_student[mock_test_id]
            if mock_test.target_exam in result[mock_test.type]:
                result[mock_test.type][mock_test.target_exam]['attempted'].append(mock_test.id)
            else:
                result[mock_test.type][mock_test.target_exam] = {
                    'attempted': [mock_test.id, ],
                    'not_attempted': []
                }
            attempted_independent_mock_test_ids_by_type[mock_test.type] += 1

        payment_plan = app.config['PAYMENT_PLAN']

        for mock_test_id, mock_test in available_mock_tests_for_student.items():
            # if mock test is not for institutes and attempted number mock tests of a particular type are less than
            # in payment plan
            if not mock_test.for_institutes and (mock_test.type not in attempted_independent_mock_test_ids_by_type or
                    attempted_independent_mock_test_ids_by_type[mock_test.type] < payment_plan[mock_test.type]):
                if mock_test.target_exam in result[mock_test.type]:
                    # if mock test not attempted
                    if mock_test.id not in result[mock_test.type][mock_test.target_exam]['attempted']:
                        result[mock_test.type][mock_test.target_exam]['not_attempted'].append(mock_test.id)
                else:
                    result[mock_test.type][mock_test.target_exam] = {
                        'attempted': [],
                        'not_attempted': [mock_test.id, ]
                    }

        for mock_test_type, val1 in result.items():
            for target_exam, val2 in val1.items():
                if 'attempted' in val2:
                    temp = []
                    for id in val2['attempted']:
                        pushed_id = filter(lambda pmt: pmt.mock_test_id == id, pushed_mock_tests)[0].id if mock_test_type == '0' else None
                        attempted_mock_test = filter(lambda amt: amt.mock_test_id == id and amt.pushed_mock_test_id is None, attempted_mock_tests)[0] \
                            if mock_test_type != '0' else filter(lambda amt: amt.mock_test_id == id and amt.pushed_mock_test_id == pushed_id, attempted_mock_tests)[0]
                        analysis = json.loads(attempted_mock_test.analysis) if attempted_mock_test.analysis is not None else None

                        temp.append({
                            'id': id,
                            'name': available_mock_tests_for_student[id].name,
                            'description': available_mock_tests_for_student[id].description,
                            'syllabus': available_mock_tests_for_student[id].syllabus,
                            'difficulty': available_mock_tests_for_student[id].difficulty,
                            'target_exam': available_mock_tests_for_student[id].target_exam,
                            'prerequisite_id': available_mock_tests_for_student[id].prerequisite_id,
                            'type_id': available_mock_tests_for_student[id].type_id,
                            'pushed_id': pushed_id,
                            'cutoff': available_mock_tests_for_student[id].cutoff,
                            'attempted_id': attempted_mock_test.id,
                            'score': attempted_mock_test.score,
                            'maximum_marks': analysis['maximum_marks'] if analysis is not None else None,
                            'percentage_marks': analysis['percentage_marks'] if analysis is not None else None,

                            'date_closed': available_mock_tests_for_student[id].date_closed,
                            'opening_date': str(available_mock_tests_for_student[id].opening_date),

                            'created_at': str(available_mock_tests_for_student[id].created_at)

                        })
                    val2['attempted'] = temp

                if 'not_attempted' in val2:
                    val2['not_attempted'] = [{
                        'id': id,
                        'name': available_mock_tests_for_student[id].name,
                        'description': available_mock_tests_for_student[id].description,
                        'syllabus': available_mock_tests_for_student[id].syllabus,
                        'difficulty': available_mock_tests_for_student[id].difficulty,
                        'target_exam': available_mock_tests_for_student[id].target_exam,
                        'prerequisite_id': available_mock_tests_for_student[id].prerequisite_id,
                        'type_id': available_mock_tests_for_student[id].type_id,
                        'pushed_id': filter(lambda pmt: pmt.mock_test_id == id, pushed_mock_tests)[0].id if mock_test_type == '0' else None,
                        'cutoff': available_mock_tests_for_student[id].cutoff,

                        'date_closed': available_mock_tests_for_student[id].date_closed,
                        'opening_date': str(available_mock_tests_for_student[id].opening_date),

                        'created_at': str(available_mock_tests_for_student[id].created_at)

                    } for id in val2['not_attempted']]
        import pprint
        pprint.pprint({'mock_tests': result , 'institute_name': institute_name})
        return {'mock_tests': result, 'institute_name': institute_name}
