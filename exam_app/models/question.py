# -*- coding: utf-8 -*-

import datetime
import re
import urlparse
from collections import OrderedDict

from sqlalchemy.dialects.postgresql import ARRAY, HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import not_, or_
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import validates

from exam_app.models import db
from exam_app import app
from exam_app.exceptions import InvalidOntologyNodeId, InvalidQuestionId, UnAcceptableVideoUrl
from exam_app.helpers import S3, parse_base64_string


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(MutableDict.as_mutable(HSTORE), default={})          # contains flags with values 0 and 1
    comprehension_id = db.Column(db.Integer, db.ForeignKey('comprehensions.id', ondelete='CASCADE'))
    all_options = db.Column(ARRAY(db.Text), default=[])
    correct_options = db.Column(ARRAY(db.Integer), default=[])
    option_reasons = db.Column(ARRAY(db.Text), default=[])
    average_time = db.Column(db.Integer)
    ontology = db.Column(ARRAY(db.Integer))
    nature = db.Column(db.Enum(*app.config['QUESTION_NATURE'].keys(), name='question_nature_enum'))
    difficulty = db.Column(db.Enum(*app.config['QUESTION_DIFFICULTY_LEVEL'], name='question_difficulty_enum'))
    type = db.Column(db.Enum(*app.config['QUESTION_TYPE'], name='question_type_enum'))
    text_solution = db.Column(db.Text)          # null until approved
    video_solution_url = db.Column(db.String(app.config['URL_MAX_LENGTH']))     # null until approved
    text_solution_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    text_solution_by_id = db.Column(db.Integer)
    video_solution_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    video_solution_by_id = db.Column(db.Integer)
    similar_question_ids = db.Column(ARRAY(db.Integer))      # null if unfilled
    created_by_type = db.Column(db.Integer, db.ForeignKey('user_types.id'))
    created_by_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_similarity_marked = db.Column(db.Boolean, default=False)

    @validates('video_solution_url')
    def validate_video_url(self, key, url):
        if url is None:
            return url
        parsed_url = urlparse.urlparse(url)
        netloc = parsed_url.netloc
        if netloc not in ('youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be'):
            raise UnAcceptableVideoUrl
        return url

    img_base64_pat = re.compile('<img [^>]*?src="(data:image.*?)".*?>')

    @classmethod
    def parse_content(cls, content):
        """
        Parse and return the content. Convert base64 images to s3 image urls.

        :param content:
        :return: string
        """
        match = cls.img_base64_pat.search(content)
        s3obj = S3()
        while match is not None:
            mimetype, image_data = parse_base64_string(match.groups()[0])
            url = s3obj.upload(image_data, mimetype)
            img_tag = '<img src="%s" />' % url
            content = content[:match.start()] + img_tag + content[match.end():]
            match = cls.img_base64_pat.search(content)

        return content


    @classmethod
    def create(cls, content, status, comprehension_id=None, all_options=None, correct_options=None, option_reasons=None,
               ontology_id=None, average_time=app.config['DEFAULT_AVERAGE_TIME'], nature=None, difficulty=None, type=None,
               text_solution=None, video_solution_url=None, text_solution_by_type=None, text_solution_by_id=None,
               video_solution_by_type=None, video_solution_by_id=None, similar_question_ids=None, created_by_type=None,
               created_by_id=None):
        """
        Create a new question and return the newly created object.

        :param content: question test
        :param status: status dict
        :param comprehension_id: if question is part of comprehension
        :param all_options:
        :param correct_options: indices of correct options
        :param option_reasons:
        :param ontology_id:
        :param average_time:
        :param nature:
        :param difficulty:
        :param type:
        :param text_solution:
        :param video_solution_url:
        :param text_solution_by_type: the type of user if text solution was provided
        :param text_solution_by_id:   the id of user if text solution was provided
        :param video_solution_by_type: the type of user if video solution was provided
        :param video_solution_by_id:    the id of user if video solution was provided
        :param similar_question_ids:    array of question ids
        :param created_by_type:     the type of user who entered this question
        :param created_by_id:       the id of user who entered this question
        :return:
        """
        if ontology_id is not None:
            ontology_obj = Ontology.query.get(ontology_id)
            if ontology_obj is None:
                raise InvalidOntologyNodeId
            ontology = ontology_obj.absolute_path
        else:
            ontology = None

        content = content.strip()
        content = cls.parse_content(content)

        if all_options is not None:
            for i, option in enumerate(all_options):
                if option is not None:
                    all_options[i] = cls.parse_content(option)

        if option_reasons is not None:
            for i, reason in enumerate(option_reasons):
                if reason is not None:
                    option_reasons[i] = cls.parse_content(reason)

        if text_solution is not None:
            text_solution = cls.parse_content(text_solution)

        question = cls(content=content, status=status, comprehension_id=comprehension_id, all_options=all_options,
                       correct_options=correct_options, option_reasons=option_reasons, ontology=ontology,
                       average_time=average_time, nature=nature, difficulty=difficulty, type=type, text_solution=text_solution,
                       video_solution_url=video_solution_url, text_solution_by_type=text_solution_by_type,
                       text_solution_by_id=text_solution_by_id, video_solution_by_type=video_solution_by_type,
                       video_solution_by_id=video_solution_by_id, similar_question_ids=similar_question_ids, created_by_type=created_by_type,
                       created_by_id=created_by_id)
        db.session.add(question)
        db.session.commit()
        return question

    @classmethod
    def get(cls, id):
        """
        Get details of a single question

        :param id: question id
        :return: question object
        """
        question = cls.query.get(id)
        if question is not None:
            if question.text_solution is not None or question.video_solution_url is not None:
                ss = SolutionSubmission.query.filter_by(question_id=question.id).all()
                for item in ss:
                    if item.solution_type == 'video':
                        video_submission = item
                    if item.solution_type == 'text':
                        text_submission = item
                if question.text_solution is not None:
                    question.text_solution_by_type = text_submission.submitted_by_type
                    question.text_solution_by_id = text_submission.submitted_by_id
                if question.video_solution_url is not None:
                    question.video_solution_by_type = video_submission.submitted_by_type
                    question.video_solution_by_id = video_submission.submitted_by_id
            return question
        else:
            raise InvalidQuestionId

    def update(self, content, status, comprehension_id=None, all_options=None, correct_options=None, option_reasons=None,
               ontology_id=None, average_time=app.config['DEFAULT_AVERAGE_TIME'], nature=None, difficulty=None, type=None,
               text_solution=None, video_solution_url=None, text_solution_by_type=None, text_solution_by_id=None,
               video_solution_by_type=None, video_solution_by_id=None, similar_question_ids=None):
        """
        Update the details of single question

        :param id: question_id
        :param content:
        :param status: status dict
        :param comprehension_id: if question is part of comprehension
        :param all_options:
        :param correct_options: indices of correct options
        :param option_reasons:
        :param ontology_id:
        :param average_time:
        :param nature:
        :param difficulty:
        :param type:
        :param text_solution:
        :param video_solution_url:
        :param text_solution_by_type: the type of user if text solution was provided
        :param text_solution_by_id:   the id of user if text solution was provided
        :param video_solution_by_type: the type of user if video solution was provided
        :param video_solution_by_id:    the id of user if video solution was provided
        :param similar_question_ids:    array of question ids
        :return:
        """
        if ontology_id is not None:
            ontology_obj = Ontology.query.get(ontology_id)
            if ontology_obj is None:
                raise InvalidOntologyNodeId
            ontology = ontology_obj.absolute_path
        else:
            ontology = None

        content = self.__class__.parse_content(content)

        if all_options is not None:
            for i, option in enumerate(all_options):
                if option is not None:
                    all_options[i] = self.__class__.parse_content(option)

        if option_reasons is not None:
            for i, reason in enumerate(option_reasons):
                if reason is not None:
                    option_reasons[i] = self.__class__.parse_content(reason)

        if text_solution is not None:
            text_solution = self.__class__.parse_content(text_solution)

        question = self
        question.content = content
        question.status = status
        question.comprehension_id = comprehension_id
        question.all_options = all_options
        question.correct_options = correct_options
        question.option_reasons = option_reasons
        question.ontology = ontology
        question.average_time = average_time
        question.nature = nature
        question.difficulty = difficulty
        question.type = type
        question.text_solution = text_solution
        question.video_solution_url = video_solution_url
        question.text_solution_by_type = text_solution_by_type
        question.text_solution_by_id = text_solution_by_id
        question.video_solution_by_type = video_solution_by_type
        question.video_solution_by_id = video_solution_by_id
        question.similar_question_ids = similar_question_ids
        db.session.commit()
        return question

    @classmethod
    def get_filtertered_list(cls, nature=None, type=None, difficulty=None, average_time=None, categorized=None,
                         proof_read_categorization=None, proof_read_text_solution=None, proof_read_video_solution=None,
                        finalized=None, error_reported=None, text_solution_added=None, video_solution_added=None,
                         ontology=None, is_comprehension=None, similar_questions_to=None, not_similar_questions_to=None,
                         exclude_question_ids=None, include_question_ids=None, page=1, limit=None):
        """
        Get a list of question after applying filters

        :param nature:
        :param type:
        :param difficulty:
        :param average_time:
        :param categorized:
        :param proof_read_categorization:
        :param proof_read_text_solution:
        :param proof_read_video_solution:
        :param finalized:
        :param text_solution_added:
        :param video_solution_added:
        :param ontology:
        :param is_comprehension:
        :param similar_questions_to: questions which are similar to the question id
        :param not_similar_questions_to: questions which are not similar to the question id
        :param exclude_question_ids: dont return questions with these ids
        :param include_question_ids: return questions with these ids
        :param page:
        :param limit:
        :return:
        """
        
        exprs = []

        if nature is not None:
            exprs.append(Question.nature == nature)

        if type is not None:
            exprs.append(Question.type == type)

        if difficulty is not None:
            exprs.append(Question.difficulty == difficulty)

        if average_time is not None:
            exprs.append(Question.average_time == average_time)

        if categorized is not None:
            exprs.append(Question.status['categorized'] == categorized)

        if proof_read_categorization is not None:
            exprs.append(Question.status['proof_read_categorization'] == proof_read_categorization)

        if proof_read_text_solution is not None:
            exprs.append(Question.status['proof_read_text_solution'] == proof_read_text_solution)

        if proof_read_video_solution is not None:
            exprs.append(Question.status['proof_read_video_solution'] == proof_read_video_solution)

        if finalized is not None:
            exprs.append(Question.status['finalized'] == finalized)
        
        if error_reported is not None:
            exprs.append(Question.status['error_reported'] == error_reported)

        if ontology is not None:
            exprs.append(Question.ontology.contains(ontology))

        if is_comprehension is not None:
            if is_comprehension == 0:
                exprs.append(Question.comprehension_id == None)
            else:
                exprs.append(Question.comprehension_id != None)

        if text_solution_added is not None:
            exprs.append(Question.status['text_solution_added'] == str(text_solution_added))

        if video_solution_added is not None:
            exprs.append(Question.status['video_solution_added'] == str(video_solution_added))

        if exclude_question_ids is not None:
            exprs.append(not_(Question.id.in_(exclude_question_ids)))

        if include_question_ids is not None:
            exprs.append(Question.id.in_(include_question_ids))

        if similar_questions_to is not None or not_similar_questions_to is not None:
            # Need to select only categorized questions
            categorized_expr = Question.status['categorized'] == '1'
            if categorized_expr not in exprs:
                exprs.append(categorized_expr)

            if similar_questions_to is not None:
                # questions need to be compared only when ontology matches exactly
                ques = cls.get(similar_questions_to)
                exprs.append(Question.ontology == ques.ontology)
                # exclude itself
                exprs.append(Question.id != ques.id)
                exprs.append(Question.similar_question_ids.any(similar_questions_to))

            if not_similar_questions_to is not None:
                # questions need to be compared only when ontology matches exactly
                ques = cls.get(not_similar_questions_to)
                exprs.append(Question.ontology == ques.ontology)
                # exclude itself
                exprs.append(Question.id != ques.id)
                exprs.append(or_(not_(Question.similar_question_ids.any(not_similar_questions_to)), Question.similar_question_ids == None))
        if limit is not None:
            questions_pag_obj = Question.query.filter(*exprs).order_by(Question.created_at.desc()).paginate(page, limit)
            questions = questions_pag_obj.items
            total = questions_pag_obj.total
        else:
            q = Question.query.filter(*exprs).order_by(Question.created_at.desc())
            questions = q.all()
            total = len(questions)

        question_dict = OrderedDict()
        for q in questions:
            question_dict[q.id] = q

        submissions = SolutionSubmission.query.filter(SolutionSubmission.question_id.in_(question_dict.keys())).all()
        for item in submissions:
            question = question_dict[item.question_id]
            if item.solution_type == 'text' and question.text_solution is not None:
                question.text_solution_by_type = item.submitted_by_type
                question.text_solution_by_id = item.submitted_by_id
            if item.solution_type == 'video' and question.video_solution_url is not None:
                question.video_solution_by_type = item.submitted_by_type
                question.video_solution_by_id = item.submitted_by_id

        return {
            'questions': question_dict.values(),
            'total': total
        }

    @classmethod
    def reset_categorization(cls, id):
        """
        Reset the categorization flag and categorization fields

        :param id:
        :return:
        """
        question = cls.query.get(id)
        question.status['categorized'] = '0'
        question.status['proof_read_categorization'] = '0'
        question.status['finalized'] = '0'
        if question.ontology is not None:
            question.ontology = question.ontology[0:1]
        question.average_time = None
        question.nature = None
        question.difficulty = None
        question.type = None
        db.session.commit()
        return question

    @classmethod
    def approve_categorization(cls, id):
        """
        Approve the categorization. Set the categorization flag and proof read categorization flag

        :param id:
        :return:
        """
        question = cls.query.get(id)
        question.status['categorized'] = '1'
        question.status['proof_read_categorization'] = '1'
        if '0' not in (question.status['proof_read_categorization'], question.status['proof_read_text_solution'], question.status['proof_read_video_solution']):
            # question has been proof read in all 3 respects so its finalized
            question.status['finalized'] = '1'
        db.session.commit()
        return question

    @classmethod
    def reset_solution(cls, id, sol_type):
        """
        Reset the solution flags and solution field

        :param id:
        :param sol_type: Solution type. Can be text or video
        :return:
        """
        question = cls.query.get(id)
        if sol_type == 'text':
            question.status['text_solution_added'] = '0'
            question.status['proof_read_text_solution'] = '0'
            question.text_solution = None
            question.text_solution_by_type = None
            question.text_solution_by_id = None

        if sol_type == 'video':
            question.status['video_solution_added'] = '0'
            question.status['proof_read_video_solution'] = '0'
            question.video_solution_url = None
            question.video_solution_by_type = None
            question.video_solution_by_id = None

        question.status['finalized'] = '0'
        db.session.commit()
        return question

    @classmethod
    def approve_solution(cls, id, sol_type):
        """
        Approve the solution. Set the solution flag and proof read solution flag

        :param id:
        :param sol_type: Solution type. Can be text or video
        :return:
        """
        question = cls.query.get(id)
        if sol_type == 'text':
            question.status['text_solution_added'] = '1'
            question.status['proof_read_text_solution'] = '1'

        if sol_type == 'video':
            question.status['video_solution_added'] = '1'
            question.status['proof_read_video_solution'] = '1'

        if '0' not in (question.status['proof_read_categorization'], question.status['proof_read_text_solution'], question.status['proof_read_video_solution']):
            # question has been proof read in all 3 respects so its finalized
            question.status['finalized'] = '1'
        db.session.commit()
        return question

from exam_app.models.comprehension import Comprehension
from exam_app.models.users import UserTypes
from exam_app.models.ontology import Ontology
from exam_app.models.solution_submission import SolutionSubmission
