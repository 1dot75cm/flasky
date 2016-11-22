# coding: utf-8
from __future__ import print_function
import sys
[sys.path.append('/usr/%s/python%s.%s/site-packages' % (arch,
    sys.version_info.major, sys.version_info.minor)) for arch in ('lib', 'lib64')]
try:
    from commands import getoutput
except:
    from subprocess import getoutput
import os
import re
import dnf
import json
import random
import string
import shutil
import hashlib
import bleach
import time
from datetime import datetime
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin, current_user
from jieba.analyse import ChineseAnalyzer
from app.exceptions import ValidationError
from dnf.exceptions import RepoError
from . import db, login_manager, chrome


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
    num_of_view = db.Column(db.Integer, default=0)  # 用户页访问量
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
    comments = db.relationship('Comment', backref='author', lazy='dynamic')  # 返回与用户关联的评论列表
    # backref 向 Comment 模型添加 author 属性, 从而定义反向关系
    # author 属性可代替 author_id 引用 User 模型, 获取与 author 相关的 Comment 模型对象
    oauth = db.relationship('OAuth', backref='local', uselist=False)
    # backref 向 OAuth 模型添加 local 属性, 从而定义反向关系
    # local 属性可代替 local_uid 引用 User 模型, 获取与 local 相关的 OAuth 模型对象

    @staticmethod
    def generate_fake(count=100):
        '''生成虚拟用户数据'''
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
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
            if i > 1:
                ufs = User.query.offset(randint(0, i)).all()
                for uf in ufs[0: randint(0, len(ufs))]:
                    u.follow(uf)
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:  # username, email有重复数据, 则回滚会话
                db.session.rollback()

    @staticmethod
    def add_self_follows():
        '''更新现有用户, 使用户关注自己'''
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
        db.session.commit()

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
        self.followed.append(Follow(followed=self))

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
            url = 'https://cn.gravatar.com/avatar'
        else:
            url = 'http://cn.gravatar.com/avatar'
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

    @property
    def followed_posts(self):
        '''关注用户发布的文章'''
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    def generate_auth_token(self, expiration):
        '''生成用户认证令牌'''
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')  # 根据id生成令牌

    @staticmethod
    def verify_auth_token(token):
        '''验证认证令牌'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])  # 返回用户对象

    def to_json(self):
        '''将用户转为 JSON'''
        json_user = {
            'url': url_for('api.get_user', id=self.id, _external=True),
            'username': self.username,
            'email': self.email.replace('@', '<AT>'),
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts', id=self.id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user

    def add_view(self):
        '''记录用户页访问量'''
        if self.num_of_view is None:
            self.num_of_view = 0
        self.num_of_view += 1
        db.session.add(self)

    def add_favorite(self, post):
        '''收藏文章'''
        if not self.is_favorite(post):
            self.favorite_posts.append(post)
            db.session.add(self)

    def del_favorite(self, post):
        '''取消收藏'''
        if self.is_favorite(post):
            self.favorite_posts.remove(post)
            db.session.add(self)

    def is_favorite(self, post):
        '''判断是否收藏文章'''
        return self.favorite_posts.filter_by(
            id=post.id).first() is not None

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


favorite_relationship = db.Table(
    'favorite_relationship',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True))


class Post(db.Model):
    '''posts表模型'''
    __tablename__ = 'posts'
    __searchable__ = ['title', 'body']  # 需要建立全文索引的字段
    __analyzer__ = ChineseAnalyzer()  # 中文分词
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')  # 返回与文章相关的评论列表
    # backref 向 Comment 模型添加 post 属性, 从而定义反向关系
    # post 属性可代替 post_id 引用 Post 模型, 获取与 post 相关的 Comment 模型对象
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    num_of_view = db.Column(db.Integer, default=0)
    favorite_users = db.relationship('User', secondary=favorite_relationship,
                        backref=db.backref('favorite_posts', lazy='dynamic'),
                        lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        '''生成虚拟文章数据'''
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()  # 用户总数
        cate_count = Category.query.count()  # 分类总数
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()  # 随机选择用户
            c = Category.query.offset(randint(0, cate_count-1)).first()  # 随机选择分类
            p = Post(title=forgery_py.lorem_ipsum.title(),
                     body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     num_of_view=randint(100, 15000),
                     category=c,
                     author=u)
            if i > 1:
                pfs = Post.query.offset(randint(0, i)).all()  # 随机选择文章
                for pf in pfs[0: randint(0, len(pfs))]:
                    u.add_favorite(pf)
            db.session.add_all([p, u])
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        '''将 Markdown 转为 HTML'''
        allowed_tags = ['a', 'abbr', 'acronym', 'br', 'blockquote', 'img',
                        'em', 'i', 'strong', 'b', 'ol', 'ul', 'li',
                        'span', 'code', 'pre', 'p', 'div',
                        'table', 'thead', 'tbody', 'tr', 'th', 'td',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attrs = {'a': ['href', 'title'], 'abbr': ['title'],
                         'acronym': ['title'], 'img': ['alt', 'src'],
                         'span': ['class'], 'div': ['class']}
        extensions = ['extra', 'codehilite', 'nl2br', 'sane_lists']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html', extensions=extensions),
            tags=allowed_tags, attributes=allowed_attrs, strip=True))
        # 1. markdown() 将 md 转为 html
        # 2. bleach.clean() 清除不在白名单中的标签
        # 3. bleach.linkify() 将 URL 转为 <a> 标签

    def to_json(self):
        '''将文章转为 JSON'''
        json_post = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'title': self.title,
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
            'comments': url_for('api.get_post_comments', id=self.id, _external=True),
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        '''将 JSON 转为模型'''
        title = json_post.get('title')
        body = json_post.get('body')
        if title is None or title == '':
            raise ValidationError('post does not have a title')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(title=title, body=body)

    def add_view(self):
        '''记录文章访问量'''
        if self.num_of_view is None:
            self.num_of_view = 0
        self.num_of_view += 1
        db.session.add(self)

    def __repr__(self):
        return '<Post %r>' % self.title


db.event.listen(Post.body, 'set', Post.on_changed_body)
# on_changed_body 函数注册在 body 字段上, 是 SQLAlchemy 'set' 事件的监听程序,
# 只要 Post 类实例的 body 字段设置了新值, 就会自动调用 on_changed_body 函数渲染 HTML


class Comment(db.Model):
    '''comments表模型'''
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)  # 用于管理员禁用不当言论
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        '''将 Markdown 转为 HTML'''
        # 评论要求更严, 删除段落相关的标签, 只留下格式化字符的标签
        allowed_tags = ['a', 'abbr', 'acronym', 'br', 'blockquote', 'img',
                        'em', 'i', 'strong', 'b', 'ol', 'ul', 'li',
                        'span', 'code', 'pre', 'p', 'div',
                        'table', 'thead', 'tbody', 'tr', 'th', 'td']
        allowed_attrs = {'a': ['href', 'title'], 'abbr': ['title'],
                         'acronym': ['title'], 'img': ['alt', 'src'],
                         'span': ['class'], 'div': ['class']}
        extensions = ['extra', 'codehilite', 'nl2br', 'sane_lists']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html', extensions=extensions),
            tags=allowed_tags, attributes=allowed_attrs, strip=True))

    def to_json(self):
        '''将评论转为 JSON'''
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        '''将 JSON 转为模型'''
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)

    @staticmethod
    def generate_fake(count=100):
        '''生成虚拟文章评论'''
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()  # 用户总数
        post_count = Post.query.count()  # 文章总数
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()  # 随机选择用户
            p = Post.query.offset(randint(0, post_count-1)).first()  # 随机选择文章
            c = Comment(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                        timestamp=forgery_py.date.date(True),
                        author=u,
                        post=p)
            db.session.add(c)
        try:
            db.session.commit()
        except:
            db.session.rollback()


db.event.listen(Comment.body, 'set', Comment.on_changed_body)  # 定义事件, 修改 body 时, 渲染 md


# 由于不需要记录额外信息, 这里使用关联表(非模型类), SQLAlchemy 会接管该表
tag_relationship = db.Table('tag_relationship',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True))


class Tag(db.Model):
    '''tags表模型'''
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    posts = db.relationship('Post', secondary=tag_relationship,
                            backref=db.backref('tags', lazy='dynamic'),
                            lazy='dynamic')

    def is_tag(self, post):
        '''判断文章是否包含该标签'''
        return self.posts.filter_by(id=post.id).first() is not None

    @staticmethod
    def process_tag(post, tag_data):
        '''处理标记'''
        tags = re.split(',\s*|\s+', tag_data.lower())
        for tag in tags:
            t = Tag.query.filter_by(name=tag).first()
            if t is None:  # tag不存在
                t = Tag(name=tag)
                t.posts.append(post)
            if not t.is_tag(post):  # 未标记
                t.posts.append(post)
            db.session.add(t)
        for pt in post.tags.all():
            if pt.name not in tags:  # 原tag不在列表中, 删除
                pt.posts.remove(post)
                db.session.add(pt)

    def tag(self, post):
        '''标记文章'''
        if not self.is_tag(post):
            t = self.posts.append(post)
            db.session.add(t)

    def untag(self, post):
        '''取消标记'''
        if self.is_tag(post):
            t = self.posts.remove(post)
            db.session.add(t)

    def __repr__(self):
        return '<Tag %r>' % self.name


class Category(db.Model):
    '''categories表模型'''
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    posts = db.relationship('Post', backref='category', lazy='dynamic')

    @staticmethod
    def insert_category():
        '''插入默认分类'''
        cates = current_app.config['DEFAULT_CATEGORY']
        for i in cates:
            category = Category.query.filter_by(name=i).first()
            if category is None:
                category = Category(name=i)
            db.session.add(category)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    def __repr__(self):
        return '<Category %r>' % self.name


class BlogView(db.Model):
    '''blog pv访问统计'''
    __tablename__ = 'blog_view'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=None)
    user_agent = db.Column(db.Text())
    ip_addr = db.Column(db.String(15))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    page = db.Column(db.String(128))

    @staticmethod
    def add_view():
        '''记录 Blog 日访问量'''
        if request.path.find('static') == -1:  # 过滤请求
            pages = []
            today = time.mktime(datetime.utcnow().date().timetuple())
            pvs = BlogView.query.order_by(BlogView.timestamp.desc())\
                .filter_by(ip_addr=request.remote_addr).all()
            for pv in pvs:
                ts = time.mktime(pv.timestamp.timetuple())
                if ts > today:
                    pages.append(pv.page)
                else:
                    break
            # 不记录同一用户对页面的重复请求
            if request.path not in pages:
                if current_user.is_authenticated:
                    user_id = current_user.id
                else:
                    user_id = None
                pv = BlogView(user_id=user_id,
                              user_agent=request.user_agent.string,
                              ip_addr=request.remote_addr,
                              page=request.path)
                db.session.add(pv)

    def __repr__(self):
        return '<BlogView %r>' % self.id


class OAuth(db.Model):
    '''oauth表模型'''
    __tablename__ = 'oauth'
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('oauth_type.id'))
    local_uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    remote_uid = db.Column(db.String(50))
    access_token = db.Column(db.String(400), unique=True, default='')

    def __repr__(self):
        return '<OAuth %r>' % self.remote_uid


class OAuthType(db.Model):
    '''oauth_type表模型'''
    __tablename__ = 'oauth_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    oauths = db.relationship('OAuth', backref='type', lazy='dynamic')

    @staticmethod
    def insert_oauth():
        '''插入OAuth类型'''
        oauths = current_app.config['DEFAULT_OAUTHS']
        for i in oauths:
            oauth = OAuthType.query.filter_by(name=i).first()
            if oauth is None:
                oauth = OAuthType(name=i)
            db.session.add(oauth)

    def __repr__(self):
        return '<OAuthType %r>' % self.name


class Chrome(db.Model):
    '''chrome表模型'''
    __tablename__ = 'chrome'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    os = db.Column(db.String(5))
    arch = db.Column(db.String(3))
    channel = db.Column(db.String(6))
    version = db.Column(db.String(15))
    size = db.Column(db.String(10))
    hash = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    urls = db.Column(db.Text())

    @staticmethod
    def check_update(system, channel, arch, cache=True, interval=3600):
        '''检查更新, 返回列表'''
        pkglist = []
        p = Chrome.query.order_by(Chrome.timestamp.desc()).first()
        # 查询数据库, 返回包信息
        if p is not None and cache:
            qtime = time.mktime(p.timestamp.timetuple())
            ctime = time.mktime(time.gmtime())
            if ctime - qtime < interval:
                for os in system:
                    p = Chrome.query.filter_by(os=os).all()
                    pkglist += p
                return pkglist, cache

        # 从 Google 获取包信息
        cache = False
        pkgs = chrome.get_pkg_info(system, channel, arch)
        for pkg in pkgs:
            p = Chrome.query.filter_by(hash=pkg['sha256']).first()
            if p is None:
                p = Chrome(name=pkg['name'],
                           version=pkg['version'],
                           os=pkg['os'],
                           arch=pkg['arch'],
                           channel=pkg['channel'],
                           size=pkg['size'],
                           hash=pkg['sha256'],
                           urls=','.join(pkg['urls']))
            else:
                p.timestamp = datetime.utcnow()
            db.session.add(p)
            pkglist.append(p)
        return pkglist, cache

    def __repr__(self):
        return '<Chrome %r>' % self.name


class Package(db.Model):
    '''packages表模型'''
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    pkgnames = db.Column(db.Text)
    task_id = db.Column(db.String(100), unique=True)
    release_id = db.Column(db.Integer, db.ForeignKey('releases.id'))
    karma = db.Column(db.Integer, default=0)
    status = db.Column(db.String(10), default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.Integer, default=3600*24*2)
    comments = db.relationship('Comment', backref='package', lazy='dynamic')

    @staticmethod
    def insert_pkgs(pkgs, arch, release):
        '''插入package'''
        for pkg in pkgs:
            pkgname = '%s-%s-%s.%s.rpm' % (pkg.name, pkg.version, pkg.release, pkg.arch)
            p = Package.query.filter_by(name=pkg.sourcerpm.split('.src.rpm')[0]).first()
            if p is None:
                p = Package(
                    name=pkg.sourcerpm.split('.src.rpm')[0],
                    pkgnames=json.dumps({'i386': [], 'x86_64': []}),
                    task_id=Package.generate_task_id(),
                    release=Release.query.filter_by(name=release).first(),
                    deadline=current_app.config['PKG_DEADLINE'])
            p.add_pkg(arch, pkgname)
            db.session.add(p)
        db.session.commit()

    def get_pkg_dict(self):
        '''返回package字典'''
        return json.loads(self.pkgnames)

    def add_pkg(self, arch, pkg):
        '''写入pkg至pkgnames字段'''
        pkgnames = self.get_pkg_dict()
        if pkg not in pkgnames[arch]:
            pkgnames[arch].append(pkg)
            self.pkgnames = json.dumps(pkgnames)

    @staticmethod
    def scan_repo():
        '''扫描 repo 写入数据库'''
        config = current_app.config
        for rel in config['DEFAULT_RELEASES']:
            for arch in config['REPO_ARCH']:
                reponame = '%s_fc%s_%s' % (
                    config['REPO_TESTING_DIR'], rel[1:], arch)
                r = dnf.repo.Repo(id_=reponame, cachedir='/tmp/')
                r.baseurl = '/'.join([
                    config['REPO_URL'],
                    config['REPO_TESTING_DIR'],
                    rel[1:], arch])
                try:
                    r.load()
                except RepoError:
                    continue

                b = dnf.Base()
                b.repos.add(r)
                b.fill_sack(load_available_repos=True)
                q = b.sack.query()
                pkgs = q.filter(reponame=reponame).run()
                Package.insert_pkgs(pkgs, arch, rel)

    @staticmethod
    def generate_task_id(length=10):
        '''生成ID'''
        return 'Fedora-%s-%s' % (
            datetime.today().year,
            ''.join(random.sample(string.ascii_letters+string.digits, length)))

    @staticmethod
    def create_repo(output):
        '''Creates metadata of rpm repository'''
        command = '/bin/createrepo_c -d -x *.src.rpm '
        if isinstance(output, list):
            return [getoutput(''.join([command, out])) for out in output]
        if isinstance(output, str):
            return getoutput(''.join([command, output]))

    def set_karma(self, data):
        '''set karma'''
        if data.find('+1') != -1:
            self.karma += 1
        if data.find('-1') != -1:
            self.karma -= 1
        self.check_karma()
        db.session.add(self)

    def check_karma(self):
        '''check karma'''
        config = current_app.config
        qtime = time.mktime(self.timestamp.timetuple())
        ctime = time.mktime(time.gmtime())
        if self.status == 'pending':
            self.to_testing()
        if self.karma >= config['KARMA_MINI_STABLE'] \
                and ctime - qtime > self.deadline \
                and self.status == 'testing':
            self.to_stable()
        if self.karma >= config['KARMA_TO_STABLE'] \
                and self.status == 'testing':
            self.to_stable()
        if ctime - qtime > self.deadline and self.status == 'testing':
            self.to_stable()
        if self.karma <= config['KARMA_MINI_OBSOLETE'] \
                and ctime - qtime > self.deadline \
                and self.status == 'testing':
            self.to_obsolete()
        if self.karma <= config['KARMA_TO_OBSOLETE'] \
                and self.status == 'testing':
            self.to_obsolete()

    def to_testing(self):
        '''修改包状态为testing'''
        self.status = 'testing'
        db.session.add(self)

    def to_stable(self):
        '''修改包状态为stable'''
        self.status = 'stable'
        pkgs = self.get_pkg_dict()
        base = current_app.config['REPO_PATH']
        release = self.release.name[1:]
        for arch in current_app.config['REPO_ARCH']:
            spath = os.path.join(base, current_app.config['REPO_TESTING_DIR'], release, arch)
            tpath = os.path.join(base, current_app.config['REPO_STABLE_DIR'], release, arch)
            for pkg in pkgs[arch]:
                source = os.path.join(spath, pkg)
                target = os.path.join(tpath, pkg)
                try:
                    shutil.move(source, target)
                except IOError as e:
                    print(e)
            if not os.environ.get('IS_DAEMON', ''):
                self.create_repo([spath, tpath])
        db.session.add(self)
        db.session.commit()
        return True

    def to_obsolete(self):
        '''修改包状态为obsolete'''
        self.status = 'obsolete'
        db.session.add(self)

    def __repr__(self):
        return '<Package %r>' % self.name


class Release(db.Model):
    '''releases表模型'''
    __tablename__ = 'releases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10))
    packages = db.relationship('Package', backref='release', lazy='dynamic')

    @staticmethod
    def insert_release():
        '''插入默认Release'''
        releases = current_app.config['DEFAULT_RELEASES']
        for release in releases:
            rel = Release.query.filter_by(name=release).first()
            if rel is None:
                rel = Release(name=release)
            db.session.add(rel)

    def __repr__(self):
        return '<Release %r>' % self.name
