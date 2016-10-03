#!/usr/bin/env python2
# coding: utf-8
import os
import shutil
from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment, Tag,\
    Category, BlogView, OAuth, OAuthType, Chrome, Package, Release
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
is_sqlite = app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite')
manager = Manager(app)
migrate = Migrate(app, db, render_as_batch=is_sqlite)
# SQLite do not support ALTER, so add render_as_batch=True and naming convention
# https://github.com/miguelgrinberg/Flask-Migrate/issues/61#issuecomment-208131722


def string_split(string, split):
    '''string to list filter'''
    return string.split(split)

# Global variables to jinja2 environment:
app.jinja_env.globals['Post'] = Post
app.jinja_env.globals['Comment'] = Comment
app.jinja_env.globals['Tag'] = Tag
app.jinja_env.globals['Category'] = Category
app.jinja_env.globals['BlogView'] = BlogView
app.jinja_env.globals['Language'] = app.config['LANGUAGES']
app.jinja_env.filters['split'] = string_split


def make_shell_context():
    '''定义向Shell导入的对象'''
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment,
                Tag=Tag, Category=Category, BlogView=BlogView, OAuth=OAuth,
                OAuthType=OAuthType, Chrome=Chrome, Package=Package, Release=Release)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)


@manager.command
def test():
    '''Run the unit tests.'''
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy(deploy_type='product'):
    '''Deploy project.'''
    from flask_migrate import upgrade
    from app.models import Role, User, Category, Post, Comment

    # upgrade database to the latest version
    upgrade()

    if deploy_type == 'product':
        # create user roles
        Role.insert_roles()
        # create self-follows for all users
        User.add_self_follows()
        # insert default category
        Category.insert_category()
        # insert default oauth
        OAuthType.insert_oauth()
        # insert default release
        Release.insert_release()

    # run `python manage.py deploy test_data`
    if deploy_type == 'test_data':
        # insert admin account
        User(email='admin@flasky.com',
             username='admin',
             password='admin',
             role=Role.query.get(2),
             confirmed=True)
        # generate random users
        User.generate_fake(50)
        # generate random articles
        Post.generate_fake(500)
        # generate random comments
        Comment.generate_fake(5000)


@manager.command
def scan_repo():
    '''Scan rpm package in repository.'''
    Package.scan_repo()


@manager.command
def check_karma():
    '''Check karma and push package.'''
    pkgs = Package.query.all()
    for pkg in pkgs:
        pkg.check_karma()


@manager.command
def create_repo():
    '''Create repositories.'''
    base = app.config['REPO_PATH']
    releases = app.config['DEFAULT_RELEASES']
    for release in releases:
        for arch in app.config['REPO_ARCH']:
            spath = os.path.join(base, app.config['REPO_TESTING_DIR'], release[1:], arch)
            tpath = os.path.join(base, app.config['REPO_STABLE_DIR'], release[1:], arch)
            Package.create_repo([spath, tpath])


@manager.command
def tran_init(code):
    '''Initial new language and create directory.'''
    pybabel = 'venv/bin/pybabel'
    os.system(pybabel + ' extract -F babel.cfg -k lazy_gettext -o messages.pot app')  # 生成翻译模板
    os.system('%s init -i messages.pot -d app/translations -l %s' % (pybabel, code))  # 初始化新语言
    os.unlink('messages.pot')


@manager.command
def tran_update():
    '''Update language directory.'''
    pybabel = 'venv/bin/pybabel'
    os.system(pybabel + ' extract -F babel.cfg -k lazy_gettext -o messages.pot app')  # 生成翻译模板
    os.system(pybabel + ' update -i messages.pot -d app/translations')  # 更新语言翻译
    os.unlink('messages.pot')


@manager.command
def tran_compile():
    '''Generate binary message catalog (mo file).'''
    pybabel = 'venv/bin/pybabel'
    os.system(pybabel + ' compile -d app/translations')  # 生成 mo 文件


@manager.command
def build_index():
    '''Create whoosh index.'''
    import flask_whooshalchemyplus as whooshalchemy
    if os.path.exists(app.config['WHOOSH_BASE']):
        shutil.rmtree(app.config['WHOOSH_BASE'])
    whooshalchemy.index_all(app)


if __name__ == '__main__':
    manager.run()
