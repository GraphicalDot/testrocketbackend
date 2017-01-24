# -*- coding: utf-8 -*-

import json
from hashlib import md5
from base64 import b64encode

import flask
from flask.views import MethodView
from flask import render_template, redirect, request
from flask.ext.restful import reqparse

from exam_app import app
from exam_app.models.student import Student
from exam_app.exceptions import EmailAlreadyRegistered, MobileNoAlreadyRegistered
from exam_app.async_tasks import welcome_student_email_task


class StudentSignup(MethodView):
    def get(self):
        return render_template('student_signup.html')

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('mobile_no', type=str, required=True)
        parser.add_argument('target_year', type=int)
        parser.add_argument('city', type=str)
        parser.add_argument('area', type=str)
        parser.add_argument('branches', type=str, action='append', required=True)
        parser.add_argument('refcode', type=str)
        parser.add_argument('target_exams', type=str, action='append')
        parser.add_argument('father_name', type=str)
        parser.add_argument('father_mobile_no', type=str)
        parser.add_argument('host', type=str)
        try:
            args = parser.parse_args()
        except Exception as e:
            print e.message
            raise e

        args['branches'] = map(str, args['branches'])
        if args['target_exams'] is not None:
            args['target_exams'] = map(str, args['target_exams'])
        else:
            args['target_exams'] = []
            if '1' in args['branches']:
                args['target_exams'].extend(['1', '2', '3'])
            if '2' in args['branches']:
                args['target_exams'].extend(['4', '5'])
            if '3' in args['branches']:
                args['target_exams'].extend(['6'])

        
        try:
            student = Student.create(name=args['name'], email=args['email'], password=md5(args['password']).hexdigest(),
                                 mobile_no=args['mobile_no'], target_year=args['target_year'], city=args['city'], area=args['area'],
                                 branches=args['branches'], target_exams=args['target_exams'], father_name=args['father_name'], 
                                 father_mobile_no=args['father_mobile_no'], registered_from='independent', refcode=args['refcode'])
            print student 
        except EmailAlreadyRegistered:
            #return render_template('student_signup.html', error='email', **args)
            print "email aredy "
            
            return flask.jsonify({"success": False, 
                "error": True,
                "is_email_registered": True,
                "is_mobile_registered": None})

        except MobileNoAlreadyRegistered:
            #return render_template('student_signup.html', error='mobile_no', **args)
            print "mobile aredy "
            return flask.jsonify({"success": False, 
                "error": True,
                "is_email_registered": None,
                "is_mobile_registered": True})


        #welcome_student_email_task.delay({'name': student.name, 'email': student.email})
        token = b64encode(student.email) + '|' + student.password + '|' + str(student.id) + '|' + b64encode(student.name) + '|' + b64encode(','.join(student.target_exams))
        # return redirect(args['host'] + app.config['STUDENT_URL']+'#token='+token)
        

        print flask.jsonify({"success": True, 
                "error": False,
                "token": token})