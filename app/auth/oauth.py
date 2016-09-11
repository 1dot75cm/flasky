# coding: utf-8
from flask import request, jsonify, json, url_for, session, g, redirect, flash
from flask_login import login_user
from . import auth
from .. import db, oauth, fas
from ..models import User, OAuth, OAuthType

github = oauth.remote_app('github', app_key='GITHUB')  # GitHub OAuth2


@auth.route('/login/oauth')
def oauth_login():
    '''OAuth登陆'''
    if request.args.get('op') == 'github':
        return github.authorize(callback=url_for('.oauth_authorized',
            next=request.args.get('next') or request.referrer or None,
            op='github', _external=True))
    if request.args.get('op') == 'fedora':
        return fas.login(return_url=url_for('.oauth_authorized',
            next=request.args.get('next') or request.referrer or None,
            op='fedora', _external=True),
            cancel_url=url_for('.login'))
    return jsonify({'error': 'Access denied'})


@auth.route('/login/oauth/authorized')
def oauth_authorized():
    '''授权回调'''
    op = request.args.get('op')
    if op == 'fedora' and g.fas_user:
        oauth = OAuth.query.filter_by(remote_uid=g.fas_user.username).first()
        oauth_type = OAuthType.query.filter_by(name=op).first()
        if oauth is None:
            u = User(email=g.fas_user.email,
                     username=g.fas_user.username,
                     confirmed=True,
                     name=g.fas_user.fullname,
                     location=g.fas_user.timezone,
                     about_me='Welcome to use flasky.',
                     oauth=OAuth(type=oauth_type,
                                 remote_uid=g.fas_user.username))
            db.session.add(u)
            login_user(u)
            flash('Hello, %s.' % u.username, 'success')
            return redirect(request.args.get('next') or url_for('main.index'))
        if oauth:
            login_user(oauth.local)
            flash('Hello, %s.' % oauth.local.username, 'success')
            return redirect(request.args.get('next') or url_for('main.index'))

    if op == 'github':
        resp = github.authorized_response()
        if resp is None:  # 验证失败
            flash('Access denied: reason=%s error=%s' % (
                request.args['error'],
                request.args['error_description']
            ), 'danger')
            return redirect(request.args.get('next') or url_for('.login'))
        if resp.get('access_token'):  # 防刷新
            get = github.get('user', token=(resp['access_token'], ''))
            me = json.loads(get.raw_data)
            oauth = OAuth.query.filter_by(remote_uid=me['id']).first()
            oauth_type = OAuthType.query.filter_by(name=op).first()
            if get.status == 200:
                session['github_id'] = me['id']
                if oauth is None:  # 从未登陆, 创建新账户
                    email_addr = '%s_%s@flasky.org' % (me['login'], me['id'])
                    u = User(email=me['email'] if me['email'] else email_addr,
                             username=me['login'],
                             confirmed=True,
                             name=me['name'] if me['name'] else me['login'],
                             location=me['location'],
                             about_me='Welcome to use flasky.',
                             oauth=OAuth(type=oauth_type,
                                         remote_uid=me['id'],
                                         access_token=resp['access_token']))
                    db.session.add(u)
                    login_user(u)
                    flash('Hello, %s.' % u.username, 'success')
                    return redirect(request.args.get('next') or url_for('main.index'))
                if oauth:  # 再次授权, 更新token
                    oauth.access_token = resp['access_token']
                    login_user(oauth.local)
                    flash('Hello, %s.' % oauth.local.username, 'success')
                    return redirect(request.args.get('next') or url_for('main.index'))
    flash('Access denied.', 'danger')
    return redirect(request.args.get('next') or url_for('.login'))


@github.tokengetter
def get_github_oauth_token(token=None):
    '''读取第三方应用返回的 token'''
    uid = session.get('github_id')
    oauth = OAuth.query.filter_by(remote_uid=uid).first()
    return (oauth.access_token, '')
