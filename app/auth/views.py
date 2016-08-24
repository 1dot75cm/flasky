# coding: utf-8
from flask import render_template
from . import auth


@auth.route('/login')
def login():
    '''用户登陆视图'''
    return render_template('auth/login.html')
