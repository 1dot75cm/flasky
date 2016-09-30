# coding: utf-8
from flask import jsonify, url_for, request, send_file, abort
from . import api
from .errors import bad_request
from .. import cache, qrcode

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
            'comments': url_for('.get_comments', _external=True),
            'chrome': url_for('.get_chrome', _external=True),
            'qrcode': url_for('.get_qrcode', _external=True)}
        })


@api.route('/qrcode', methods=['GET', 'POST'])
@cache.memoize(timeout=20)
def get_qrcode():
    '''生成二维码'''
    _request = request.args or request.json
    url = _request.get('url', None)           # 数据
    version = _request.get('version', None)   # 图片尺寸
    correct = _request.get('correct', 'L')    # 纠错级别
    box_size = _request.get('box_size', 10)   # 像素大小
    border = _request.get('border', 1)        # 边框大小
    fcolor = _request.get('fcolor', 'black')  # 前景色
    bcolor = _request.get('bcolor', 'white')  # 背景色
    factor = _request.get('factor', 4)        # 小图标是二维码的 1/4
    icon = _request.get('icon', 'fedora.png') # 小图标
    box = _request.get('box', None)           # 小图标位置 "left, top"
    box = box.split(',') if box else None

    try:
        if url is None:
            raise ValueError('Need some value')
        data = qrcode.qrcode(url, mode='raw', version=version, error_correction=correct,
                             box_size=box_size, border=border, fill_color=fcolor,
                             back_color=bcolor, factor=factor, icon_img=icon, box=box)
    except:
        return bad_request('value error')
    return send_file(data, mimetype='image/png', cache_timeout=0)
