# coding: utf-8
import flask_whooshalchemyplus as whooshalchemy
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_oauthlib.client import OAuth
from flask_fas_openid import FAS
from flask_babel import Babel, lazy_gettext
from flask_cache import Cache
from flask_cachecontrol import FlaskCacheControl
from flask_compress import Compress
from flask_qrcode import QRcode
from .qrcodex import QRcodeEx
from sqlalchemy import MetaData

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
ma = Marshmallow()
pagedown = PageDown()
oauth = OAuth()
fas = FAS(Flask(__name__))
babel = Babel()
cache = Cache()
cache_control = FlaskCacheControl()
compress = Compress()
qrcode = QRcodeEx()

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # 会话安全等级
login_manager.login_view = 'auth.login'  # 登陆页endpoint
login_manager.login_message = lazy_gettext('Please log in to access this page.')  # 惰性求值
