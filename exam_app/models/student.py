# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from exam_app import app
from exam_app.models import db
from exam_app.models.users import User
from exam_app.exceptions import EmailAlreadyRegistered, MobileNoAlreadyRegistered, InvalidStudentId


class Student(User, db.Model):
    __tablename__ = 'students'
    type = db.Column(db.Integer, db.ForeignKey('user_types.id'), nullable=False)
    mobile_no = db.Column(db.String(app.config['MOBILE_NO_MAX_LENGTH']), unique=True)
    city = db.Column(db.String(100))
    area = db.Column(db.String(100))
    pin = db.Column(db.String(10))
    school = db.Column(db.String(100))
    ntse_score = db.Column(db.Float)
    roll_no = db.Column(db.String(20))
    branches = db.Column(ARRAY(db.String(1)))
    target_exams = db.Column(ARRAY(db.String(1)))
    target_exam_roll_nos = db.Column(ARRAY(db.String(100)))
    target_year = db.Column(db.Integer)
    father_name = db.Column(db.String(app.config['NAME_MAX_LENGTH']))
    father_mobile_no = db.Column(db.String(app.config['MOBILE_NO_MAX_LENGTH']))
    father_email = db.Column(db.String(app.config['EMAIL_MAX_LENGTH']))
    payment_plan_id = db.Column(db.Integer, db.ForeignKey('payment_plans.id'))
    registered_from = db.Column(db.Enum('institute', 'independent', name='registered_from_enum'))
    fp_token = db.Column(db.String(64))
    refcode = db.Column(db.String(200), nullable=True)

    @classmethod
    def create(cls, name, email, password, mobile_no=None, city=None, area=None, pin=None, school=None, ntse_score=None,
               roll_no=None, branches=None, target_exams=None, target_exam_roll_nos=None, target_year=None, father_name=None,
               father_mobile_no=None, father_email=None, payment_plan_id=None, registered_from=None, refcode=None):
        """

        :param name:
        :param email:
        :param password:
        :param mobile_no:
        :param city:
        :param area:
        :param pin:
        :param school:
        :param ntse_score:
        :param roll_no:
        :param branches:
        :param target_exams:
        :param target_exam_roll_nos:
        :param target_year:
        :param father_name:
        :param father_email:
        :param father_mobile_no:
        :param payment_plan_id:
        :param registered_from:
        :return:
        """
        user_type = UserTypes.query.filter_by(name='student').first()
        student = cls(name=name, email=email, password=password, mobile_no=mobile_no, city=city, area=area, pin=pin,
                      school=school, ntse_score=ntse_score, roll_no=roll_no, branches=branches, target_exams=target_exams,
                      target_exam_roll_nos=target_exam_roll_nos, target_year=target_year, father_name=father_name,
                      father_mobile_no=father_mobile_no, payment_plan_id=payment_plan_id, registered_from=registered_from,
                      type=user_type.id, refcode=refcode)
        db.session.add(student)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            if 'email' in e.message:
                raise EmailAlreadyRegistered
            if 'mobile_no' in e.message:
                raise MobileNoAlreadyRegistered
            raise e
        return student

    @classmethod
    def get(cls, id):
        """
        Get details of a single student

        :param id: student id
        :return: student object
        """
        student = cls.query.get(id)
        if student is not None:
            return student
        else:
            raise InvalidStudentId

    @classmethod
    def get_list(cls, page=1, limit=10):
        """
        Get a list of students

        :param page:
        :param limit:
        :return:
        """
        students_pag_obj = cls.query.filter_by(is_active=True).paginate(page, limit)
        students = students_pag_obj.items
        total = students_pag_obj.total

        return students, total

    @classmethod
    def get_attempted_mock_tests(cls, id):
        """

        :param id:
        :return:
        """
        attempted_mock_tests = AttemptedMockTest.query.filter_by(student_id=id).all()
        return attempted_mock_tests

    @classmethod
    def get_pushed_mock_tests(cls, id):
        """

        :param id:
        :return:
        """
        # get batches that the student is currently part of
        student_current_batches = StudentBatches.query.filter(StudentBatches.student_id == id, StudentBatches.left_at == None).all()
        if len(student_current_batches) > 0:
            # get mock tests that are pushed to batches that the student is currently part of and have not expired
            batch_ids = [sb.batch_id for sb in student_current_batches]

            pushed_mock_tests = PushedMockTest.query.filter(PushedMockTest.batch_id.in_(batch_ids),
                                                        or_(PushedMockTest.expires_at == None, PushedMockTest.expires_at > datetime.datetime.utcnow())).all()
        else:
            pushed_mock_tests = []

        return pushed_mock_tests


from exam_app.models.payment_plan import PaymentPlan
from exam_app.models.users import UserTypes
from exam_app.models.attempted_mock_test import AttemptedMockTest
from exam_app.models.student_batches import StudentBatches
from exam_app.models.pushed_mock_test import PushedMockTest
