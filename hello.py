# coding: utf-8
import os
from flask import Flask, render_template, session, redirect, url_for
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)  # 实例化app
app.config['SECRET_KEY'] = 'secret_key_string'  # 用于加密 session 的密钥
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')  # 数据库URI
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # 请求结束后, 自动提交
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)


class Role(db.Model):
    '''roles表模型'''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')  # 返回与角色关联的用户列表
    # backref 向 User 模型添加 role 属性, 从而定义反向关系
    # role 属性可代替 role_id 访问 Role 模型, 获取模型对象

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    '''users表模型'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 外键, 值为 roles.id

    def __repr__(self):
        return '<User %r>' % self.username


class NameForm(Form):
    '''Name表单类'''
    name = StringField('What is your name?', validators=[Required()])  # 文本字段
    submit = SubmitField('Submit')  # 提交按钮


def make_shell_context():
    '''定义向Shell导入的对象'''
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))


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
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)  # 创建 user 对象
            db.session.add(user)  # 添加数据至 db 会话
            session['known'] = False
        else:
            session['known'] = True  # 根据用户是否注册, 在前端显示不同内容
        session['name'] = form.name.data  # 使用会话保存 name
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))


if __name__ == '__main__':
    db.create_all()  # 创建所有表
    manager.run()
