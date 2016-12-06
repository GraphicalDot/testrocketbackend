# -*- coding: utf-8 -*-

import json
from base64 import b64encode
from collections import Counter, OrderedDict
import math

from flask.views import MethodView
from flask import render_template, redirect, request

from exam_app import app
from exam_app.models.attempted_mock_test import AttemptedMockTest
from exam_app.models.mock_test import MockTest
from exam_app.models.ontology import Ontology
from exam_app.models.question import Question
from exam_app.resources.attempted_mock_test import AttemptedMockTest as AttemptedMockTestResource


class PdfReport(MethodView):
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

    def get(self, *args, **kwargs):
        attempted_mock_test_id = kwargs['id']
        attempted_mock_test = AttemptedMockTest.query.filter(AttemptedMockTest.id == attempted_mock_test_id, AttemptedMockTest.pdf_report_url == None).first()
        if attempted_mock_test is None:
            return '404 Not Found', 404

        mock_test = MockTest.query.get(attempted_mock_test.mock_test_id)
        if mock_test is None:
            return '404 Not Found', 404

        if attempted_mock_test.answers is None:
            return '404 Not Found', 404

        page = request.args.get('page')

        ontology = {node.id: node for node in Ontology.get_all_nodes_of_tree()}

        analysis = json.loads(attempted_mock_test.analysis)
        for sid, data in analysis['subjects'].items():
            data['name'] = ontology[int(sid)].name

        analysis['cutoff'] = mock_test.cutoff
        analysis['percentile'] = AttemptedMockTestResource.get_percentile(attempted_mock_test)
        rank_colleges = AttemptedMockTestResource.get_rank_and_college(attempted_mock_test, mock_test)
        if rank_colleges is not None:
            analysis['expected_rank'], analysis['expected_colleges'] = rank_colleges

        common_page_vars = {
            'page': page,
            'analysis': analysis,
            'mock_test_name': mock_test.name,
            'target_exam_name': app.config['TARGET_EXAMS'][mock_test.target_exam]
        }

        if page == 'page1':
            return render_template('pdf_report.html', **common_page_vars)

        if page in (None, 'page2'):
            MAXIMUM_TIME_WIDTH = 1000.0                                                                                 # px
            MAXIMUM_TIME = mock_test.duration                                                                       # seconds
            ATTEMPT_TIME_DISPLAY_UNIT_SECONDS = 150                                                                 # seconds
            #ATTEMPT_TIME_DISPLAY_UNIT_WIDTH = (MAXIMUM_TIME_WIDTH/MAXIMUM_TIME)*ATTEMPT_TIME_DISPLAY_UNIT_SECONDS     # px
            subject_attempt_order = []
            time_window_chunk_length = int(math.floor(ATTEMPT_TIME_DISPLAY_UNIT_SECONDS/analysis['attempt_order_time_window_length']))
            temp = []
            for i, sid in enumerate(analysis['subjects_attempt_order']):
                temp.append(sid)
                if (i+1) % time_window_chunk_length == 0:
                    temp.append(sid)
                    c = Counter(temp)
                    subject_attempt_order.append(c.most_common(1)[0][0])
                    temp = []

            color_classes = ['info', 'primary', 'success', 'warning', 'danger']
            unique_subject_ids = list(set(subject_attempt_order))

            subject_colors = {sid: color_classes[unique_subject_ids.index(sid)] for sid in unique_subject_ids}
            total_time_bar_width = round(analysis['total_time']*(MAXIMUM_TIME_WIDTH/MAXIMUM_TIME))
            subject_attempt_order = [{
                'name': ontology[sid].name,
                'id': sid,
                'color_class': subject_colors[sid],
                'width': 100.0/len(subject_attempt_order)
            } for sid in subject_attempt_order]
            combined_subjects = []
            last_subject = None
            for i, s in enumerate(subject_attempt_order):
                if last_subject is not None:
                    if last_subject == s['id']:
                        combined_subjects[-1]['width'] += s['width']
                    else:
                        combined_subjects.append(s)
                        last_subject = s['id']
                else:
                    combined_subjects.append(s)
                    last_subject = s['id']

            subject_attempt_legend = [{'name': ontology[sid].name, 'color': subject_colors[sid]} for sid in unique_subject_ids]

            mtqi = json.loads(mock_test.question_ids)
            sorted_subjects = OrderedDict(sorted(analysis['subjects'].items(), key=lambda t: mtqi[t[0]]['order']))

            if page == 'page2':
                return render_template('pdf_report.html', subject_attempt_order=combined_subjects, total_time_bar_width=total_time_bar_width,
                                   max_time_width=MAXIMUM_TIME_WIDTH, duration=MAXIMUM_TIME, subject_attempt_legend=subject_attempt_legend,
                                   sorted_subjects=sorted_subjects, **common_page_vars)

        if page in (None, 'page3', 'page4'):
            answers = json.loads(attempted_mock_test.answers)
            question_ids = answers.keys()
            questions = {q.id: q for q in Question.get_filtertered_list(include_question_ids=question_ids)['questions']}

            # dictionary with string value of duration as key and value as question id
            durations_dict = {}
            # list with durations of questions
            durations_list = []

            for question_id, value in answers.items():
                for duration in value['durations']:
                    duration_key = self.get_duration_key(duration)
                    if duration_key is not None:
                        durations_dict[duration_key] = int(question_id)
                        durations_list.append(duration)

            sorted_durations_list = sorted(durations_list, key=lambda d: d[0])
            if mock_test.duration <= 7200:
                UNIT_TIME_DURATION = 600                        # seconds
            else:
                UNIT_TIME_DURATION = 900                        # seconds
            UNIT_TIME_DURATION = 600
            # ordered list of list of questions attempted every `UNIT_TIME_DURATION`
            question_attempt_order = []

            for current_time_window_start in xrange(0, int(math.ceil(analysis['total_time'])), UNIT_TIME_DURATION):
                current_time_window_end = current_time_window_start + UNIT_TIME_DURATION
                i = -1
                j = -1
                for index, duration in enumerate(sorted_durations_list):
                    # if current_time_window_start lies in the current duration
                    if duration[0] <= current_time_window_start < duration[1]:
                        i = index
                    # if current_time_window_end lies in the current duration
                    if duration[0] < current_time_window_end <= duration[1]:
                        j = index
                        break

                # if time window start and end lie inside test duration
                if i != -1 and j != -1:
                    qs = []
                    for d in sorted_durations_list[i:j+1]:
                        question_id = durations_dict[self.get_duration_key(d)]
                        qs.append(question_id)
                    question_attempt_order.append(qs)

                # if time window start lies inside test duration but time window end does not
                elif i != -1 and j == -1:
                    qs = []
                    for d in sorted_durations_list[i:]:
                        question_id = durations_dict[self.get_duration_key(d)]
                        qs.append(question_id)
                    question_attempt_order.append(qs)

            test_duration_minutes = mock_test.duration/60.0
            if page in (None, 'page3'):
                difficulty_map = {
                    '1': 'Easy',
                    '2': 'Easy',
                    '3': 'Medium',
                    '4': 'Medium',
                    '5': 'Hard'
                }
                # ordered list of list of difficulty counts every `UNIT_TIME_DURATION`
                difficulty_attempt_order = []
                for question_list in question_attempt_order:
                    easy = {
                        'count': 0,
                        'marks': 0
                    }
                    medium = {
                        'count': 0,
                        'marks': 0
                    }
                    hard = {
                        'count': 0,
                        'marks': 0
                    }
                    for qid in question_list:
                        dif = difficulty_map[questions[qid].difficulty]
                        if dif == 'Easy':
                            easy['count'] += 1
                            easy['marks'] += answers[str(qid)]['marks']
                        if dif == 'Medium':
                            medium['count'] += 1
                            medium['marks'] += answers[str(qid)]['marks']
                        if dif == 'Hard':
                            hard['count'] += 1
                            hard['marks'] += answers[str(qid)]['marks']
                    difficulty_attempt_order.append({
                        'minutes': (len(difficulty_attempt_order) + 1)*(UNIT_TIME_DURATION/60),
                        'easy': easy,
                        'medium': medium,
                        'hard': hard
                    })

                while len(difficulty_attempt_order) < 210*60/UNIT_TIME_DURATION:
                    difficulty_attempt_order.append({
                        'minutes': (len(difficulty_attempt_order) + 1)*(UNIT_TIME_DURATION/60),
                        'easy': {
                            'count': 0,
                            'marks': 0
                        },
                        'medium': {
                            'count': 0,
                            'marks': 0
                        },
                        'hard': {
                            'count': 0,
                            'marks': 0
                        }
                    })

                if page == 'page3':
                    return render_template('pdf_report.html', difficulty_attempt_order=difficulty_attempt_order,
                                           test_duration_minutes=test_duration_minutes, **common_page_vars)

            if page in (None, 'page4'):
                # ordered list of list of attempt quality counts every `UNIT_TIME_DURATION`
                aq_attempt_order = []
                for question_list in question_attempt_order:
                    perfect = {
                        'count': 0,
                        'marks': 0
                    }
                    overtime = {
                        'count': 0,
                        'marks': 0
                    }
                    wasted = {
                        'count': 0,
                        'marks': 0
                    }
                    completely_wasted = {
                        'count': 0,
                        'marks': 0
                    }
                    for qid in question_list:
                        if qid in analysis['perfect']:
                            perfect['count'] += 1
                            perfect['marks'] += answers[str(qid)]['marks']
                        if qid in analysis['overtime']:
                            overtime['count'] += 1
                            overtime['marks'] += answers[str(qid)]['marks']
                        if qid in analysis['wasted']:
                            wasted['count'] += 1
                            wasted['marks'] += answers[str(qid)]['marks']
                        if qid in analysis['completely_wasted']:
                            completely_wasted['count'] += 1
                            completely_wasted['marks'] += answers[str(qid)]['marks']
                    aq_attempt_order.append({
                        'minutes': (len(aq_attempt_order) + 1)*(UNIT_TIME_DURATION/60),
                        'perfect': perfect,
                        'overtime': overtime,
                        'wasted': wasted,
                        'completely_wasted': completely_wasted
                    })

                while len(aq_attempt_order) < 210*60/UNIT_TIME_DURATION:
                    aq_attempt_order.append({
                        'minutes': (len(aq_attempt_order) + 1)*(UNIT_TIME_DURATION/60),
                        'perfect': {
                            'count': 0,
                            'marks': 0
                        },
                        'overtime': {
                            'count': 0,
                            'marks': 0
                        },
                        'wasted': {
                            'count': 0,
                            'marks': 0
                        },
                        'completely_wasted': {
                            'count': 0,
                            'marks': 0
                        }
                    })

                if page == 'page4':
                    return render_template('pdf_report.html', aq_attempt_order=aq_attempt_order,test_duration_minutes=test_duration_minutes,
                                           **common_page_vars)

        if page in (None, 'page5'):
            optimum_accuracy = 40               # percent
            spent_time = {}
            answers = json.loads(attempted_mock_test.answers)
            for subject_id in analysis['subjects']:
                if subject_id not in spent_time:
                    spent_time[subject_id] = {
                        'name': ontology[int(subject_id)].name,
                        'correct': 0,
                        'incorrect': 0,
                        'not_attempted': 0,
                        'total_time': analysis['subjects'][subject_id]['time']
                    }
                for q_id in analysis['subjects'][subject_id]['correct']:
                    spent_time[subject_id]['correct'] += answers[str(q_id)]['time']
                for q_id in analysis['subjects'][subject_id]['incorrect']:
                    spent_time[subject_id]['incorrect'] += answers[str(q_id)]['time']
                for q_id in analysis['subjects'][subject_id]['not_attempted']:
                    spent_time[subject_id]['not_attempted'] += answers[str(q_id)]['time']
            if page == 'page5':
                return render_template('pdf_report.html', optimum_accuracy=optimum_accuracy, spent_time=spent_time, **common_page_vars)

        return render_template('pdf_report.html', subject_attempt_order=combined_subjects, total_time_bar_width=total_time_bar_width,
                               max_time_width=MAXIMUM_TIME_WIDTH, duration=MAXIMUM_TIME, subject_attempt_legend=subject_attempt_legend,
                               sorted_subjects=sorted_subjects, test_duration_minutes=test_duration_minutes,
                               spent_time=spent_time, difficulty_attempt_order=difficulty_attempt_order,
                               aq_attempt_order=aq_attempt_order, optimum_accuracy=optimum_accuracy, **common_page_vars)