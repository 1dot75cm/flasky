# coding: utf-8
from flask import Flask
app = Flask(__name__)  # 实例化app

@app.route('/')
def index():
    '''主页视图函数'''
    return '<h1>Hello, Flask!</h1>'

@app.route('/user/<name>')
def user(name):
    '''User视图函数'''
    return '<h1>Hello, %s!</h1>' % name

if __name__ == '__main__':
    app.run(debug=True)
