# coding: utf-8
import hashlib
import bleach
from datetime import datetime
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager


class Permission:
    '''权限常量'''
    FOLLOW = 0x01  # 关注用户
    COMMENT = 0x02  # 发表评论
    WRITE_ARTICLES = 0x04  # 写文章
    MODERATE_COMMENTS = 0x08  # 管理评论
    ADMINISTER = 0x80  # 管理员


class Role(db.Model):
    '''roles表模型'''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)  # 默认角色
    permissions = db.Column(db.Integer)  # 角色具有的权限
    users = db.relationship('User', backref='role', lazy='dynamic')  # 返回与角色关联的用户列表
    # backref 向 User 模型添加 role 属性, 从而定义反向关系
    # role 属性可代替 role_id 引用 Role 模型, 获取与角色相关的 User 模型对象

    @staticmethod
    def insert_roles():
        '''创建角色'''
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)  # 创建角色
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    '''follows关联表模型'''
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)  # 关注者
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)  # 被关注者
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 关注时间戳


class User(db.Model, UserMixin):
    '''users表模型'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 外键, 值为 roles.id
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)  # 账户是否经过邮箱验证
    name = db.Column(db.String(64))  # 用户姓名
    location = db.Column(db.String(64))  # 所在地
    about_me = db.Column(db.Text())  # 自我介绍
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)  # 注册日期
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)  # 最后访问日期
    avatar_hash = db.Column(db.String(32))  # 头像hash
    posts = db.relationship('Post', backref='author', lazy='dynamic')  # 返回与用户关联的文章列表
    # backref 向 Post 模型添加 author 属性, 从而定义反向关系
    # author 属性可代替 author_id 引用 User 模型, 获取与用户相关的 Post 模型对象
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')  # 返回我关注的用户列表
    # backref 向 Follow 模型添加 follower 属性, 从而定义反向关系
    # follower 属性可代替 follower_id 引用 User 模型, 获取与 follower 相关的 Follow 模型对象
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')  # 返回关注我的用户列表
    # backref 向 Follow 模型添加 followed 属性, 从而定义反向关系
    # followed 属性可代替 followed_id 引用 User 模型, 获取与 followed 相关的 Follow 模型对象

    @staticmethod
    def generate_fake(count=100):
        '''生成虚拟用户数据'''
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:  # username, email有重复数据, 则回滚会话
                db.session.rollback()

    def __init__(self, **kwargs):
        '''构造函数定义用户默认角色'''
        super(User, self).__init__(**kwargs)
        if self.email == current_app.config['FLASKY_ADMIN']:
            self.role = Role.query.filter_by(permissions=0xff).first()
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

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
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        '''检查用户是否有指定权限'''
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        '''检查是否为管理员'''
        return self.can(Permission.ADMINISTER)

    def ping(self):
        '''刷新用户最后访问日期'''
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        '''生成 Gravatar 头像 URL'''
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def is_following(self, user):
        '''判断我是否关注该用户'''
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        '''判断该用户是否关注我'''
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    def follow(self, user):
        '''关注用户'''
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        '''取消关注'''
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    '''匿名用户类'''
    # 无需确定是否登陆, 就可以检查权限
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    '''扩展使用该回调函数加载用户'''
    return User.query.get(int(user_id))  # 返回用户对象或 None


class Post(db.Model):
    '''posts表模型'''
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def generate_fake(count=100):
        '''生成虚拟文章数据'''
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()  # 用户总数
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()  # 随机选择用户
            p = Post(title=forgery_py.lorem_ipsum.title(),
                     body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        '''将 Markdown 转为 HTML'''
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'img']
        allowed_attrs = {'a': ['href', 'title'], 'abbr': ['title'],
                         'acronym': ['title'], 'img': ['alt', 'src']}
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, attributes=allowed_attrs, strip=True))
        # 1. markdown() 将 md 转为 html
        # 2. bleach.clean() 清除不在白名单中的标签
        # 3. bleach.linkify() 将 URL 转为 <a> 标签

    def __repr__(self):
        return '<Post %r>' % self.title

db.event.listen(Post.body, 'set', Post.on_changed_body)
# on_changed_body 函数注册在 body 字段上, 是 SQLAlchemy 'set' 事件的监听程序,
# 只要 Post 类实例的 body 字段设置了新值, 就会自动调用 on_changed_body 函数渲染 HTML
