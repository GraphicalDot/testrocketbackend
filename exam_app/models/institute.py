# -*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError

from exam_app import app
from exam_app.models import db
from exam_app.models.users import User
from exam_app.exceptions import EmailAlreadyRegistered, InvalidInstituteId, MobileNoAlreadyRegistered, UsernameAlreadyRegistered


class Institute(User, db.Model):
    __tablename__ = 'institutes'
    type = db.Column(db.Integer, db.ForeignKey('user_types.id'), nullable=False)
    location = db.Column(db.String(100))
    logo_url = db.Column(db.String(app.config['URL_MAX_LENGTH']))
    username = db.Column(db.String(app.config['USERNAME_MAX_LENGTH']), unique=True)
    mobile_no = db.Column(db.String(app.config['MOBILE_NO_MAX_LENGTH']), unique=True)
    batches = db.relationship('Batch', backref='institute', lazy='dynamic')
    fp_token = db.Column(db.String(64))

    @classmethod
    def authenticate_by_username(cls, username, password):
        """
        Used in institute login

        :param username: chosen username of the institute
        :param password:
        :return: the institute row if authentication successful, none otherwise
        """
        with app.app_context():
            ins = cls.query.filter(cls.username == username, cls.password == password).first()
            return ins

    @classmethod
    def create(cls, name, email, password, username, location=None, mobile_no=None, logo_url=None):
        """
        Create an institute

        :param name:
        :param email:
        :param password:
        :param username:
        :param location:
        :param mobile_no:
        :param logo_url:
        :return:
        """
        user_type = UserTypes.query.filter_by(name='teacher').first()
        institute = cls(name=name, email=email, password=password, username=username, location=location, mobile_no=mobile_no,
                        logo_url=logo_url, type=user_type.id)
        db.session.add(institute)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            if 'email' in e.message:
                raise EmailAlreadyRegistered
            if 'username' in e.message:
                raise UsernameAlreadyRegistered
            if 'mobile_no' in e.message:
                raise MobileNoAlreadyRegistered
            raise e
        return institute

    @classmethod
    def get(cls, id):
        """
        Get details of a single institute

        :param id: institute id
        :return: institute object
        """
        institute = cls.query.get(id)
        if institute is not None:
            return institute
        else:
            raise InvalidInstituteId

    @classmethod
    def get_list(cls, page=1, limit=10):
        """
        Get a list of institutes

        :param page:
        :param limit:
        :return:
        """
        institutes_pag_obj = cls.query.filter_by(is_active=True).paginate(page, limit)
        institutes = institutes_pag_obj.items
        total = institutes_pag_obj.total

        return institutes, total

from exam_app.models.users import UserTypes
