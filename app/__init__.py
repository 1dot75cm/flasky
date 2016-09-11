# coding: utf-8
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_oauthlib.client import OAuth
from flask_fas_openid import FAS
from sqlalchemy import MetaData
from config import config

# SQLite naming convention
# https://github.com/miguelgrinberg/Flask-Migrate/issues/61#issuecomment-208131722
metadata = MetaData(naming_convention = {
    'ix': 'ix_%(column_0_label)s',  # index
    'uq': 'uq_%(table_name)s_%(column_0_name)s',  # unique
    'ck': 'ck_%(table_name)s_%(column_0_name)s',  # check
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',  # foreign key
    'pk': 'pk_%(table_name)s'  # primary key
})

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy(metadata=metadata)
pagedown = PageDown()
oauth = OAuth()
fas = FAS(Flask(__name__))

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # 会话安全等级
login_manager.login_view = 'auth.login'  # 登陆页endpoint


def create_app(config_name):
    '''初始化App和扩展类'''
    app = Flask(__name__)
    # 将配置类通过from_object()方法导入app.config字典
    app.config.from_object(config[config_name])
    # 执行指定配置的初始化动作
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    oauth.init_app(app)
    fas.__init__(app)

    # 附加路由和错误页面, 在蓝图中定义
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app
