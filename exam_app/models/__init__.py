# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from exam_app.models.users import UserTypes
from exam_app.models.student import Student
from exam_app.models.teacher import Teacher
from exam_app.models.data_operator import DataOperator
from exam_app.models.intern import Intern
from exam_app.models.institute import Institute
from exam_app.models.payment_plan import PaymentPlan
from exam_app.models.batch import Batch
from exam_app.models.ontology import Ontology
from exam_app.models.question import Question
from exam_app.models.comprehension import Comprehension
from exam_app.models.category_submission import CategorySubmission
from exam_app.models.category_approval import CategoryApproval
from exam_app.models.solution_submission import SolutionSubmission
from exam_app.models.solution_approval import SolutionApproval
from exam_app.models.reported_question import ReportedQuestion
from exam_app.models.mock_test import MockTest
from exam_app.models.pushed_mock_test import PushedMockTest
from exam_app.models.attempted_mock_test import AttemptedMockTest
from exam_app.models.student_batches import StudentBatches
from exam_app.models.past_exam_results import PastExamResult
from exam_app.models.question_upload_set import QuestionUploadSet
