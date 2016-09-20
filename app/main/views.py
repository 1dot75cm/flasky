# coding: utf-8
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from .. import db
from ..models import Permission, Role, User, Post
from ..decorators import admin_required


@main.route('/', methods=['GET', 'POST'])
def index():
    '''主页视图函数'''
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():  # 验证用户权限和表单
        post = Post(title=form.title.data,
                    body=form.body.data,
                    author=current_user._get_current_object())
                    # 使用 _get_current_object() 返回数据库需要的实际用户对象
        db.session.add(post)
        flash('Your article has been updated.')
        return redirect(url_for('.index'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()  # 按时间戳降序排列文章
    return render_template('index.html', form=form, posts=posts)


@main.route('/user/<username>')
def user(username):
    '''用户页视图函数'''
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    '''编辑用户页视图函数'''
    form = EditProfileForm()
    if form.validate_on_submit():  # 验证表单
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    '''管理员编辑用户页视图函数'''
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
