# coding: utf-8
from flask import jsonify
from app.exceptions import ValidationError
from . import api


def bad_request(message):
    '''400错误辅助函数'''
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    '''401错误辅助函数'''
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    '''403错误辅助函数'''
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


@api.errorhandler(ValidationError)  # 只要抛出该异常, 就调用被修饰的函数
def validation_error(e):
    '''ValidationError异常处理函数'''
    return bad_request(e.args[0])
