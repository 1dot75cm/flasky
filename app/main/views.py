# coding: utf-8
from flask import render_template
from . import main


@main.route('/')
def index():
    '''主页视图函数'''
    return render_template('index.html')
