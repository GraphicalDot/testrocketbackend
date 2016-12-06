# -*- coding: utf-8 -*-

import json

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app import app
from exam_app.resources.common import AuthorizedResource
from exam_app.resources.common import comma_separated_ints_type


def options_json_type(options):
    try:
        data = json.loads(options)
    except:
        raise ValueError('Malformed JSON')

    # parse data for the format [{'content': , 'is_correct': , 'reason': }, ]
    if isinstance(data, list) and len(data) > 1:
        all_options = []
        correct_options = []
        option_reasons = []
        correct_option_encountered = False
        for option in data:
            if isinstance(option, dict) and {'content', 'is_correct', 'reason'}.issubset(set(option.keys())):
                all_options.append(option['content'])
                option_reasons.append(option['reason'] if option['reason'] is not None else '')
                if option['is_correct']:
                    correct_option_encountered = True
                    # append the index of correct option
                    correct_options.append(len(all_options)-1)

        if correct_option_encountered:
            # if at least 1 correct option found
            return {
                'all_options': all_options,
                'correct_options': correct_options,
                'option_reasons': option_reasons
            }
        else:
            raise ValueError("Option JSON not as expected")

    raise ValueError("Option JSON not as expected")


def user_json_type(user):
    # parse user for the format {'type': , 'id': }

    try:
        data = json.loads(user)
    except:
        raise ValueError('Malformed JSON')
    if isinstance(data, dict) and {'type', 'id'}.issubset(set(data.keys())):
        # required keys are present
        # convert the user type name to user type id
        data['type'] = UserTypes.query.filter_by(name=data['type']).first().id
        return data
    else:
        raise ValueError("User JSON not as expected")


