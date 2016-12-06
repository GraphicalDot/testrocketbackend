# -*- coding: utf-8 -*-

from exam_app.models import db
from exam_app import app


class Comprehension(db.Model):
    __tablename__ = 'comprehensions'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    questions = db.relationship('Question', backref='comprehension', lazy='dynamic')

    @classmethod
    def create(cls, content):
        """
        Create a comprehension and return the comprehension object

        :param content: text of comprehension
        :return: comprehension object
        """
        content = Question.parse_content(content)
        comprehension = cls(content=content)
        db.session.add(comprehension)
        db.session.commit()
        return comprehension

    @classmethod
    def update(cls, id, content):
        """
        Update the content of a comprehension

        :param id: the comprehension id
        :param content: text of comprehension
        :return: comprehension object
        """
        content = Question.parse_content(content)
        comprehension = cls.query.get(id)
        comprehension.content = content
        db.session.commit()
        return comprehension


from exam_app.models.question import Question
