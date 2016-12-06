# -*- coding: utf-8 -*-
import csv, datetime

from md5 import md5

import exam_app
from exam_app import app, db
from exam_app.models.institute import Institute
from exam_app.models.student import Student
from exam_app.models.batch import Batch
from exam_app.models.student_batches import StudentBatches

ctx = app.test_request_context()
ctx.push()

def get_data_from_csv(file_path):
    csv_file = open(file_path, 'rb')
    student_data = csv.DictReader(csv_file)
    return student_data

def create_student(student_details, all_batches):
    student = Student.create(
        name = student_details['name'],
        email = student_details['email'],
        password = md5(student_details['password']).hexdigest(),
        mobile_no = student_details['mobile_no'],
        city = student_details['city'],
        area = student_details['area'],
        # pin = student_details['pin'],
        school = student_details['school'],
        # ntse_score = student_details['ntse_score'],
        roll_no = student_details['roll_no'],
        father_name = student_details['father_name'],
        father_mobile_no = student_details['father_mobile_no'],
        # father_email = student_details['father_email'],
        registered_from = student_details['registered_from'],
        target_year = int(student_details['target_year'])
    )
    student.branches = [i for i in student_details['branches'].split(',')]
    student.target_exams = [int(i) for i in student_details['target_exams'].split(',')]
    batch_obj = all_batches[student_details['batch']]
    student_batch = StudentBatches(batch_id=batch_obj['id'], student_id=student.id, joined_at=datetime.datetime.utcnow())
    db.session.add(student_batch)
    db.session.commit()


_students = get_data_from_csv('/Users/rishabh/Downloads/student_data.csv')
students = [student for student in _students]
institute = Institute.get(4)
batches = Batch.get_filtered(institute_id=institute.id)
batches = {batch.name: batch.__dict__ for batch in batches}
# for student in students:
#     create_student(student, batches)