class QuestionList(AuthorizedResource):

    @staticmethod
    def is_categorization_complete(params):
        if None not in (params['nature'], params['type'], params['difficulty'], params['average_time']):
            # All required attributes present
            if params['ontology_id'] is not None and Ontology.is_leaf_node(params['ontology_id']):
                # Ontology is complete since leaf node. So consider it categorized
                return True
        return False

    question_obj = {
        'id': fields.Integer,
        'status': fields.Nested({
            'categorized': fields.String,
            'proof_read_categorization': fields.String,
            'text_solution_added': fields.String,
            'video_solution_added': fields.String,
            'proof_read_text_solution': fields.String,
            'proof_read_video_solution': fields.String,
            'finalized': fields.String,
            'error_reported': fields.String
        }),
        'content': fields.String,
        'ontology': fields.List(fields.Integer),
        'type': fields.String,
        'difficulty': fields.String,
        'nature': fields.String,
        'average_time': fields.String,
        'text_solution': fields.String,
        'video_solution_url': fields.String,
        'text_solution_by_type': fields.Integer(default=None),
        'text_solution_by_id': fields.Integer(default=None),
        'video_solution_by_type': fields.Integer(default=None),
        'video_solution_by_id': fields.Integer(default=None),
        'all_options': fields.List(fields.String),
        'correct_options': fields.List(fields.Integer),
        'option_reasons': fields.List(fields.String),
        'comprehension': fields.Nested({
            'id': fields.Integer(default=None),
            'content': fields.String
        }),
        'similar_question_ids': fields.List(fields.Integer),
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'questions': fields.List(fields.Nested(question_obj)),
        'total': fields.Integer
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'question': fields.Nested(question_obj)
    }

    common_parser = reqparse.RequestParser()
    common_parser.add_argument('nature', type=str, choices=app.config['QUESTION_NATURE'].keys())
    common_parser.add_argument('type', type=str, choices=app.config['QUESTION_TYPE'].keys())
    common_parser.add_argument('difficulty', type=str, choices=app.config['QUESTION_DIFFICULTY_LEVEL'])
    common_parser.add_argument('average_time', type=int, choices=map(int, app.config['QUESTION_AVERAGE_TIME']))

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = self.common_parser.copy()
        parser.add_argument('categorized', type=str, choices=['0', '1'])
        parser.add_argument('proof_read_categorization', type=str, choices=['0', '1'])
        parser.add_argument('proof_read_text_solution', type=str, choices=['0', '1'])
        parser.add_argument('proof_read_video_solution', type=str, choices=['0', '1'])
        parser.add_argument('finalized', type=str, choices=['0', '1'])
        parser.add_argument('error_reported', type=str, choices=['0', '1'])

        # this contains comma separated ontology node ids
        parser.add_argument('ontology', type=comma_separated_ints_type)

        parser.add_argument('ontology_id', type=int)

        parser.add_argument('is_comprehension', type=int, choices=[0, 1])
        parser.add_argument('text_solution_added', type=int, choices=[0, 1])
        parser.add_argument('video_solution_added', type=int, choices=[0, 1])
        parser.add_argument('exclude_question_ids', type=comma_separated_ints_type)
        parser.add_argument('include_question_ids', type=comma_separated_ints_type)
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['QUESTION_BANK_LIST_LIMIT'])
        args = parser.parse_args()

        if args['ontology_id'] is not None and args['ontology'] is None:
            ontology_obj = Ontology.query.get(args['ontology_id'])
            if ontology_obj is not None:
                args['ontology'] = ontology_obj.absolute_path

        return Question.get_filtertered_list(nature=args['nature'], type=args['type'], difficulty=args['difficulty'],
                                         average_time=args['average_time'],categorized=args['categorized'],
                                         proof_read_categorization=args['proof_read_categorization'],
                                         proof_read_text_solution=args['proof_read_text_solution'],
                                         proof_read_video_solution=args['proof_read_video_solution'], finalized=args['finalized'],
                                         error_reported=args['error_reported'], text_solution_added=args['text_solution_added'],
                                         video_solution_added=args['video_solution_added'], ontology=args['ontology'],
                                         is_comprehension=args['is_comprehension'], exclude_question_ids=args['exclude_question_ids'],
                                         include_question_ids=args['include_question_ids'], page=args['page'], limit=args['limit'])

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = self.common_parser.copy()
        # the next field will be present when the first question of a comprehension is added
        parser.add_argument('comprehension_text', type=unicode)

        # the next field will be present when question of an already created comprehension is added
        parser.add_argument('comprehension_id', type=int)

        parser.add_argument('ontology_id', type=int)
        parser.add_argument('content', type=unicode, required=True)
        parser.add_argument('options', type=options_json_type, required=True)
        parser.add_argument('text_solution', type=unicode)
        parser.add_argument('video_solution_url', type=str)
        parser.add_argument('text_solution_by', type=user_json_type)
        parser.add_argument('video_solution_by', type=user_json_type)
        args = parser.parse_args()

        comprehension = None
        if args['comprehension_id'] is not None:
            # comprehension_id is present, just update the comprehension content if its present in request
            if args['comprehension_text'] is not None:
                comprehension = Comprehension.update(args['comprehension_id'], args['comprehension_text'])
        else:
            # comprehension_id is not present, create the comprehension object if comprehension content if its present in request
            if args['comprehension_text'] is not None:
                comprehension = Comprehension.create(args['comprehension_text'])
        comprehension_id = comprehension.id if comprehension is not None else (args['comprehension_id'] if args['comprehension_id'] is not None else None)

        status = {
            # keeping string values of 0 and 1 because postgres hstore needs keys and values as text
            'categorized': '0',
            'proof_read_categorization': '0',
            'text_solution_added': '1' if args['text_solution'] is not None else '0',
            'video_solution_added': '1' if args['video_solution_url'] is not None else '0',
            'proof_read_text_solution': '0',
            'proof_read_video_solution': '0',
            'finalized': '0',
            'error_reported': '0'
        }

        # If question is categorized
        if self.is_categorization_complete(args):
            status['categorized'] = '1'
            status['proof_read_categorization'] = '1'

        text_solution_submitted_by_type, text_solution_submitted_by_id, text_solution_added_by_type, text_solution_added_by_id = [None]*4
        if args['text_solution'] is not None:
            status['text_solution_added'] = '1'
            status['proof_read_text_solution'] = '1'
            text_solution_submitted_by_type = args['text_solution_by']['type']
            text_solution_submitted_by_id = args['text_solution_by']['id']
            text_solution_added_by_type = kwargs['user_type'].id
            text_solution_added_by_id = kwargs['user'].id

        video_solution_submitted_by_type, video_solution_submitted_by_id, video_solution_added_by_type, video_solution_added_by_id = [None]*4
        if args['video_solution_url'] is not None:
            status['video_solution_added'] = '1'
            status['proof_read_video_solution'] = '1'
            video_solution_submitted_by_type = args['video_solution_by']['type']
            video_solution_submitted_by_id = args['video_solution_by']['id']
            video_solution_added_by_type = kwargs['user_type'].id
            video_solution_added_by_id = kwargs['user'].id

        question = Question.create(content=args['content'], status=status, comprehension_id=comprehension_id,
                                   ontology_id=args['ontology_id'], average_time=args['average_time'],
                                   nature=args['nature'], type=args['type'], difficulty=args['difficulty'],
                                   text_solution=args['text_solution'], video_solution_url=args['video_solution_url'],
                                   text_solution_by_type=text_solution_added_by_type if args['text_solution_by'] is not None else None,
                                   text_solution_by_id=text_solution_added_by_id if args['text_solution_by'] is not None else None,
                                   video_solution_by_type=video_solution_added_by_type if args['video_solution_by'] is not None else None,
                                   video_solution_by_id=video_solution_added_by_id if args['video_solution_by'] is not None else None,
                                   created_by_type=kwargs['user_type'].id, created_by_id=kwargs['user'].id, **args['options'])

        if status['categorized'] == '1':
            # Question is categorized. Submit it for approval
            ontology_obj = Ontology.query.get(args['ontology_id'])

            # Do a category submission so it can be verified by teacher
            CategorySubmission.create(kwargs['user_type'].id, kwargs['user'].id, question.id, ontology=ontology_obj.absolute_path,
                                      type=args['type'], nature=args['nature'], difficulty=args['difficulty'],
                                      average_time=args['average_time'])

        if args['text_solution'] is not None:
            # Text solution is provided. Do a solution submission so it can be verified by teacher
            SolutionSubmission.create(text_solution_submitted_by_type, text_solution_submitted_by_id, question.id, 'text', args['text_solution'])

        if args['video_solution_url'] is not None:
            # Video solution is provided. Do a solution submission so it can be verified by teacher
            SolutionSubmission.create(video_solution_submitted_by_type, video_solution_submitted_by_id, question.id, 'video', args['video_solution_url'])

        return {
            'comprehension_id': comprehension_id,
            'question': question,
            'error': False
        }

from exam_app.models.question import Question
from exam_app.models.comprehension import Comprehension
from exam_app.models.ontology import Ontology
from exam_app.models.category_submission import CategorySubmission
from exam_app.models.solution_submission import SolutionSubmission
from exam_app.models.users import UserTypes
