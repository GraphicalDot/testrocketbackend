# -*- coding: utf-8 -*-

from exam_app.models import db
from exam_app import app


class PaymentPlan(db.Model):
    __tablename__ = 'payment_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(app.config['NAME_MAX_LENGTH']), unique=True)
    price = db.Column(db.Integer)
