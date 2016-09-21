# coding: utf-8
import os
basedir = os.path.abspath(os.getcwd())
datadir = os.path.join(basedir, 'data')
logdir  = os.path.join(datadir, 'logs')


class Config:
    '''通用配置'''
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 请求结束后, 自动提交
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    MAIL_SERVER = os.getenv('MAIL_SERVER') or 'smtp.googlemail.com'
    MAIL_PORT = os.getenv('MAIL_PORT') or 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.getenv('FLASKY_ADMIN')
    FLASKY_POSTS_PER_PAGE = 20
    FLASKY_PKGS_PER_PAGE = 25
    FLASKY_FOLLOWERS_PER_PAGE = 50
    FLASKY_COMMENTS_PER_PAGE = 30
    SECRET_KEY = os.getenv('SECRET_KEY') or 'secret_key_string'  # 用于加密 session 的密钥
    WTF_CSRF_SECRET_KEY = 'random key for form' # for csrf protection
    # https://github.com/xpleaf/Blog_mini/blob/master/config.py
    # Take good care of 'SECRET_KEY' and 'WTF_CSRF_SECRET_KEY', if you use the
    # bootstrap extension to create a form, it is Ok to use 'SECRET_KEY',
    # but when you use tha style like '{{ form.name.labey }}:{{ form.name() }}',
    # you must do this for yourself to use the wtf, more about this, you can
    # take a reference to the book <<Flask Framework Cookbook>>.
    # But the book only have the version of English.

    # GitHub OAuth2
    GITHUB = dict(
        consumer_key = os.getenv('GITHUB_ID'),
        consumer_secret = os.getenv('GITHUB_SECRET'),
        base_url = 'https://api.github.com/',
        request_token_url = None,
        request_token_params = {'scope': 'user:email'},
        access_token_method = 'POST',
        access_token_url = 'https://github.com/login/oauth/access_token',
        authorize_url = 'https://github.com/login/oauth/authorize'
    )

    # Google OAuth2
    GOOGLE = dict(
        consumer_key = os.getenv('GOOGLE_ID'),
        consumer_secret = os.getenv('GOOGLE_SECRET'),
        base_url='https://www.googleapis.com/oauth2/v2/',
        request_token_params = {'scope': 'email'},
        request_token_url = None,
        access_token_method = 'POST',
        access_token_url = 'https://accounts.google.com/o/oauth2/token',
        authorize_url = 'https://accounts.google.com/o/oauth2/auth'
    )

    # Fedora FAS OpenID
    FAS_OPENID_ENDPOINT = 'https://id.fedoraproject.org/openid/'
    FAS_OPENID_CHECK_CERT = True

    DEFAULT_CATEGORY = ['Python', 'JavaScript', 'CentOS', 'Fedora', 'MySQL', 'Redis']
    DEFAULT_OAUTHS = ['github', 'google', 'fedora']
    DEFAULT_RELEASES = ['F22', 'F23', 'F24', 'F25']
    REPO_URL = 'https://repo.fdzh.org/FZUG'
    REPO_ARCH = ['x86_64', 'i386']
    REPO_PATH = os.path.join(os.getenv('REPO_PATH'))
    REPO_TESTING_DIR = os.getenv('REPO_TESTING_DIR') or 'testing'
    REPO_STABLE_DIR = os.getenv('REPO_STABLE_DIR') or 'stable'
    PKG_DEADLINE = 3600 * 24 * os.getenv('PKG_DEADLINE', 2)
    KARMA_MINI_STABLE = 1
    KARMA_TO_STABLE = 2
    KARMA_MINI_OBSOLETE = -1
    KARMA_TO_OBSOLETE = -2
    INTERVAL = 3600 * os.getenv('INTERVAL', 0.5)

    @staticmethod
    def init_app(app):
        '''初始化app'''
        pass


class DevelopmentConfig(Config):
    '''开发环境配置'''
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    '''测试环境配置'''
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    '''生产环境配置'''
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
