# coding: utf-8
from flask import render_template, redirect, request, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import gettext as _
from . import auth
from .. import db, fas, cache, cache_valid
from ..models import User, OAuthType
from ..email import send_email
from .forms import LoginForm, RegistrationForm, ChangePasswordForm,\
    PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm


@auth.before_app_request
def before_request():
    '''过滤未验证账户, 更新已登陆用户访问时间'''
    if current_user.is_authenticated:
        current_user.ping()  # 每次已登陆用户发送请求, 更新访问时间
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
@cache.cached(timeout=1800, unless=cache_valid)
def unconfirmed():
    '''未验证账户视图'''
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    '''用户登陆视图'''
    form = LoginForm()
    oauths = OAuthType.query.all()
    if form.validate_on_submit():  # 验证表单
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)  # 在会话中标记用户为已登陆
            flash(_('Hello, %(username)s.', username=user.username), 'success')
            return redirect(request.args.get('next') or url_for('main.index'))
        flash(_('Invalid username or password.'), 'danger')
    return render_template('auth/login.html', form=form,
                           oauths=oauths, next=request.referrer)


@auth.route('/logout')
@login_required
def logout():
    '''退出登陆视图'''
    logout_user()  # 删除用户会话
    if g.fas_user:
        fas.logout()
    flash(_('You have been logged out.'), 'success')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    '''用户注册视图'''
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()  # 生成确认令牌需要用到用户ID, 在此提交
        # 新用户写入数据库后, 需要在重定向前发送确认邮件
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
        flash(_('A confirmation email has been sent to you by email.'), 'warning')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    '''确认令牌视图'''
    if current_user.confirmed:  # 当前用户已确认
        return redirect(url_for('main.index'))
    if current_user.confirm(token):  # 验证令牌
        flash(_('You have confirmed your account. Thanks!'), 'success')
    else:
        flash(_('The confirmation link is invalid or has expired.'), 'warning')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    '''重新发送确认邮件'''
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash(_('A new confirmation email has been sent to you by email.'), 'warning')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    '''修改密码视图'''
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash(_('Your password has been updated.'), 'success')
            return redirect(url_for('main.index'))
        else:
            flash(_('Invalid password.'), 'danger')
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    '''请求密码重置视图(忘记密码)'''
    if not current_user.is_anonymous:  # 用户已登陆
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():  # 验证表单
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()  # 生成token
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))  # 发送重置密码邮件
            flash(_('An email with instructions to reset your password has been'
                  ' sent to you.'), 'warning')
            return redirect(url_for('auth.login'))
        else:
            flash(_('Email address is unknown.'), 'warning')
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    '''密码重置视图(忘记密码)'''
    if not current_user.is_anonymous:  # 用户已登陆
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():  # 验证表单
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):  # token验证通过, 则重置密码
            flash(_('Your password has been updated.'), 'success')
        else:
            flash(_('Your password has been update failed.'), 'warning')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    '''请求修改邮箱视图'''
    form = ChangeEmailForm()
    if form.validate_on_submit():  # 验证表单
        if current_user.verify_password(form.password.data):  # 验证密码
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       user=current_user, token=token)  # 发送邮件
            flash(_('An email with instructions to confirm your new email '
                  'address has been sent to you.'), 'warning')
            return redirect(url_for('main.index'))
        else:
            flash(_('Invalid email or password.'), 'danger')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    '''修改邮箱视图'''
    if current_user.change_email(token):
        flash(_('Your email address has been updated.'), 'success')
    else:
        flash(_('Invalid request.'), 'danger')
    return redirect(url_for('main.index'))
