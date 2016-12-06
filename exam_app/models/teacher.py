#-*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from exam_app import app
from exam_app.models import db
from exam_app.models.users import User, UserTypes
from exam_app.exceptions import EmailAlreadyRegistered, InvalidTeacherId
from exam_app.models.category_submission import CategorySubmission
from exam_app.models.category_approval import CategoryApproval
from exam_app.models.solution_submission import SolutionSubmission
from exam_app.models.solution_approval import SolutionApproval
from exam_app.models.reported_question import ReportedQuestion


class Teacher(User, db.Model):
    __tablename__ = 'teachers'
    type = db.Column(db.Integer, db.ForeignKey('user_types.id'), nullable=False)
    subject_expert = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    qualification = db.Column(db.String(100))

    @classmethod
    def create(cls, name, email, password, subject_expert=None, specialization=None, qualification=None):
        """
        Create a new teacher. If need encrypted password, then provide one. No encryption is done in this function.

        :param name:
        :param email:
        :param password:
        :param subject_expert:
        :param specialization:
        :param qualification:
        :return:
        """
        user_type = UserTypes.query.filter_by(name='teacher').first()
        teacher = cls(name=name, email=email, password=password, subject_expert=subject_expert, specialization=specialization,
                      qualification=qualification, type=user_type.id)
        db.session.add(teacher)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise EmailAlreadyRegistered
        return teacher

    @classmethod
    def get_list(cls, page=1, limit=10):
        """
        Get a list of active teacher with their stats

        :param page:
        :param limit:
        :return:
        """
        result = {}

        pag_obj = cls.query.filter_by(is_active=True).paginate(page, limit)
        teachers = pag_obj.items
        total = pag_obj.total
        if total == 0:
            return [], 0

        for op in teachers:
            result[op.id] = {'teacher': op}
        teacher_type = teachers[0].type
        teacher_ids = result.keys()

        reported_resolved_count = db.session.query(ReportedQuestion.resolved_by_id, func.count(ReportedQuestion.id)).filter(
            ReportedQuestion.resolved_by_type == teacher_type, ReportedQuestion.resolved_by_id.in_(teacher_ids),
            ReportedQuestion.is_resolved == True).group_by(ReportedQuestion.resolved_by_id)
        for id, count in reported_resolved_count:
            result[id]['reported_resolved'] = count

        cat_sub_counts = db.session.query(CategorySubmission.submitted_by_id, func.count(CategorySubmission.id)).filter(
            CategorySubmission.submitted_by_type == teacher_type, CategorySubmission.submitted_by_id.in_(teacher_ids))\
            .group_by(CategorySubmission.submitted_by_id)
        for id, count in cat_sub_counts:
            result[id]['questions_categorized'] = count

        cat_app_counts = db.session.query(CategoryApproval.approved_by_id, func.count(CategoryApproval.id))\
            .filter(CategoryApproval.approved_by_id.in_(teacher_ids), CategoryApproval.approved_by_type == teacher_type).group_by(CategoryApproval.approved_by_id)
        for id, count in cat_app_counts:
            result[id]['questions_approved'] = count

        sol_counts = db.session.query(SolutionSubmission.submitted_by_id, SolutionSubmission.solution_type, func.count(SolutionSubmission.id))\
            .filter(SolutionSubmission.submitted_by_type == teacher_type, SolutionSubmission.submitted_by_id.in_(teacher_ids))\
            .group_by(SolutionSubmission.submitted_by_id, SolutionSubmission.solution_type)
        for id, sol_type, count in sol_counts:
            if sol_type == 'text':
                result[id]['text_solutions_submitted'] = count
            if sol_type == 'video':
                result[id]['video_solutions_submitted'] = count

        sol_app_counts = db.session.query(SolutionApproval.approved_by_id, SolutionSubmission.solution_type, func.count(SolutionApproval.id))\
            .filter(SolutionApproval.approved_by_type == teacher_type, SolutionApproval.approved_by_id.in_(teacher_ids),
                    SolutionApproval.submission_id == SolutionSubmission.id).group_by(SolutionApproval.approved_by_id,
                                                                                      SolutionSubmission.solution_type)

        for id, sol_type, count in sol_app_counts:
            if sol_type == 'text':
                result[id]['text_solutions_approved'] = count
            if sol_type == 'video':
                result[id]['video_solutions_approved'] = count

        return result.values(), total

    @classmethod
    def get(cls, id):
        """
        Get a single teacher with his stats

        :param id:
        :return:
        """

        teacher = cls.query.get(id)
        if teacher is None:
            raise InvalidTeacherId

        reported_resolved = db.session.query(func.count(ReportedQuestion.id)).filter(
            ReportedQuestion.is_resolved == True, ReportedQuestion.resolved_by_type == teacher.type, ReportedQuestion.resolved_by_id == teacher.id).first()[0]

        cat_sub_count = db.session.query(func.count(CategorySubmission.id)).filter(
            CategorySubmission.submitted_by_type == teacher.type, CategorySubmission.submitted_by_id == teacher.id).first()[0]

        cat_app_count = db.session.query(func.count(CategoryApproval.id))\
            .filter(CategorySubmission.submitted_by_type == teacher.type, CategorySubmission.submitted_by_id == teacher.id, CategoryApproval.submission_id == CategorySubmission.id).first()[0]

        sol_counts = db.session.query(SolutionSubmission.solution_type, func.count(SolutionSubmission.id))\
            .filter(SolutionSubmission.submitted_by_type == teacher.type, SolutionSubmission.submitted_by_id == teacher.id)\
            .group_by(SolutionSubmission.solution_type)

        text_solutions_submitted = 0
        video_solutions_submitted = 0
        for sol_type, count in sol_counts:
            if sol_type == 'text':
                text_solutions_submitted = count
            if sol_type == 'video':
                video_solutions_submitted = count

        sol_app_counts = db.session.query(SolutionSubmission.solution_type, func.count(SolutionApproval.id))\
            .filter(CategorySubmission.submitted_by_type == teacher.type, CategorySubmission.submitted_by_id == teacher.id, SolutionApproval.submission_id == SolutionSubmission.id)\
            .group_by(SolutionSubmission.solution_type)

        text_solutions_approved = 0
        video_solutions_approved = 0
        for sol_type, count in sol_app_counts:
            if sol_type == 'text':
                text_solutions_approved = count
            if sol_type == 'video':
                video_solutions_approved = count

        return {
            'teacher': teacher,
            'questions_categorized': cat_sub_count,
            'questions_approved': cat_app_count,
            'text_solutions_submitted': text_solutions_submitted,
            'video_solutions_submitted': video_solutions_submitted,
            'text_solutions_approved': text_solutions_approved,
            'video_solutions_approved': video_solutions_approved,
            'reported_resolved': reported_resolved
        }



