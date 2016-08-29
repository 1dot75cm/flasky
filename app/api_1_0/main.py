# coding: utf-8
from flask import jsonify, url_for
from . import api

@api.route('/')
def main():
    '''API列表'''
    return jsonify({
        'message': 'Hello, Fedora.',
        'version': 'v1.0',
        'apis': {
            'token': url_for('.get_token', _external=True),
            'users': url_for('.get_users', _external=True),
            'posts': url_for('.get_posts', _external=True),
            'comments': url_for('.get_comments', _external=True)}
        })
