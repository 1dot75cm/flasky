# coding: utf-8
import os
from flask import Flask, request, session
from .ext import (bootstrap, mail, moment, db, ma, login_manager, pagedown,
                  oauth, fas, babel, cache, cache_control, compress, qrcode,
                  whooshalchemy)
from .models import Post, Comment, Category, Tag, BlogView
from config import config


def initial_template_variable(app):
    '''初始化 Jinja2 模板变量'''
    def string_split(string, split):
        '''string to list filter'''
        return string.split(split)

    # Global variables to jinja2 environment
    app.add_template_global(Post, 'Post')
    app.add_template_global(Comment, 'Comment')
    app.add_template_global(Tag, 'Tag')
    app.add_template_global(Category, 'Category')
    app.add_template_global(BlogView, 'BlogView')
    app.add_template_global(app.config['LANGUAGES'], 'Language')
    app.add_template_filter(string_split, 'split')


def create_app(config_name):
    '''初始化App和扩展类'''
    app = Flask(__name__)
    # 将配置类通过from_object()方法导入app.config字典
    app.config.from_object(config[config_name])
    # 执行指定配置的初始化动作
    config[config_name].init_app(app)
    # 初始化 Jinja2 模板变量
    initial_template_variable(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    ma.init_app(app)  # 必须在 Flask-SQLAlchemy 后初始化
    login_manager.init_app(app)
    pagedown.init_app(app)
    oauth.init_app(app)
    fas.__init__(app)
    babel.init_app(app)
    cache.init_app(app)
    cache_control.init_app(app)
    compress.init_app(app)
    qrcode.init_app(app)
    whooshalchemy.init_app(app)  # 创建全文索引

    # 拦截发往 http 的请求, 重定向到 https
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    # 附加路由和错误页面, 在蓝图中定义
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    # localeselector function is already registered
    if babel.locale_selector_func:
        babel.locale_selector_func = None

    @babel.localeselector
    def get_locale():
        '''读取请求的 Accept-Language 头或 Cookie,
        从支持的语言列表中选择语言'''
        if session.get('locale'):
            return session['locale']
        return request.accept_languages.best_match(
            app.config['LANGUAGES'].keys())

    # https://gist.github.com/Ostrovski/f16779933ceee3a9d181
    @app.url_defaults  # 所有视图的回调函数, 用于渲染前处理 url
    def hashed_static_file(endpoint, values):
        '''为静态文件添加参数, 用于更新缓存'''
        if 'static' == endpoint or endpoint.endswith('.static'):
            filename = values.get('filename')
            if filename:
                blueprint = request.blueprint
                if '.' in endpoint:  # blueprint
                    blueprint = endpoint.rsplit('.', 1)[0]

                static_folder = app.static_folder
                if blueprint and app.blueprints[blueprint].static_folder:
                    static_folder = app.blueprints[blueprint].static_folder

                fp = os.path.join(static_folder, filename)
                if os.path.exists(fp):
                    values['_'] = int(os.stat(fp).st_mtime)  # 文件修改时间

    @app.before_request
    def before_request():
        '''处理请求缓存'''
        if request.method == 'POST':  # 使下次 GET 缓存失效
            session['nocache'] = True

    @app.after_request
    def after_request(response):
        '''请求后, 删除 nocache 使缓存生效'''
        if request.method == 'GET' and request.endpoint != 'main.set_locale':  # 使 GET 缓存生效
            session.get('nocache', None) and session.pop('nocache')
        return response

    return app


def cache_key(func_name):
    '''缓存键回调'''
    return '_'.join((
        request.remote_addr or 'localhost',  # test_client 访问后无 remote_addr
        session.get('user_id', 'anonymous'),
        func_name  # app.main.views.index
    ))


def cache_valid():
    '''缓存有效回调'''
    if request.method == 'POST':  # 使 POST 缓存失效
        return True
    return session.get('nocache', None)
