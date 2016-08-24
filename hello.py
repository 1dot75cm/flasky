# coding: utf-8
from datetime import datetime
from flask import Flask, render_template
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_moment import Moment

app = Flask(__name__)  # 实例化app
manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

@app.errorhandler(404)
def page_not_found(e):
    '''自定义404页面'''
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    '''自定义500页面'''
    return render_template('500.html'), 500

@app.route('/')
def index():
    '''主页视图函数'''
    return render_template('index.html',
                           current_time=datetime.utcnow())

@app.route('/user/<name>')
def user(name):
    '''User视图函数'''
    return render_template('user.html', name=name)

if __name__ == '__main__':
    manager.run()
