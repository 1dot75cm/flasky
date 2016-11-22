# coding: utf-8
from flask import render_template, request, jsonify
from . import main


@main.app_errorhandler(403)
def forbidden(e):
    '''自定义403页面'''
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        # 内容协商, 根据客户端请求头格式改写响应
        # 为只接受 JSON 格式的客户端生成 JSON 响应
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403


@main.app_errorhandler(404)
def page_not_found(e):
    '''自定义404页面'''
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    '''自定义500页面'''
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500
