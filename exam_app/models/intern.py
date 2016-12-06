#-*- coding: utf-8 -*-

from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

from exam_app.models import db
from exam_app.models.users import User
from exam_app.models.category_submission import CategorySubmission
from exam_app.models.category_approval import CategoryApproval
from exam_app.models.solution_submission import SolutionSubmission
from exam_app.models.solution_approval import SolutionApproval
from exam_app.models.reported_question import ReportedQuestion
from exam_app.exceptions import EmailAlreadyRegistered, InvalidInternId


class Intern(User, db.Model):
    __tablename__ = 'interns'
    type = db.Column(db.Integer, db.ForeignKey('user_types.id'), nullable=False)

    @classmethod
    def get_list(cls, page=1, limit=10):
        """
        Get a list of active interns with their stats

        :param page:
        :param limit:
        :return:
        """
        result = {}

        pag_obj = cls.query.filter_by(is_active=True).paginate(page, limit)
        interns = pag_obj.items
        total = pag_obj.total
        if total == 0:
            return [], 0

        for intern in interns:
            result[intern.id] = {'intern': intern}
        intern_type = interns[0].type
        intern_ids = result.keys()

        reported_count = db.session.query(ReportedQuestion.reported_by_id, func.count(ReportedQuestion.id)).filter(
            ReportedQuestion.reported_by_type == intern_type, ReportedQuestion.reported_by_id.in_(intern_ids))\
            .group_by(ReportedQuestion.reported_by_id)
        for id, count in reported_count:
            result[id]['reported_questions'] = count

        cat_sub_counts = db.session.query(CategorySubmission.submitted_by_id, func.count(CategorySubmission.id)).filter(
            CategorySubmission.submitted_by_type == intern_type, CategorySubmission.submitted_by_id.in_(intern_ids))\
            .group_by(CategorySubmission.submitted_by_id)
        for id, count in cat_sub_counts:
            result[id]['questions_categorized'] = count

        cat_app_counts = db.session.query(CategorySubmission.submitted_by_id, func.count(CategoryApproval.id))\
            .filter(CategorySubmission.submitted_by_type == intern_type, CategorySubmission.submitted_by_id
                    .in_(intern_ids), CategoryApproval.submission_id == CategorySubmission.id).group_by(CategorySubmission.submitted_by_id)
        for id, count in cat_app_counts:
            result[id]['questions_approved'] = count

        sol_counts = db.session.query(SolutionSubmission.submitted_by_id, SolutionSubmission.solution_type, func.count(SolutionSubmission.id))\
            .filter(SolutionSubmission.submitted_by_type == intern_type, SolutionSubmission.submitted_by_id.in_(intern_ids))\
            .group_by(SolutionSubmission.submitted_by_id, SolutionSubmission.solution_type)
        for id, sol_type, count in sol_counts:
            if sol_type == 'text':
                result[id]['text_solutions_submitted'] = count
            if sol_type == 'video':
                result[id]['video_solutions_submitted'] = count

        sol_app_counts = db.session.query(SolutionSubmission.submitted_by_id, SolutionSubmission.solution_type, func.count(SolutionApproval.id))\
            .filter(SolutionSubmission.submitted_by_type == intern_type, SolutionSubmission.submitted_by_id.in_(intern_ids), SolutionApproval.submission_id == SolutionSubmission.id)\
            .group_by(SolutionSubmission.submitted_by_id, SolutionSubmission.solution_type)

        for id, sol_type, count in sol_app_counts:
            if sol_type == 'text':
                result[id]['text_solutions_approved'] = count
            if sol_type == 'video':
                result[id]['video_solutions_approved'] = count

        return result.values(), total

    @classmethod
    def create(cls, name, email, password):
        """
        Create an intern. If need encrypted password, then provide one. No encryption is done in this function.

        :param name:
        :param email:
        :param password: encrypted/unencrypted password
        :return:
        """
        user_type = UserTypes.query.filter_by(name='intern').first()
        intern = cls(name=name, email=email, password=password, type=user_type.id)
        db.session.add(intern)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rolback()
            raise EmailAlreadyRegistered

        return intern

    @classmethod
    def get(cls, id):
        """
        Get a single teacher with his stats

        :param id:
        :return:
        """

        intern = cls.query.get(id)
        if intern is None:
            raise InvalidInternId

        reported_count = db.session.query(func.count(ReportedQuestion.id)).filter(
            ReportedQuestion.reported_by_type == intern.type, ReportedQuestion.reported_by_id == intern.id).first()[0]

        cat_sub_count = db.session.query(func.count(CategorySubmission.id)).filter(
            CategorySubmission.submitted_by_type == intern.type, CategorySubmission.submitted_by_id == intern.id).first()[0]

        cat_app_count = db.session.query(func.count(CategoryApproval.id))\
            .filter(CategorySubmission.submitted_by_type == intern.type, CategorySubmission.submitted_by_id == intern.id, CategoryApproval.submission_id == CategorySubmission.id).first()[0]

        sol_counts = db.session.query(SolutionSubmission.solution_type, func.count(SolutionSubmission.id))\
            .filter(SolutionSubmission.submitted_by_type == intern.type, SolutionSubmission.submitted_by_id == intern.id)\
            .group_by(SolutionSubmission.solution_type)

        text_solutions_submitted = 0
        video_solutions_submitted = 0
        for sol_type, count in sol_counts:
            if sol_type == 'text':
                text_solutions_submitted = count
            if sol_type == 'video':
                video_solutions_submitted = count

        sol_app_counts = db.session.query(SolutionSubmission.solution_type, func.count(SolutionApproval.id))\
            .filter(CategorySubmission.submitted_by_type == intern.type, CategorySubmission.submitted_by_id == intern.id, SolutionApproval.submission_id == SolutionSubmission.id)\
            .group_by(SolutionSubmission.solution_type)

        text_solutions_approved = 0
        video_solutions_approved = 0
        for sol_type, count in sol_app_counts:
            if sol_type == 'text':
                text_solutions_approved = count
            if sol_type == 'video':
                video_solutions_approved = count

        return {
            'intern': intern,
            'reported_questions': reported_count,
            'questions_categorized': cat_sub_count,
            'questions_approved': cat_app_count,
            'text_solutions_submitted': text_solutions_submitted,
            'video_solutions_submitted': video_solutions_submitted,
            'text_solutions_approved': text_solutions_approved,
            'video_solutions_approved': video_solutions_approved
        }

from exam_app.models.users import UserTypes
