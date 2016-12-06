# -*- coding: utf-8 -*-

import json
import datetime
import math
from collections import Counter

from flask.ext.restful import reqparse, fields, marshal_with
from sqlalchemy import or_, and_

from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import InvalidMockTestId, MockTestTestAlreadyAttempted, PaymentPlanLimitReached, InvalidQuestionId
from exam_app import app
from exam_app.models.mock_test import MockTest
from exam_app.models.attempted_mock_test import AttemptedMockTest
from exam_app.models import db
from exam_app.resources.mock_test_list import MockTestList
from exam_app.resources.question_list import QuestionList
from exam_app.models.question import Question
from exam_app.models.ontology import Ontology
from exam_app.async_tasks import upload_report_and_send_email
from exam_app.models.batch import Batch
from exam_app.models.pushed_mock_test import PushedMockTest


class AttemptedMockTestList(AuthorizedResource):
    @classmethod
    def answers_json_type(cls, data):
        """
        Parse the answers json which is in the format
        {
            <question_id1>: {
                'options': [<opt1_index>],            single correct question
                'time': <in seconds>,
                'answer_order': <answer order>,
                'durations': [[<start>, <end>], [<start>, <end>], [<start>, <end>]]
            },
            <question_id2>: {
                'options': [<opt1_index>, <opt2_index>],    multi correct question
                'time': <in seconds>,
                'answer_order': <answer order>,
                'durations': [[<start>, <end>], [<start>, <end>], [<start>, <end>]]
            },
            <question_id2>: {
                'options': [],                  non attempted questions
                'time': <in seconds>,
                'answer_order': <answer order>,
                'durations': [[<start>, <end>], [<start>, <end>], [<start>, <end>]]
            },
        }

        :param data:
        :return:
        """
        parsed_data = json.loads(data)
        if not isinstance(parsed_data, dict):
            raise ValueError("JSON not as expected")
        for key, value in parsed_data.items():
            if not ('options' in value and isinstance(value['options'], list)):
                raise ValueError('options key not present in answers or not list')
            if not ('time' in value and (isinstance(value['time'], float) or isinstance(value['time'], int))):
                raise ValueError('time key not present in answers or not number')
        return parsed_data

    class JSObject(fields.Raw):
        def format(self, value):
            return json.loads(value)

    attempted_mock_test_obj = {
        'id': fields.Integer,
        'pushed_mock_test_id': fields.Integer,
        'mock_test_id': fields.Integer,
        'score': fields.Float,
        'answers': JSObject,
        'analysis': JSObject,
        'attempted_at': fields.String
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'attempted_mock_tests': fields.List(fields.Nested(attempted_mock_test_obj)),
        'mock_tests': fields.List(fields.Nested(MockTestList.mock_test_obj)),
        'questions': fields.List(fields.Nested(QuestionList.question_obj)),
        'accuracy': fields.Float,
        'speed': fields.Float
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'attempted_mock_test': fields.Nested(attempted_mock_test_obj)
    }

    @staticmethod
    def get_duration_key(duration):
        """
        Get key corresponding to the duration which is used with dictionary durations_dict

        :param duration: a list of start and end instants of a duration
        :return:
        """
        if len(duration) == 2:
            return '%s-%s' % (str(duration[0]), str(duration[1]))
        if len(duration) == 1:
            return '%s-%s' % (str(duration[0]), str(duration[0]))
        if len(duration) == 0:
            return None

    @staticmethod
    def get_cumulative_analysis(student_id, institute_id=None):
        # get mock tests by student which have completed
        if institute_id is not None:
            batches = Batch.get_filtered(institute_id=institute_id)
            pushed_mock_tests = PushedMockTest.query.filter(PushedMockTest.batch_id.in_([b.id for b in batches]))
            attempted_mock_tests = AttemptedMockTest.query.filter(AttemptedMockTest.student_id == student_id, AttemptedMockTest.score != None,
                                                                  AttemptedMockTest.pushed_mock_test_id.in_([p.id for p in pushed_mock_tests])).all()
        else:
            attempted_mock_tests = AttemptedMockTest.query.filter(AttemptedMockTest.student_id == student_id, AttemptedMockTest.score != None).all()
        mock_test_ids = [amt.mock_test_id for amt in attempted_mock_tests]
        mock_tests = MockTest.query.filter(MockTest.id.in_(mock_test_ids)).all()
        question_ids = set()
        overall_correct_q_ids = set()
        overall_incorrect_q_ids = set()
        overall_not_attempted_q_ids = set()
        total_ideal_time = 0
        total_taken_time = 0

        for amt in attempted_mock_tests:
            analysis = json.loads(amt.analysis)
            subjects = analysis['subjects']
            for sid in subjects:
                overall_correct_q_ids.update(set(subjects[sid]['correct']))
                overall_incorrect_q_ids.update(set(subjects[sid]['incorrect']))
                overall_not_attempted_q_ids.update(set(subjects[sid]['not_attempted']))

        question_ids.update(overall_correct_q_ids)
        question_ids.update(overall_incorrect_q_ids)
        question_ids.update(overall_not_attempted_q_ids)
        questions = {q.id: q for q in Question.get_filtertered_list(include_question_ids=list(question_ids))['questions']}
        overall_attempted_count = len(overall_incorrect_q_ids) + len(overall_correct_q_ids)
        accuracy = round(len(overall_correct_q_ids)*100.0/overall_attempted_count, 2) if overall_attempted_count > 0 else 0.0

        for amt in attempted_mock_tests:
            answers = json.loads(amt.answers)
            for q_id, answer in answers.items():
                q_id = int(q_id)
                # if attempted question
                if len(answer['options']) != 0 and q_id in questions:
                    total_ideal_time += questions[q_id].average_time
                    total_taken_time += answer['time']

        overall_speed = total_ideal_time - total_taken_time

        return {
            'attempted_mock_tests': attempted_mock_tests,
            'mock_tests': mock_tests,
            'questions': questions.values(),
            'accuracy': accuracy,
            'speed': overall_speed
        }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        student_id = kwargs['user'].id
        return self.get_cumulative_analysis(student_id)

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('mock_test_id', type=int, required=True)
        parser.add_argument('pushed_mock_test_id', type=int)
        parser.add_argument('answers', type=self.__class__.answers_json_type, required=True)
        args = parser.parse_args()
        mock_test_id = args['mock_test_id']
        pushed_mock_test_id = args['pushed_mock_test_id']
        mock_test = MockTest.query.get(mock_test_id)
        if mock_test is None:
            raise InvalidMockTestId

        # get attempted mock tests by the student which have same pushed id as in this request or a null pushed id and
        # same mock test id as this request. If such a mock test is found error is returned. This prevents reattempting
        # the mock test probably from a different browser/ browser tab
        amt = AttemptedMockTest.query.filter(AttemptedMockTest.student_id == kwargs['user'].id, or_(
            and_(AttemptedMockTest.pushed_mock_test_id != None, AttemptedMockTest.pushed_mock_test_id == pushed_mock_test_id),
            and_(AttemptedMockTest.pushed_mock_test_id == None, AttemptedMockTest.mock_test_id == mock_test_id))).all()
        if len(amt) > 0:
            raise MockTestTestAlreadyAttempted

        # get attempted mock tests of the same type and check if number of permitted mock tests as per payment plan is
        # exceeded or not
        attempted_mock_test_ids = [amt.mock_test_id for amt in AttemptedMockTest.query.filter(AttemptedMockTest.student_id == kwargs['user'].id).all()]
        attempted_mock_tests = MockTest.query.filter(MockTest.id.in_(attempted_mock_test_ids)).all()
        attempted_mock_tests_of_type = filter(lambda m: m.type == mock_test.type, attempted_mock_tests)
        if len(attempted_mock_tests_of_type) >= app.config['PAYMENT_PLAN'][mock_test.type]:
            raise PaymentPlanLimitReached

        # create attempted test entry
        attempted_mock_test = AttemptedMockTest(pushed_mock_test_id=pushed_mock_test_id, mock_test_id=mock_test_id, student_id=kwargs['user'].id,
                                attempted_at=datetime.datetime.utcnow())
        answers = args['answers']
        question_ids = answers.keys()
        questions = {q.id: q for q in Question.get_filtertered_list(include_question_ids=question_ids)['questions']}
        if len(question_ids) != len(questions):
            raise InvalidQuestionId
        marking_scheme = app.config['MARKING_SCHEME']
        target_exam = mock_test.target_exam

        maximum_marks = 0
        total_marks = 0
        subject_wise = {}
        topic_wise = {}

        question_overtime = app.config['QUESTION_OVER_TIME']

        perfect_attempts = []
        wasted_attempts = []
        overtime_attempts = []
        completely_wasted_attempts = []

        ontology = {node.id: node for node in Ontology.get_all_nodes_of_tree()}

        # dictionary with string value of duration as key and value as question id
        durations_dict = {}

        # list with durations of questions
        durations_list = []

        for question_id, value in answers.items():
            question_id = int(question_id)
            question = questions[question_id]
            subject_id = question.ontology[0]
            topic_id = None
            for node_id in question.ontology:
                if node_id in ontology:
                    if ontology[node_id].type == '3':
                        topic_id = node_id
                        break

            # subject seen first time
            if subject_id not in subject_wise:
                subject_wise[subject_id] = {
                    'name': ontology[subject_id].name,
                    'topic_ids': [],
                    'correct': [],
                    'incorrect': [],
                    'not_attempted': [],
                    'marks': 0,
                    'time': 0,
                    'maximum_marks': 0,
                    'perfect_attempts': [],
                    'wasted_attempts': [],
                    'overtime_attempts': [],
                    'completely_wasted_attempts': [],
                }

            # topic seen first time
            if topic_id is not None and topic_id not in topic_wise:
                topic_wise[topic_id] = {
                    'name': ontology[topic_id].name,
                    'correct': [],
                    'incorrect': [],
                    'not_attempted': [],
                    'marks': 0,
                    'time': 0,
                    'maximum_marks': 0,
                    'perfect_attempts': [],
                    'wasted_attempts': [],
                    'overtime_attempts': [],
                    'completely_wasted_attempts': [],
                }
                subject_wise[subject_id]['topic_ids'].append(topic_id)

            if subject_id not in marking_scheme[target_exam]:
                # subject id not added in marking scheme config, indicates config errors
                print 'subject id %s not added in marking scheme config, indicates config errors' % str(subject_id)
                continue

            if question.type not in marking_scheme[target_exam][subject_id]:
                # question type not added for subject in marking scheme config, indicates config errors
                print 'question type %s not added for subject in marking scheme config, indicates config errors' % str(question.type)
                continue

            print '-----------------------------------'
            print question.correct_options
            print '-----------------------------------'

            # if not attempted
            if len(value['options']) == 0:
                marks = marking_scheme[target_exam][subject_id][question.type]['not_attempted']
                value['marks'] = marks
                value['is_correct'] = False
                subject_wise[subject_id]['not_attempted'].append(question.id)
                if topic_id is not None:
                    topic_wise[topic_id]['not_attempted'].append(question.id)

            # if correct
            elif set(question.correct_options) == (set(value['options'])):
                marks = marking_scheme[target_exam][subject_id][question.type]['correct']
                value['marks'] = marks
                value['is_correct'] = True
                subject_wise[subject_id]['correct'].append(question.id)
                if topic_id is not None:
                    topic_wise[topic_id]['correct'].append(question.id)
                if value['time'] < question.average_time + question_overtime:
                    subject_wise[subject_id]['perfect_attempts'].append(question_id)
                    if topic_id is not None:
                        topic_wise[topic_id]['perfect_attempts'].append(question_id)
                    perfect_attempts.append(question.id)
                else:
                    subject_wise[subject_id]['overtime_attempts'].append(question_id)
                    if topic_id is not None:
                        topic_wise[topic_id]['overtime_attempts'].append(question_id)
                    overtime_attempts.append(question.id)

            # if incorrect
            else:
                marks = marking_scheme[target_exam][subject_id][question.type]['incorrect']
                value['marks'] = marks
                value['is_correct'] = False
                subject_wise[subject_id]['incorrect'].append(question.id)
                if topic_id is not None:
                    topic_wise[topic_id]['incorrect'].append(question.id)
                if value['time'] <= question.average_time:
                    subject_wise[subject_id]['wasted_attempts'].append(question_id)
                    if topic_id is not None:
                        topic_wise[topic_id]['wasted_attempts'].append(question_id)
                    wasted_attempts.append(question.id)
                else:
                    subject_wise[subject_id]['completely_wasted_attempts'].append(question_id)
                    if topic_id is not None:
                        topic_wise[topic_id]['completely_wasted_attempts'].append(question_id)
                    completely_wasted_attempts.append(question.id)

            for duration in value['durations']:
                duration_key = self.get_duration_key(duration)
                if duration_key is not None:
                    durations_dict[duration_key] = question.id
                    durations_list.append(duration)

            correct_answer_marks = marking_scheme[target_exam][subject_id][question.type]['correct']
            subject_wise[subject_id]['time'] += value['time']
            subject_wise[subject_id]['marks'] += marks
            subject_wise[subject_id]['maximum_marks'] += correct_answer_marks
            if topic_id is not None:
                topic_wise[topic_id]['time'] += value['time']
                topic_wise[topic_id]['marks'] += marks
                topic_wise[topic_id]['maximum_marks'] += correct_answer_marks

            total_marks += marks
            maximum_marks += correct_answer_marks

        total_time = 0
        total_correct = 0
        total_incorrect = 0
        total_not_attempted = 0
        overall_correct_q_ids = []
        overall_incorrect_q_ids = []
        total_ideal_time = 0
        total_taken_time = 0

        for sub in subject_wise.values():
            overall_correct_q_ids.extend(sub['correct'])
            overall_incorrect_q_ids.extend(sub['incorrect'])
            sub['accuracy'] = round(len(sub['correct'])*100.0/(len(sub['correct']) + len(sub['incorrect'])), 2) if (len(sub['correct']) + len(sub['incorrect'])) > 0 else 0.0
            total_time += sub['time']
            total_correct += len(sub['correct'])
            total_incorrect += len(sub['incorrect'])
            total_not_attempted += len(sub['not_attempted'])

        overall_attempted_count = len(overall_correct_q_ids) + len(overall_incorrect_q_ids)
        overall_accuracy = round(len(overall_correct_q_ids)*100.0/overall_attempted_count, 2) if overall_attempted_count > 0 else 0.0

        for q_id in overall_correct_q_ids + overall_incorrect_q_ids:
            q = questions[int(q_id)]
            total_ideal_time += q.average_time
            total_taken_time += answers[str(q_id)]['time']
        overall_speed = total_ideal_time - total_taken_time

        num_subjects = len(subject_wise.keys())
        attempt_order_time_window_length = total_time/(num_subjects*10)
        sorted_durations_list = sorted(durations_list, key=lambda d: d[0])
        subjects_attempt_order = []
        if int(attempt_order_time_window_length) > 0:
            for current_time_window_start in xrange(0, int(math.ceil(total_time)), int(attempt_order_time_window_length)):
                current_time_window_end = current_time_window_start + attempt_order_time_window_length
                i = -1
                j = -1
                for index, duration in enumerate(sorted_durations_list):
                    if len(duration) != 2:
                        continue
                    # if current_time_window_start lies in the current duration
                    if duration[0] <= current_time_window_start < duration[1]:
                        i = index
                        # if current_time_window_end lies in the current duration
                    if duration[0] < current_time_window_end <= duration[1]:
                        j = index
                        break

                # if time window start and end lie inside test duration
                if i != -1 and j != -1:
                    sub = []
                    for d in sorted_durations_list[i:j+1]:
                        question_id = durations_dict[self.get_duration_key(d)]
                        question = questions[question_id]
                        sub.append(question.ontology[0])
                    c = Counter(sub)
                    subjects_attempt_order.append(c.most_common(1)[0][0])

                # if time window start lies inside test duration but time window end does not
                elif i != -1 and j == -1:
                    sub = []
                    for d in sorted_durations_list[i:]:
                        question_id = durations_dict[self.get_duration_key(d)]
                        question = questions[question_id]
                        sub.append(question.ontology[0])
                    c = Counter(sub)
                    subjects_attempt_order.append(c.most_common(1)[0][0])

        attempted_mock_test.answers = json.dumps(answers)
        attempted_mock_test.score = total_marks
        attempted_mock_test.analysis = json.dumps({
            'subjects': subject_wise,
            'topics': topic_wise,
            'perfect': perfect_attempts,
            'overtime': overtime_attempts,
            'wasted': wasted_attempts,
            'completely_wasted': completely_wasted_attempts,
            'total_marks': total_marks,
            'maximum_marks': maximum_marks,
            'percentage_marks': round((total_marks*100.0/maximum_marks), 2) if maximum_marks > 0 else 0.0,
            'total_time': total_time,
            'total_correct': total_correct,
            'total_incorrect': total_incorrect,
            'total_not_attempted': total_not_attempted,
            'attempt_order_time_window_length': attempt_order_time_window_length,
            'subjects_attempt_order': subjects_attempt_order,
            'accuracy': overall_accuracy,
            'speed': overall_speed
        })

        db.session.add(attempted_mock_test)
        db.session.commit()
        upload_report_and_send_email.delay(attempted_mock_test.id)
        return {'attempted_mock_test': attempted_mock_test}
