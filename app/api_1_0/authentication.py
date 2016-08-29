# coding: utf-8
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, forbidden

auth = HTTPBasicAuth()  # 该认证只用于 API 蓝图, 因此在此初始化


@auth.verify_password
def verify_password(email_or_token, password):
    '''密码验证回调'''
    if email_or_token == '':  # 匿名用户
        g.current_user = AnonymousUser()
        return True
    if password == '':  # 验证token
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True  # 当前为令牌验证
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user  # 通过验证的用户保存至全局对象g, 供视图函数访问
    g.token_used = False  # 当前为密码验证
    return user.verify_password(password)  # 验证密码


@auth.error_handler
def auth_error():
    '''自定义错误响应'''
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    '''验证所有蓝图中的路由'''
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:  # 拒绝已登陆但未确认账户的用户
        return forbidden('Unconfirmed account')


@api.route('/token')
def get_token():
    '''生成令牌'''
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
