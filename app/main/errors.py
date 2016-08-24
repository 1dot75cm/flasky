# coding: utf-8
from flask import render_template
from . import main

@main.app_errorhandler(404)
def page_not_found(e):
    '''自定义404页面'''
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    '''自定义500页面'''
    return render_template('500.html'), 500
