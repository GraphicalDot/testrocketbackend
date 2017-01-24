import os
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from exam_app import app
from exam_app.models import db
 
_POSTGRES = {
        'host': 'localhost',
        'user': 'postgres2',
        'password': 'postgres',
        'database': 'exam_prep'
    }
    
SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(password)s@%(host)s/%(database)s' % _POSTGRES



app.config.from_object('exam_app.config.DevelopmentConfig')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()