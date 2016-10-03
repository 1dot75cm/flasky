# coding: utf-8
from flask_wtf import FlaskForm as Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from flask_babel import lazy_gettext as _  # 直到渲染表单时, 才惰性翻译文本
from ..models import User, Role, Category


class NameForm(Form):
    '''姓名表单'''
    name = StringField(_('What is your name?'), validators=[Required()])
    submit = SubmitField(_('Submit'))


class EditProfileForm(Form):
    '''编辑用户信息表单'''
    name = StringField(_('Real name'), validators=[Length(0, 64)])
    location = StringField(_('Location'), validators=[Length(0, 64)])
    about_me = TextAreaField(_('About me'))
    submit = SubmitField(_('Submit'))


class EditProfileAdminForm(Form):
    '''管理员编辑用户信息表单'''
    email = StringField(_('Email'), validators=[Required(), Length(1, 64), Email()])
    username = StringField(_('Username'), validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                        _('Usernames must have only letters, '
                                          'numbers, dots or underscores'))])
    confirmed = BooleanField(_('Confirmed'))
    role = SelectField(_('Role'), coerce=int)
    name = StringField(_('Real name'), validators=[Length(0, 64)])
    location = StringField(_('Location'), validators=[Length(0, 64)])
    about_me = TextAreaField(_('About me'))
    submit = SubmitField(_('Submit'))

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
            raise ValidationError(_('Email already registered.'))

    def validate_username(self, field):
        '''验证用户名'''
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError(_('Username already in use.'))


class PostForm(Form):
    '''文章表单'''
    title = StringField(_('Title'), validators=[Required()])
    tag = StringField(_('Tags'))
    category = SelectField(_('Categories'), coerce=int)
    body = PageDownField(_("What's on your mind?"), validators=[Required()])
    submit = SubmitField(_('Submit'))

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # 在 choices 属性设置 select 控件各选项, 格式: [(选项标识符, 显示文本), ...]
        self.category.choices = [(cate.id, cate.name)
            for cate in Category.query.order_by(Category.name).all()]


class CommentForm(Form):
    '''评论表单'''
    body = TextAreaField(_('Enter your comment'), validators=[Required()])
    submit = SubmitField(_('Submit'))


class SearchForm(Form):
    '''搜索表单'''
    search = StringField('Search', validators=[Required(), Length(0, 64)])
