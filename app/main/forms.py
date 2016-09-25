# coding: utf-8
from flask_wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import User, Role, Category


class NameForm(Form):
    '''姓名表单'''
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(Form):
    '''编辑用户信息表单'''
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(Form):
    '''管理员编辑用户信息表单'''
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.user = user
        # 在 choices 属性设置 select 控件各选项, 格式: [(选项标识符, 显示文本), ...]
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]

    def validate_email(self, field):
        '''验证邮箱'''
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        '''验证用户名'''
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(Form):
    '''文章表单'''
    title = StringField('Title', validators=[Required()])
    tag = StringField('Tags')
    category = SelectField('Categories', coerce=int)
    body = PageDownField("What's on your mind?", validators=[Required()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # 在 choices 属性设置 select 控件各选项, 格式: [(选项标识符, 显示文本), ...]
        self.category.choices = [(cate.id, cate.name)
            for cate in Category.query.order_by(Category.name).all()]


class CommentForm(Form):
    '''评论表单'''
    body = TextAreaField('Enter your comment', validators=[Required()])
    submit = SubmitField('Submit')
