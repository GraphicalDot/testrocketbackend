# -*- coding: utf-8 -*-

import json
import sys
import heapq

from flask.ext.restful import reqparse, fields, marshal_with
from sqlalchemy import or_, and_

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app import app
from exam_app.models.batch import Batch
from exam_app.models.student_batches import StudentBatches
from exam_app.models.pushed_mock_test import PushedMockTest
from exam_app.models.attempted_mock_test import AttemptedMockTest
from exam_app.models.mock_test import MockTest
from exam_app.models.question import Question
from exam_app.models.student import Student
from exam_app.models.ontology import Ontology


class InstituteAnalysis(AuthorizedResource):
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('target_exams', type=comma_separated_ints_type)
        parser.add_argument('batches', type=comma_separated_ints_type)
        args = parser.parse_args()
        # if batches are provided
        if args['batches'] is not None:
            batch_ids = args['batches']
        # if batches are not provided but target exams are provided
        elif args['target_exams'] is not None:
            target_exams = map(str, args['target_exams'])
            batch_ids = [b.id for b in Batch.query.filter(Batch.target_exam.in_(target_exams), Batch.status == 1,
                                                          Batch.institute_id == kwargs['user'].id).all()]
        # if no filters are used then get all batches for this institute
        else:
            batch_ids = [b.id for b in Batch.get_filtered(institute_id=kwargs['user'].id)]

        students = {}
        for sb in StudentBatches.query.filter(StudentBatches.batch_id.in_(batch_ids)).all():
            student_id = sb.student_id
            batch_id = sb.batch_id
            if student_id not in students:
                students[student_id] = {}
            if batch_id not in students[student_id]:
                # not using dictionary for `joined_at` and `left_at` on purpose, saving memory
                students[student_id][batch_id] = (sb.joined_at, sb.left_at)

        # current_students, past_students = [], []
        # for student in students:
        #     (current_students, past_students)[student['left_at'] is not None].append(student)

        # Get all mock tests that were pushed to the batches with id in `batch_ids`
        pushed_mock_tests = PushedMockTest.query.filter(PushedMockTest.batch_id.in_(batch_ids)).all()

        exprs = [AttemptedMockTest.pushed_mock_test_id.in_([p.id for p in pushed_mock_tests])]

        # if len(current_students) > 0:
        #     exprs.append(AttemptedMockTest.student_id.in_([s['id'] for s in current_students]))
        # if len(past_students) > 0:
        #     for student in past_students:
        #         exprs.append(or_(AttemptedMockTest.student_id == student['id'], AttemptedMockTest.attempted_at < student['left_at']))

        attempted_mock_tests = AttemptedMockTest.query.filter(*exprs).all()

        mock_test_ids = list({a.mock_test_id for a in attempted_mock_tests})
        mock_tests = {m.id: m for m in MockTest.query.filter(MockTest.id.in_(mock_test_ids)).all()}

        question_ids = set()
        for mock_test in mock_tests.values():
            subjects = json.loads(mock_test.question_ids)
            for sid, data in subjects.items():
                question_ids.update(set(data['q_ids']))

        question_difficulty = {q.id: q.difficulty for q in Question.query.with_entities(Question.id, Question.difficulty).filter(Question.id.in_(list(question_ids)))}
        exam_weights = app.config['TARGET_EXAM_WEIGHT']

        performance = {}
        topics = {}
        attempted_test_count = {}
        for amt in attempted_mock_tests:
            mock_test = mock_tests[amt.mock_test_id]
            d = []
            subjects = json.loads(mock_test.question_ids)
            analysis = json.loads(amt.analysis)
            for sid, data in subjects.items():
                for q_id in data['q_ids']:
                    d.append(int(question_difficulty[q_id]))
            average_difficulty = sum(d)/float(len(d))
            p = (amt.score/analysis['maximum_marks'])*exam_weights[mock_tests[amt.mock_test_id].target_exam] * average_difficulty

            if amt.student_id in performance:
                performance[amt.student_id][amt.id] = p
            else:
                performance[amt.student_id] = {
                    amt.id: p
                }
            attempted_test_count[amt.student_id] = attempted_test_count.get(amt.student_id, 0) + 1
            # this set is used for keeping track of those topic ids whose subject id not known yet
            new_topic_ids = set()
            for topic_id, data in analysis['topics'].items():
                topic_id = int(topic_id)
                total = len(data['not_attempted']) + len(data['correct']) + len(data['incorrect'])
                correct = len(data['correct'])
                if topic_id in topics:
                    topics[topic_id]['total'] += total
                    topics[topic_id]['correct'] += correct
                else:
                    # topic has not been seen yet
                    new_topic_ids.add(topic_id)
                    topics[topic_id] = {
                        'total': total,
                        'correct': correct
                    }
            for sid, data in analysis['subjects'].items():
                sid = int(sid)
                subject_topic_ids = set(data['topic_ids'])
                # topic ids of the current subject whose subject id was not known
                found_topic_ids = subject_topic_ids.intersection(new_topic_ids)
                for tid in found_topic_ids:
                    topics[tid]['subject_id'] = sid
                new_topic_ids = new_topic_ids - found_topic_ids

        student_count = len(performance)
        top_student_count = int(student_count*(app.config['TOP_PERFORMERS_PERCENTAGE']/100))
        top_student_count = top_student_count if top_student_count > app.config['TOP_PERFORMERS_MIN_COUNT'] else app.config['TOP_PERFORMERS_MIN_COUNT']
        bottom_student_count = int(student_count*(app.config['BOTTOM_PERFORMERS_PERCENTAGE']/100))
        bottom_student_count = bottom_student_count if bottom_student_count > app.config['BOTTOM_PERFORMERS_MIN_COUNT'] else app.config['BOTTOM_PERFORMERS_MIN_COUNT']
        top_students = {}
        bottom_students = {}

        for student_id, data in performance.items():
            score = sum(data.values())/float(len(data.values()))

            if len(top_students) < top_student_count:
                top_students[student_id] = score
            else:
                min_score = min(top_students.values())
                if score > min_score:
                    k = None
                    for i, s in top_students.items():
                        if s == min_score:
                            k = i
                            break
                    if k is not None:
                        del top_students[k]
                        top_students[student_id] = score

            if len(bottom_students) < bottom_student_count:
                bottom_students[student_id] = score
            else:
                max_score = max(bottom_students.values())
                if score < max_score:
                    k = None
                    for i, s in bottom_students.items():
                        if s == max_score:
                            k = i
                            break
                    if k is not None:
                        del bottom_students[k]
                        bottom_students[student_id] = score

        # Students that appear both in top students and bottom students should be removed from bottom students
        for student_id in top_students:
            if student_id in bottom_students:
                del bottom_students[student_id]


        top_topic_count = app.config['TOP_TOPICS_COUNT']
        bottom_topic_count = app.config['BOTTOM_TOPICS_COUNT']
        top_topics = {}
        bottom_topics = {}
        top_topics_by_subjects = {}
        bottom_topics_by_subjects = {}
        subject_ids = set()

        for topic_id, data in topics.items():
            accuracy = (data['correct']*100.0)/data['total'] if data['total'] > 0 else 0
            subject_id = data['subject_id']
            subject_ids.add(subject_id)
            # Overall top topics

            # if number of top_topics found yet is less than required top topics then add topic to top_topics
            if len(top_topics) < top_topic_count:
                top_topics[topic_id] = accuracy
            # if number of top_topics found yet is more than or equal to required top_topics
            else:
                min_acc = min(top_topics.values())
                # if accuracy of current topic is more than minimum accuracy of any topic in top_topics
                if accuracy > min_acc:
                    k = None
                    # in the next loop the topic_id with minimum accuracy is found
                    for i, s in top_topics.items():
                        if s == min_acc:
                            k = i
                            break
                    # remove the topic_id with minimum accuracy
                    del top_topics[k]
                    # add current topic to top_topics
                    top_topics[topic_id] = accuracy

            # Subject wise top topics

            if subject_id not in top_topics_by_subjects or len(top_topics_by_subjects[subject_id]) < top_topic_count:
                if subject_id not in top_topics_by_subjects:
                    top_topics_by_subjects[subject_id] = {}
                top_topics_by_subjects[subject_id][topic_id] = accuracy
            else:
                min_acc = min(top_topics_by_subjects[subject_id].values())
                if accuracy > min_acc:
                    k = None
                    for i, s in top_topics_by_subjects[subject_id].items():
                        if s == min_acc:
                            k = i
                            break
                    del top_topics_by_subjects[subject_id][k]
                    top_topics_by_subjects[subject_id][topic_id] = accuracy

            # Overall bottom topics

            # if number of bottom_topics found yet is less than required bottom topics then add topic to bottom_topics
            if len(bottom_topics) < bottom_topic_count:
                bottom_topics[topic_id] = accuracy
            # if number of bottom_topics found yet is more than or equal to required bottom_topics
            else:
                max_acc = max(bottom_topics.values())
                # if accuracy of current topic is less than maximum accuracy of any topic in bottom_topics
                if accuracy < max_acc:
                    k = None
                    # in the next loop the topic_id with maximum accuracy is found
                    for i, s in bottom_topics.items():
                        if s == max_acc:
                            k = i
                            break
                    # remove the topic_id with maximum accuracy
                    del bottom_topics[k]
                    # add current topic to bottom_topics
                    bottom_topics[topic_id] = accuracy

            # Subject wise bottom topics

            if subject_id not in bottom_topics_by_subjects or len(bottom_topics_by_subjects[subject_id]) < bottom_topic_count:
                if subject_id not in bottom_topics_by_subjects:
                    bottom_topics_by_subjects[subject_id] = {}
                bottom_topics_by_subjects[subject_id][topic_id] = accuracy
            else:
                max_acc = max(bottom_topics_by_subjects[subject_id].values())
                if accuracy < max_acc:
                    k = None
                    for i, s in bottom_topics_by_subjects[subject_id].items():
                        if s == max_acc:
                            k = i
                            break
                    del bottom_topics_by_subjects[subject_id][k]
                    bottom_topics_by_subjects[subject_id][topic_id] = accuracy

        # Topics that appear both in top topics and bottom topics should be removed from bottom topics
        for topic_id in top_topics:
            if topic_id in bottom_topics:
                del bottom_topics[topic_id]

        # Topics that appear both in top topics for a subject and bottom topics of the same subject should be removed
        # from bottom topics of that subject
        for subject_id in top_topics_by_subjects:
            if subject_id in bottom_topics_by_subjects:
                for topic_id in top_topics_by_subjects[subject_id]:
                    if topic_id in bottom_topics_by_subjects[subject_id]:
                        del bottom_topics_by_subjects[subject_id][topic_id]

        student_objs = {s.id: s for s in Student.query.filter(Student.id.in_(top_students.keys()+bottom_students.keys()))}

        top_students_list = []
        bottom_students_list = []

        # Calculating attendance for top_students
        for student_id in top_students:
            total_pushed = 0
            seen_mock_test_ids = set()
            for batch_id, dates in students[student_id].items():
                # if current student
                if dates[1] is None:
                    for pmt in pushed_mock_tests:
                        # if mock test was pushed to this batch
                        if pmt.batch_id == batch_id:
                            if pmt.mock_test_id in seen_mock_test_ids:
                                continue
                            total_pushed += 1
                            seen_mock_test_ids.add(pmt.mock_test_id)
                # if past student
                else:
                    for pmt in pushed_mock_tests:
                        # if mock test was pushed to this batch before this student left the batch
                        if pmt.batch_id == batch_id and dates[0] < pmt.pushed_at < dates[1]:
                            if pmt.mock_test_id in seen_mock_test_ids:
                                continue
                            total_pushed += 1
                            seen_mock_test_ids.add(pmt.mock_test_id)
            student = {
                'id': student_id,
                'attendance': (attempted_test_count[student_id]*100.0)/total_pushed if total_pushed > 0 else 0,
                'name': student_objs[student_id].name,
                'score': top_students[student_id]
            }
            top_students_list.append(student)

        # Calculating attendance for bottom_students
        for student_id in bottom_students:
            total_pushed = 0
            for batch_id, dates in students[student_id].items():
                # if current student
                if dates[1] is None:
                    for pmt in pushed_mock_tests:
                        # if mock test was pushed to this batch
                        if pmt.batch_id == batch_id:
                            total_pushed += 1
                # if past student
                else:
                    for pmt in pushed_mock_tests:
                        # if mock test was pushed to this batch before this student left the batch
                        if pmt.batch_id == batch_id and dates[0] < pmt.pushed_at < dates[1]:
                            total_pushed += 1

            student = {
                'id': student_id,
                'attendance': (attempted_test_count[student_id]*100.0)/total_pushed if total_pushed > 0 else 0,
                'name': student_objs[student_id].name,
                'score': bottom_students[student_id]
            }
            bottom_students_list.append(student)

        required_topic_ids = set()
        for d in top_topics_by_subjects.values():
            required_topic_ids.update(set(d.keys()))
        for d in bottom_topics_by_subjects.values():
            required_topic_ids.update(set(d.keys()))

        node_objs = {n.id: n for n in Ontology.query.filter(or_(Ontology.id.in_(top_topics.keys()+bottom_topics.keys()),
                                                                Ontology.id.in_(list(subject_ids)),
                                                                Ontology.id.in_(list(required_topic_ids))))}

        top_topics_list = []
        bottom_topics_list = []

        for topic_id, accuracy in top_topics.items():
            topic_id = int(topic_id)
            subject_id = node_objs[topic_id].parent_path[0]
            subject_name = node_objs[subject_id].name
            topic = {
                'id': topic_id,
                'name': node_objs[topic_id].name,
                'accuracy': accuracy,
                'subject_id': subject_id,
                'subject_name': subject_name
            }
            top_topics_list.append(topic)

        for topic_id, accuracy in bottom_topics.items():
            topic_id = int(topic_id)
            subject_id = node_objs[topic_id].parent_path[0]
            subject_name = node_objs[subject_id].name
            topic = {
                'id': topic_id,
                'name': node_objs[topic_id].name,
                'accuracy': accuracy,
                'subject_id': subject_id,
                'subject_name': subject_name
            }
            bottom_topics_list.append(topic)

        for subject_id, data in top_topics_by_subjects.items():
            subject_name = node_objs[subject_id].name
            topics_list = tuple(data.items())
            top_topics_by_subjects[subject_id] = [{
                'id': tpl[0],
                'name': node_objs[tpl[0]].name,
                'accuracy': tpl[1],
                'subject_id': subject_id,
                'subject_name': subject_name
            } for tpl in topics_list]

        for subject_id, data in bottom_topics_by_subjects.items():
            subject_name = node_objs[subject_id].name
            topics_list = tuple(data.items())
            bottom_topics_by_subjects[subject_id] = [{
                'id': tpl[0],
                'name': node_objs[tpl[0]].name,
                'accuracy': tpl[1],
                'subject_id': subject_id,
                'subject_name': subject_name
            } for tpl in topics_list]

        return {
            'top_students': top_students_list,
            'bottom_students': bottom_students_list,
            'top_topics': top_topics_list,
            'bottom_topics': bottom_topics_list,
            'top_topics_by_subjects': top_topics_by_subjects,
            'bottom_topics_by_subjects': bottom_topics_by_subjects
        }