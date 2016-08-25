# coding: utf-8
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from . import db, login_manager


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


class User(db.Model, UserMixin):
    '''users表模型'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 外键, 值为 roles.id
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)  # 账户是否经过邮箱验证

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

    def generate_confirmation_token(self, expiration=3600):
        '''生成确认账户令牌'''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        '''验证确认账户令牌'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:  # 检查id是否和已登陆用户匹配
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        '''生成重设密码令牌'''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        '''验证重设密码令牌'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:  # 检查id是否和已登陆用户匹配
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        '''生成更改邮箱令牌'''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        '''验证更改邮箱令牌'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:  # 检查id是否和已登陆用户匹配
            return False
        new_email = data.get('new_email')
        if new_email is None:  # email为空
            return False
        if self.query.filter_by(email=new_email).first() is not None:  # email已存在
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    '''扩展使用该回调函数加载用户'''
    return User.query.get(int(user_id))  # 返回用户对象或 None
