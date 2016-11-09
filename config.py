# coding: utf-8
from __future__ import unicode_literals
from whoosh.analysis import StemmingAnalyzer
import os
basedir = os.path.abspath(os.getcwd())
datadir = os.path.join(basedir, 'data')
logdir  = os.path.join(datadir, 'logs')
covdir  = os.path.join(datadir, 'coverage')
bindir  = os.path.join(datadir, 'bin')
prodir  = os.path.join(datadir, 'profile')


class Config:
    '''通用配置'''
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 请求结束后, 自动提交
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_RECORD_QUERIES = True  # 记录查询统计信息
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
    FLASKY_SLOW_DB_QUERY_TIME = 0.5  # 慢查询阀值, 秒
    SECRET_KEY = os.getenv('SECRET_KEY') or 'secret_key_string'  # 用于加密 session 的密钥
    SSL_DISABLE = False  # 启用 SSL, debug/testing 不生效
    WTF_I18N_ENABLED = True
    WTF_CSRF_SECRET_KEY = 'random key for form' # for csrf protection
    # https://github.com/xpleaf/Blog_mini/blob/master/config.py
    # Take good care of 'SECRET_KEY' and 'WTF_CSRF_SECRET_KEY', if you use the
    # bootstrap extension to create a form, it is Ok to use 'SECRET_KEY',
    # but when you use tha style like '{{ form.name.labey }}:{{ form.name() }}',
    # you must do this for yourself to use the wtf, more about this, you can
    # take a reference to the book <<Flask Framework Cookbook>>.
    # But the book only have the version of English.
    MAX_SEARCH_RESULTS = 50  # 搜索结果的最大数量
    WHOOSH_ANALYZER = StemmingAnalyzer()  # 全局默认分析器
    DEFAULT_OAUTHS = ['github', 'google', 'fedora']

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

    # Post categories
    DEFAULT_CATEGORY = ['Python', 'JavaScript', 'CentOS', 'Fedora', 'MySQL', 'Redis']

    # RPM package tool
    DEFAULT_RELEASES = ['F22', 'F23', 'F24', 'F25']
    REPO_URL = 'https://repo.fdzh.org/FZUG'
    REPO_ARCH = ['x86_64', 'i386']
    REPO_PATH = os.path.join(os.getenv('REPO_PATH') or '/tmp')
    REPO_TESTING_DIR = os.getenv('REPO_TESTING_DIR') or 'testing'
    REPO_STABLE_DIR = os.getenv('REPO_STABLE_DIR') or 'stable'
    PKG_DEADLINE = 3600 * 24 * os.getenv('PKG_DEADLINE', 2)
    KARMA_MINI_STABLE = 1
    KARMA_TO_STABLE = 2
    KARMA_MINI_OBSOLETE = -1
    KARMA_TO_OBSOLETE = -2
    INTERVAL = 3600 * os.getenv('INTERVAL', 0.5)

    # Available languages
    LANGUAGES = dict(
        en_US = ['English', 'en_US'],
        zh_Hans = ['简体中文', 'zh_CN']
    )
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'

    # Cache
    CACHE_TYPE = 'simple'  # null, simple, memcached, redis, filesystem
    CACHE_DEFAULT_TIMEOUT = 600  # 缓存超时
    CACHE_THRESHOLD = 1000  # 最大缓存条数

    # Cache for redis
    #CACHE_TYPE = 'redis'
    #CACHE_KEY_PREFIX = 'flasky'  # 在键之前添加前缀, 区分不同应用程序
    #CACHE_REDIS_URL = 'redis://user:password@localhost:6379/2'
    #CACHE_REDIS_HOST = 'localhost'
    #CACHE_REDIS_PORT = 6379
    #CACHE_REDIS_PASSWORD = 'password'
    #CACHE_REDIS_DB = 0  # db库

    COMPRESS_LEVEL = 6  # Gzip 压缩级别
    COMPRESS_MIN_SIZE = 500  # 最小压缩大小

    @staticmethod
    def init_app(app):
        '''初始化app'''
        pass


class DevelopmentConfig(Config):
    '''开发环境配置'''
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(datadir, 'data-dev.sqlite')
    WHOOSH_BASE = os.getenv('DEV_WHOOSH_INDEX_DIR') or \
        os.path.join(datadir, 'search-dev.index')


class TestingConfig(Config):
    '''测试环境配置'''
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(datadir, 'data-test.sqlite')
    WHOOSH_BASE = os.getenv('TEST_WHOOSH_INDEX_DIR') or \
        os.path.join(datadir, 'search-test.index')
    WTF_CSRF_ENABLED = False  # 测试中禁用 CSRF 保护, 否则 POST 需要提交 CSRF Token


class ProductionConfig(Config):
    '''生产环境配置'''
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(datadir, 'data.sqlite')
    WHOOSH_BASE = os.getenv('WHOOSH_INDEX_DIR') or \
        os.path.join(datadir, 'search.index')

    @classmethod
    def init_app(cls, app):
        '''配置 logging 将日志写入 email 日志记录器'''
        # 把生产模式中出现的错误通过 email 发给 FLASKY_ADMIN
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None

        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        # 严重错误才发送邮件；通过添加其他日志处理程序，可以把日志写入文件或系统日志
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    '''Heroku 环境配置'''
    SSL_DISABLE = bool(os.getenv('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        '''配置 logging 将日志写入 stdout/stderr'''
        # Heroku 中, 写入 stdout/stderr 的日志会被 Heroku 捕获, 用 heroku logs 命令查看
        ProductionConfig.init_app(app)

        # handle proxy server headers
        # 做了以上改动后, 用户会强制使用 SSL。但还有一个细节需要处理才能完善该功能。
        # 使用 Heroku 时, 客户端不直接连接托管的程序, 而是连接一个反向代理服务器,
        # 然后再把请求重定向到程序。这种连接方式中, 只有代理服务器运行在 SSL 模式。
        # 程序从代理服务器收到的请求都未使用 SSL, 因为内网无需使用高安全性的请求。
        # 程序生成绝对 URL 时, 要和请求使用的安全连接一致, 这时就产生问题了, 使用
        # 反向代理服务器时, request.is_secure 的值一直是 False。
        #
        # 代理服务器通过自定义 HTTP 头, 把客户端的原始请求传给后端 Web 服务器,
        # 所以查看这些 HTTP 头就可以知道用户和程序通信时是否使用 SSL。Werkzeug
        # 提供了一个 WSGI 中间件, 用来检查代理服务器发出的自定义头并对请求对象进行修改。
        # 注意: 任何使用反向代理的部署环境都需要该中间件处理自定义 HTTP 头
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)  # 警告级别日志
        app.logger.addHandler(file_handler)


class UnixConfig(ProductionConfig):
    '''Linux 环境配置'''

    @classmethod
    def init_app(cls, app):
        '''配置 logging 将日志写入 rsyslog'''
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig,

    'default': DevelopmentConfig
}
