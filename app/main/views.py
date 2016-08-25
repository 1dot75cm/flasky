# coding: utf-8
from flask import render_template
from . import main
from ..models import User


@main.route('/')
def index():
    '''主页视图函数'''
    return render_template('index.html')


@main.route('/user/<username>')
def user(username):
    '''用户页视图函数'''
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)
