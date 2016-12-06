# -*- coding: utf-8 -*-

import datetime
import re

from sqlalchemy.orm import validates

from exam_app.models import db
from exam_app import app
from exam_app.exceptions import UnAcceptableEmail


email_pattern = re.compile(r'(?P<email>(([^<>()[\]\\.,;:\s@\']+(\.[^<>()[\]\\.,;:\s@\']+)*)|(\'.+\'))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,})))')


class UserTypes(db.Model):
    __tablename__ = 'user_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum('student', 'teacher', 'data_operator', 'intern', 'institutes', name='user_types_enum'))


class User(object):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(app.config['EMAIL_MAX_LENGTH']), unique=True)
    name = db.Column(db.String(app.config['NAME_MAX_LENGTH']))
    password = db.Column(db.String(app.config['PASSWORD_MAX_LENGTH']))
    joined_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_activity = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    @validates('email')
    def validate_email(self, key, email_id):
        m = email_pattern.search(email_id)
        if m is None:
            raise UnAcceptableEmail
        return email_id

    @classmethod
    def authenticate_by_email(cls, email, password):
        """
        Used in login when user explicitly logs in

        :param email:
        :param password:
        :return: the user row if authentication successful, none otherwise
        """
        user = cls.query.filter(cls.email == email, cls.password == password).first()
        return user

    @classmethod
    def authenticate_by_id(cls, id, password):
        """
        Used in basic auth verification that happens on each request

        :param id: user id
        :param password:
        :return: the user row if authentication successful, none otherwise
        """
        user = cls.query.filter(cls.id == id, cls.password == password).first()
        return user

    def update_last_active_to_now(self):
        u = self.__class__.query.get(self.id)
        u.last_activity = datetime.datetime.utcnow()
        db.session.commit()
