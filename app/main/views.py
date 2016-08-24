# coding: utf-8
from flask import render_template, session, redirect, url_for, current_app
from .. import db
from ..models import User
from ..email import send_email
from . import main
from .forms import NameForm

@main.route('/', methods=['GET', 'POST'])
def index():
    '''主页视图函数'''
    form = NameForm()
    if form.validate_on_submit():  # 验证表单
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)  # 创建 user 对象
            db.session.add(user)  # 添加数据至 db 会话
            session['known'] = False
            if app.config['FLASKY_ADMIN']:  # 新用户注册, 向管理员发邮件
                send_email(app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True  # 根据用户是否注册, 在前端显示不同内容
        session['name'] = form.name.data  # 使用会话保存 name
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))
