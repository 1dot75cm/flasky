# coding: utf-8
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


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
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        '''只读属性; 读取密码抛出错误'''
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        '''只写属性; 生成密码哈希值'''
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        '''验证密码'''
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username
