# coding: utf-8
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

app = Flask(__name__)  # 实例化app
app.config['SECRET_KEY'] = 'secret_key_string'  # 用于加密 session 的密钥

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(Form):
    '''Name表单类'''
    name = StringField('What is your name?', validators=[Required()])  # 文本字段
    submit = SubmitField('Submit')  # 提交按钮


@app.errorhandler(404)
def page_not_found(e):
    '''自定义404页面'''
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    '''自定义500页面'''
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    '''主页视图函数'''
    form = NameForm()
    if form.validate_on_submit():  # 验证表单
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data  # 使用会话保存 name
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'))

if __name__ == '__main__':
    manager.run()
