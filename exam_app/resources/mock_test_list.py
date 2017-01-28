# -*- coding: utf-8 -*-

import json, datetime

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app import app
from exam_app.resources.common import comma_separated_ints_type
from exam_app.models.mock_test import MockTest


class MockTestList(AuthorizedResource):

    class Qids(fields.Raw):
        def format(self, value):
            return json.loads(value)

    mock_test_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'syllabus': fields.String,
        'difficulty': fields.Integer,
        'target_exam': fields.Integer,
        'for_institutes': fields.Integer,
        'is_locked': fields.Integer,
        'question_ids': Qids,
        'type': fields.String,
        'type_id': fields.Integer,
        'prerequisite_id': fields.Integer(default=None),
        'duration': fields.Integer,
        'cutoff': fields.Float
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'mock_tests': fields.List(fields.Nested(mock_test_obj)),
        'total': fields.Integer
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'mock_test': fields.Nested(mock_test_obj)
    }

    @classmethod
    def date_json_type(cls, data):
        """
        Parse the string date and output the datetime.date object.
        """

        try:
            print data
            date = datetime.datetime.strptime(data, "%Y-%m-%d").date()
            return date
        except Exception as e:
            raise ValueError("Date is not given in the proper format.")

    @classmethod
    def question_ids_json_type(cls, data):
        """
        Parse the question ids json
        Questions are supplied in the format {
            <parent_id1>: {
            "order": 2, "q_ids": [q_id1, q_id2]
            },
            <parent_id2>: {
            "order": 1, "q_ids": [q_id4, q_id5]
            }
        }

        :param data:
        :return:
        """
        try:
            parsed_data = json.loads(data)
            if not isinstance(parsed_data, dict):
                raise ValueError('question_ids should be in the form of object')
            for subject_id, d in parsed_data.items():
                if 'order' not in d or not isinstance(d['order'], int):
                    raise ValueError('order should be present for subject and should be integer')
                if 'q_ids' not in d:
                    raise ValueError('q_ids should be present for subject and should be a non empty array')

            return data

        except Exception as e:
            raise ValueError("question_ids should be json")

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('difficulty', type=str, choices=app.config['MOCK_TEST_DIFFICULTY_LEVEL'].keys())
        parser.add_argument('target_exam', type=str, choices=app.config['TARGET_EXAMS'].keys())
        parser.add_argument('is_locked', type=int, choices=[0,1])
        parser.add_argument('for_institutes', type=int, choices=[0,1])
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['MOCK_TEST_LIST_LIMIT'])
        args = parser.parse_args()

        exprs = []
        if args['difficulty'] is not None:
            exprs.append(MockTest.difficulty == args['difficulty'])
        if args['target_exam'] is not None:
            exprs.append(MockTest.target_exam == args['target_exam'])
        if args['is_locked'] is not None:
            exprs.append(MockTest.is_locked == (args['is_locked'] == 1))
        if args['for_institutes'] is not None:
            exprs.append(MockTest.for_institutes == (args['for_institutes'] == 1))

        mock_test_pag_obj = MockTest.query.filter(*exprs).order_by(MockTest.created_at.desc()).paginate(args['page'], args['limit'])
        mock_tests = mock_test_pag_obj.items
        total = mock_test_pag_obj.total
        print mock_tests
        return {'mock_tests': mock_tests, 'total': total}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('difficulty', type=str, required=True, choices=app.config['MOCK_TEST_DIFFICULTY_LEVEL'].keys())
        parser.add_argument('description', type=unicode)
        parser.add_argument('syllabus', type=unicode)
        parser.add_argument('target_exam', type=str, required=True, choices=app.config['TARGET_EXAMS'].keys())
        parser.add_argument('for_institutes', type=int, required=True, choices=[0, 1])
        parser.add_argument('type', type=str, required=True, choices=app.config['MOCK_TEST_TYPES'].keys())
        parser.add_argument('type_id', type=int)
        parser.add_argument('prerequisite_id', type=int)
        parser.add_argument('duration', type=int, required=True)
        parser.add_argument('cutoff', type=float, required=True)
        parser.add_argument('date_closed', type=bool, required=True)
        parser.add_argument('opening_date', type=self.__class__.date_json_type)

        # comma separated question ids
        parser.add_argument('question_ids', type=self.__class__.question_ids_json_type)
        args = parser.parse_args()

        for k,v in args.items():
            print "{0}: {1}".format(k, v)

        params = {
            "name": args['name'],
            "difficulty": args['difficulty'], 
            "description": args['description'], 
            "syllabus": args['syllabus'],
            "target_exam": args['target_exam'], 
            "for_institutes": args['for_institutes']==1,
            "question_ids": args['question_ids'],
            "type": args['type'],
            "type_id": args['type_id'],
            "prerequisite_id": args['prerequisite_id'],
            "duration": args['duration'],
            "cutoff": args['cutoff'],
            "created_by_type": kwargs['user_type'].id,
            "created_by_id": kwargs['user'].id,
            "date_closed": args['date_closed'],
            "opening_date": args.get('opening_date')
        }

        mock_test = MockTest.create(**params)
        return {'mock_test': mock_test}
