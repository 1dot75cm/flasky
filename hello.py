# coding: utf-8
from flask import Flask, render_template
from flask_script import Manager

app = Flask(__name__)  # 实例化app
manager = Manager(app)

@app.route('/')
def index():
    '''主页视图函数'''
    return render_template('index.html')

@app.route('/user/<name>')
def user(name):
    '''User视图函数'''
    return render_template('user.html', name=name)

if __name__ == '__main__':
    manager.run()
