# coding: utf-8
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from flask_babel import lazy_gettext as _  # 直到渲染表单时, 才惰性翻译文本
from ..models import User


class LoginForm(Form):
    '''登陆表单'''
    email = StringField(_('Email'), validators=[Required(), Length(1, 64), Email()])
    password = PasswordField(_('Password'), validators=[Required()])
    remember_me = BooleanField(_('Keep me logged in'))
    submit = SubmitField(_('Log In'))


class RegistrationForm(Form):
    '''注册表单'''
    email = StringField(_('Email'), validators=[Required(), Length(1, 64), Email()])
    username = StringField(_('Username'), validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                        _('Usernames must have only letters, '
                                          'numbers, dots or underscores'))])
    password = PasswordField(_('Password'), validators=[
        Required(), EqualTo('password2', message=_('Passwords must match.'))])
    password2 = PasswordField(_('Confirm password'), validators=[Required()])
    submit = SubmitField(_('Register'))

    def validate_email(self, field):
        '''附加验证; 验证email无重复'''
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))

    def validate_username(self, field):
        '''附加验证; 验证username无重复'''
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(_('Username already in use.'))


class ChangePasswordForm(Form):
    '''修改密码表单'''
    old_password = PasswordField(_('Old password'), validators=[Required()])
    password = PasswordField(_('New password'), validators=[
        Required(), EqualTo('password2', message=_('Passwords must match.'))])
    password2 = PasswordField(_('Confirm new password'), validators=[Required()])
    submit = SubmitField(_('Update Password'))


class PasswordResetRequestForm(Form):
    '''请求重设密码表单'''
    email = StringField(_('Email'), validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField(_('Reset Password'))


class PasswordResetForm(Form):
    '''重设密码表单'''
    email = StringField(_('Email'), validators=[Required(), Length(1, 64), Email()])
    password = PasswordField(_('New password'), validators=[
        Required(), EqualTo('password2', message=_('Passwords must match.'))])
    password2 = PasswordField(_('Confirm password'), validators=[Required()])
    submit = SubmitField(_('Reset Password'))

    def validate_email(self, field):
        '''验证确保邮箱地址存在'''
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(_('Unknown email address.'))


class ChangeEmailForm(Form):
    '''修改Email表单'''
    email = StringField(_('New Email'), validators=[Required(), Length(1, 64), Email()])
    password = PasswordField(_('Password'), validators=[Required()])
    submit = SubmitField(_('Update Email Address'))

    def validate_email(self, field):
        '''验证确保邮箱地址不存在'''
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))
