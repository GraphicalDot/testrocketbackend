# TestRocket Backend

## How to get it up & running?

### Installing PostgreSQL
Install PostgreSQL. Version `9.4.0` has been used during the time of development. Preferably install the same to avoid any issues.

### Python Requirements
All the requirements for python are listed in `requirements.txt`. Use pip to install the requirements.
```python
pip install -r requirements.txt
```

### PostgreSQL Part
We will need to create the necessary users etc. in PostgreSQL to get the final stuff up and running. Here are the list of commands you would need to run.
```sql
CREATE DATABASE exam_prep;
CREATE USER postgres WITH PASSWORD 'postgres'; /* this is the username password used by API code to connect to the DB. */
GRANT ALL PRIVILEGES ON DATABASE "exam_prep" to postgres;
psql -d exam_app -c 'create extension hstore;'
/*CREATE EXTENSION hstore;  this is used for storing key value pairs in DB columns. */
```

You will also need to seed the DB with some basic data and the first user. Later on this first user will be used to create all the future users.

```sql
\connect exam_app
INSERT INTO user_types VALUES(1,'data_operator'), (2, 'intern'), (3, 'teacher'), (4,'student'), (5, 'teacher'); /* different types of supported users. */
INSERT INTO data_operators(name, email, password, is_active, type) VALUES('first_user', 'hi@testrocket.in', 'e668d6aab96940f26fbe81ea538eb71b', true, 1);
```
`e668d6aab96940f26fbe81ea538eb71b` in the 2nd line is the MD5 of `testrocket` which is the password of the first user.

## Using the API

There is a Postman collection explaining about the API usage. The whole API is protected by basic HTTP auth where the username & password are given using the normal HTTP Basic Authentication specification except the username includes the user type also and password is sent as MD5 instead of plain string.

1. `<user_type>|<username>` is the format for specifying the `username`. Triangular brackets are not supposed to be used, they are just for readability here.
2. `password` is given as normal string of MD5 of the password.



#If you are using an old application then the student table has some issue with
# branches filed as branches on the front end are listed as ["Engineering",
# "Medical", "Foundation"] which are too too big to fit in db.String(1), so now
# models/student.py has updated students table. If you are running the
#application for the first time, the datatype for branches in students will be
#updated automaticlly . But if its already runing , enter this command on your 
# psql console, It will do the needful. 
alter table students alter column  branches type character varying(50)[];

