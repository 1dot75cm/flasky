#!/usr/bin/env python2
# coding: utf-8
import os
from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment, Tag, Category
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
is_sqlite = app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite')
manager = Manager(app)
migrate = Migrate(app, db, render_as_batch=is_sqlite)
# SQLite do not support ALTER, so add render_as_batch=True and naming convention
# https://github.com/miguelgrinberg/Flask-Migrate/issues/61#issuecomment-208131722


def make_shell_context():
    '''定义向Shell导入的对象'''
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment,
                Tag=Tag, Category=Category)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)


@manager.command
def test():
    '''Run the unit tests.'''
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()
