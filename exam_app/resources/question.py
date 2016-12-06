# -*- coding: utf-8 -*-

import datetime

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import InvalidQuestionId
from exam_app.resources.question_list import QuestionList


class Question(AuthorizedResource):

    @staticmethod
    def is_categorization_same(question, params):
        if question.nature == params['nature'] and question.type == params['type'] and question.difficulty == params['difficulty'] and \
                                        question.average_time == params['average_time']:
            if question.ontology[-1] == params['ontology_id']:
                return True
        return False

    response = {
        'error': fields.Boolean(default=False),
        'question': fields.Nested(QuestionList.question_obj)
    }

    @marshal_with(response)
    def get(self, *args, **kwargs):
        return {'question': QuestionModel.get(kwargs['id'])}

    @marshal_with(response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()

        # the next field will be present when a comprehension question is updated
        parser.add_argument('comprehension_text', type=unicode)

        # the next field will be present when a comprehension question is updated
        parser.add_argument('comprehension_id', type=int)

        parser.add_argument('ontology_id', type=int)
        parser.add_argument('nature', type=str)
        parser.add_argument('type', type=str)
        parser.add_argument('difficulty', type=str)
        parser.add_argument('average_time', type=int)
        parser.add_argument('content', type=unicode, required=True)
        parser.add_argument('options', type=options_json_type, required=True)
        parser.add_argument('text_solution', type=unicode)
        parser.add_argument('video_solution_url', type=str)
        parser.add_argument('text_solution_by', type=user_json_type)
        parser.add_argument('video_solution_by', type=user_json_type)
        parser.add_argument('proof_read_categorization', type=int, choices=[0,1])
        parser.add_argument('proof_read_text_solution', type=int, choices=[0,1])
        parser.add_argument('proof_read_video_solution', type=int, choices=[0,1])
        parser.add_argument('error_reported', type=str, choices=['0', '1'])
        args = parser.parse_args()

        question = QuestionModel.get(kwargs['id'])
        if question is None:
            raise InvalidQuestionId

        comprehension = None
        if args['comprehension_id'] is not None:
            # comprehension_id is present, just update the comprehension content if its present in request
            if args['comprehension_text'] is not None:
                comprehension = Comprehension.update(args['comprehension_id'], args['comprehension_text'])
        else:
            # comprehension_id is not present, create the comprehension object if comprehension content is present in request
            if args['comprehension_text'] is not None:
                comprehension = Comprehension.create(args['comprehension_text'])
        comprehension_id = comprehension.id if comprehension is not None else (args['comprehension_id'] if args['comprehension_id'] is not None else None)

        status = question.status

        # if complete categorization submitted
        if QuestionList.is_categorization_complete(args):
            ontology_obj = Ontology.query.get(args['ontology_id'])
            # question was uncategorized
            if status['categorized'] == '0':
                # set categorization flag
                status['categorized'] = '1'
                status['proof_read_categorization'] = '1'
                # delete any previous category submission
                # CategorySubmission.query.filter_by(question_id=question.id).delete()
                # create a category submission that will be sent for proof reading
                CategorySubmission.create(kwargs['user_type'].id, kwargs['user'].id, question.id, ontology=ontology_obj.absolute_path,
                                      type=args['type'], nature=args['nature'], difficulty=args['difficulty'],
                                      average_time=args['average_time'])

            # question was categorized
            else:
                # if edited from proof_read_categorization
                if args['proof_read_categorization'] == 1:
                    # set proof_read_categorization flag
                    status['proof_read_categorization'] = '1'
                    # if categorization has changed
                    if not self.is_categorization_same(question, args):
                        # reject any previous accepted category submissions and delete their approvals
                        prev_submissions = CategorySubmission.query.filter(CategorySubmission.question_id == question.id, CategorySubmission.status == 'accepted').all()
                        for s in prev_submissions:
                            s.status = 'rejected'
                            CategoryApproval.query.filter_by(submission_id=s.id).delete()
                        # create a new accepted category submission
                        cs = CategorySubmission.create(kwargs['user_type'].id, kwargs['user'].id, question.id, ontology=ontology_obj.absolute_path,
                                          type=args['type'], nature=args['nature'], difficulty=args['difficulty'],
                                          average_time=args['average_time'], status='accepted')
                    else:
                        # get the category submission for this question which has neither been accepted nor rejected
                        cs = CategorySubmission.query.filter(CategorySubmission.question_id == question.id, CategorySubmission.status == None).first()

                    # create category submission approval
                    CategoryApproval.create(cs.id, kwargs['user_type'].id, kwargs['user'].id)

                # edited from anywhere except proof_read_categorization
                else:
                    # if categorization has changed
                    if not self.is_categorization_same(question, args):
                        # delete any previous category submission and its corresponding approvals
                        CategorySubmission.query.filter_by(question_id=question.id).delete()
                        CategorySubmission.create(kwargs['user_type'].id, kwargs['user'].id, question.id, ontology=ontology_obj.absolute_path,
                                          type=args['type'], nature=args['nature'], difficulty=args['difficulty'],
                                          average_time=args['average_time'])

                        # if question was already proof read categorized, then reset proof_read_categorization
                        status['proof_read_categorization'] = '1'
                        #if status['proof_read_categorization'] == '1':
                        #    status['proof_read_categorization'] = '0'

        # if incomplete categorization submitted
        else:
            status['categorized'] = '0'
            status['proof_read_categorization'] = '0'
            status['finalized'] = '0'
            # delete any previous category submission and its corresponding approvals
            CategorySubmission.query.filter_by(question_id=question.id).delete()

        text_solution_submitted_by_type, text_solution_submitted_by_id, text_solution_added_by_type, text_solution_added_by_id = [None]*4

        # if text solution is submitted
        if args['text_solution'] is not None:
            text_solution_submitted_by_type = args['text_solution_by']['type']
            text_solution_submitted_by_id = args['text_solution_by']['id']
            text_solution_added_by_type = kwargs['user_type'].id
            text_solution_added_by_id = kwargs['user'].id

            # question had no text solution
            if status['text_solution_added'] == '0':
                status['text_solution_added'] = '1'
                status['proof_read_text_solutions'] = '1'
                # delete any previous text solution submission and its corresponding approvals
                #SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id, SolutionSubmission.solution_type == 'text').delete()
                # create a new text solution submission
                SolutionSubmission.create(text_solution_submitted_by_type, text_solution_submitted_by_id, question.id, 'text', args['text_solution'])
            # question had text solution
            else:
                # if came from proof_read_text_solution
                if args['proof_read_text_solution'] == 1:
                    status['text_solution_added'] = '1'
                    status['proof_read_text_solution'] = '1'
                    # if text solution changed
                    if QuestionModel.parse_content(args['text_solution']) != question.text_solution:
                        # reject any previous accepted text solution submissions and delete their corresponding approvals
                        prev_submissions = SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id,
                                                                           SolutionSubmission.solution_type == 'text', SolutionSubmission.status == 'accepted').all()
                        for s in prev_submissions:
                            s.status = 'rejected'
                            SolutionApproval.query.filter_by(submission_id=s.id).delete()
                        # create a new text solution submission
                        ss = SolutionSubmission.create(text_solution_submitted_by_type, text_solution_submitted_by_id,
                                                       question.id, 'text', args['text_solution'], status='accepted')
                    else:
                        # get the text solution submission for this question which has neither been accepted nor rejected
                        ss = SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id,
                                                             SolutionSubmission.solution_type == 'text',
                                                             SolutionSubmission.status == None).first()

                    # create category submission approval
                    SolutionApproval.create(ss.id, kwargs['user_type'].id, kwargs['user'].id)

                # edited from anywhere except proof_read_categorization
                else:
                    # if text solution changed
                    if QuestionModel.parse_content(args['text_solution']) != question.text_solution:
                        # delete any previous text solution submission and its corresponding approvals
                        SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id, SolutionSubmission.solution_type == 'text').delete()
                        # create a new text solution submission
                        SolutionSubmission.create(text_solution_submitted_by_type, text_solution_submitted_by_id, question.id, 'text', args['text_solution'])

                        # if text solution was already proof read , then reset proof_read_text_solution
                        status['proof_read_text_solution'] = '1'
                        print 'Here here here here!!!'
                        #if status['proof_read_text_solution'] == '1':
                        #    status['proof_read_text_solution'] = '0'

        # if no text solution submitted
        else:
            status['text_solution_added'] = '0'
            status['proof_read_text_solution'] = '0'
            status['finalized'] = '0'
            # delete any previous text solution submission and its corresponding approvals
            SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id, SolutionSubmission.solution_type == 'text').delete()

        video_solution_submitted_by_type, video_solution_submitted_by_id, video_solution_added_by_type, video_solution_added_by_id = [None]*4

        # if video solution is submitted
        if args['video_solution_url'] is not None:
            video_solution_submitted_by_type = args['video_solution_by']['type']
            video_solution_submitted_by_id = args['video_solution_by']['id']
            video_solution_added_by_type = kwargs['user_type'].id
            video_solution_added_by_id = kwargs['user'].id

            # question had no video solution
            if status['video_solution_added'] == '0':
                status['video_solution_added'] = '1'
                # delete any previous video solution submission and its corresponding approvals
                #SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id, SolutionSubmission.solution_type == 'video').delete()
                # create a new solution submission
                SolutionSubmission.create(video_solution_submitted_by_type, video_solution_submitted_by_id, question.id, 'video', args['video_solution_url'])

            # question had video solution
            else:
                # if came from proof_read_video_solution
                if args['proof_read_video_solution']:
                    status['video_solution_added'] = '1'
                    status['proof_read_video_solution'] = '1'
                    # if video solution changed
                    if args['video_solution_url'] != question.video_solution_url:
                        # reject any previous accepted text solution submissions and delete their corresponding approvals
                        prev_submissions = SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id,
                                                                           SolutionSubmission.solution_type == 'video',
                                                                           SolutionSubmission.status == 'accepted').all()
                        for s in prev_submissions:
                            s.status = 'rejected'
                            SolutionApproval.query.filter_by(submission_id=s.id).delete()
                        # create a new text solution submission
                        ss = SolutionSubmission.create(video_solution_submitted_by_type, video_solution_submitted_by_id,
                                                       question.id, 'video', args['video_solution_url'], status='accepted')
                    else:
                        # get the video solution submission for this question which has neither been accepted nor rejected
                        ss = SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id,
                                                             SolutionSubmission.solution_type == 'video',
                                                             SolutionSubmission.status == None).first()
                    # create category submission approval
                    SolutionApproval.create(ss.id, kwargs['user_type'].id, kwargs['user'].id)

                # edited from anywhere except proof_read_categorization
                else:
                    # if video solution changed
                    if args['video_solution_url'] != question.video_solution_url:
                        # delete any previous video solution submission and its corresponding approvals
                        SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id, SolutionSubmission.solution_type == 'video').delete()
                        # create a new video solution submission
                        SolutionSubmission.create(video_solution_submitted_by_type, video_solution_submitted_by_id, question.id, 'video', args['video_solution_url'])

                        # if text solution was already proof read , then reset proof_read_text_solution
                        if status['proof_read_video_solution'] == '1':
                            status['proof_read_video_solution'] = '0'

        # if no video solution submitted
        else:
            status['video_solution_added'] = '0'
            status['video_read_text_solution'] = '0'
            status['finalized'] = '0'
            # delete any previous video solution submission and its corresponding approvals
            SolutionSubmission.query.filter(SolutionSubmission.question_id == question.id, SolutionSubmission.solution_type == 'video').delete()

        if args['error_reported'] is not None:
            status['error_reported'] = args['error_reported']

        if '0' not in (status['proof_read_categorization'], status['proof_read_text_solution'], status['proof_read_video_solution'], status['error_reported']):
            # question has been proof read in all 3 respects so its finalized
            status['finalized'] = '1'

        question.update(args['content'], status, comprehension_id=comprehension_id, ontology_id=args['ontology_id'],
                        average_time=args['average_time'], nature=args['nature'], type=args['type'], difficulty=args['difficulty'],
                        text_solution=args['text_solution'], video_solution_url=args['video_solution_url'],
                        text_solution_by_type=text_solution_added_by_type, text_solution_by_id=text_solution_added_by_id,
                        video_solution_by_type=video_solution_added_by_type, video_solution_by_id=video_solution_added_by_id,
                        **args['options'])

        if args['error_reported'] is not None and args['error_reported'] == '0':
            report = ReportedQuestion.query.filter(ReportedQuestion.question_id == question.id, ReportedQuestion.is_resolved == False).first()
            report.is_resolved = True
            report.resolved_by_type = kwargs['user_type'].id
            report.resolved_by_id = kwargs['user'].id
            report.resolved_at = datetime.datetime.utcnow()

        db.session.commit()
        return {'question': question, 'error': False}


from exam_app.resources.question_list import options_json_type, user_json_type
from exam_app.models.question import Question as QuestionModel
from exam_app.models.comprehension import Comprehension
from exam_app.models.ontology import Ontology
from exam_app.models.category_submission import CategorySubmission
from exam_app.models.category_approval import CategoryApproval
from exam_app.models.solution_submission import SolutionSubmission
from exam_app.models.solution_approval import SolutionApproval
from exam_app.models.reported_question import ReportedQuestion
from exam_app import db
