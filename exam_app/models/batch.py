# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.exc import IntegrityError

from exam_app.models import db
from exam_app import app
from exam_app.exceptions import BatchNameAlreadyTaken, InvalidBatchId


class Batch(db.Model):
    __tablename__ = 'batches'
    __table_args__ = (db.UniqueConstraint('name', 'institute_id'), )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(app.config['NAME_MAX_LENGTH']))
    on_weekdays = db.Column(db.Boolean, default=False)
    on_weekends = db.Column(db.Boolean, default=False)
    clazz = db.Column(db.Enum('11', '12', name='classes_enum'))
    target_year = db.Column(db.Integer)
    type = db.Column(db.Enum(*app.config['BATCH_TYPE'].keys(), name='batch_types_enum'))
    target_exam = db.Column(db.Enum(*app.config['TARGET_EXAMS'].keys(), name='target_exams_enum'))
    other = db.Column(db.Text)
    batch_timings = db.Column(db.String(20))
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.Integer, default=1)


    @classmethod
    def create(cls, name, on_weekdays, on_weekends, clazz, target_year, target_exam, type, other, batch_timings, institute_id):
        """
        Create a new batch
        :param name:
        :param on_weekdays:
        :param on_weekends:
        :param clazz:
        :param target_year:
        :param target_exam:
        :param type:
        :param other: some text about batch
        :param batch_timings: string in the form ``h1:m1-h2:m2``
        :param institute_id:
        :return:
        """
        batch = cls(name=name, on_weekdays=on_weekdays, on_weekends=on_weekends, clazz=clazz, target_year=target_year,
            target_exam=target_exam, type=type, other=other, batch_timings=batch_timings, institute_id=institute_id)
        db.session.add(batch)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise BatchNameAlreadyTaken
        return batch

    @classmethod
    def get(cls, id):
        """
        Get a single batch

        :param id:
        :return:
        """

        batch = cls.query.get(id)
        if batch is None:
            raise InvalidBatchId
        return batch

    @classmethod
    def get_filtered(cls, days=None, type=None, target_year=None, target_exam=None, include_ids=None, institute_id=None, status=None, branches=None):
        """
        Get a list of batches after applying filters

        :param days:
        :param type:
        :param target_year:
        :param target_exam:
        :param include_ids:
        :param institute_id:
        :param status:
        :param target_exam_list:
        :return:
        """
        exprs = []
        if days is not None:
            if days == 'weekdays':
                exprs.append(Batch.on_weekdays == True)
            if days == 'weekends':
                exprs.append(Batch.on_weekends == True)
        if type is not None:
            exprs.append(Batch.type == type)
        if target_year is not None:
            exprs.append(Batch.target_year == target_year)
        if target_exam is not None:
            exprs.append(Batch.target_exam == target_exam)
        if institute_id is not None:
            exprs.append(Batch.institute_id == institute_id)
        if include_ids is not None and (isinstance(include_ids, list) or isinstance(include_ids, tuple) or isinstance(include_ids, set)):
            exprs.append(Batch.id.in_(list(include_ids)))
        if branches is not None and (isinstance(branches, list) or isinstance(branches, tuple) or isinstance(branches, set)):
            target_exam_list = []
            engineering_exams = ['1', '2', '3']
            medical_exams = ['4', '5']
            if '1' in branches:
                target_exam_list.extend(engineering_exams)
            if '2' in branches:
                target_exam_list.extend(medical_exams)
            exprs.append(Batch.target_exam.in_(list(target_exam_list)))

        if status is None:
            status = 1
        # explicitly ignoring status
        if status != -1:
            exprs.append(Batch.status == status)

        return Batch.query.filter(*exprs).order_by(Batch.created_at.desc()).all()


from exam_app.models.institute import Institute
