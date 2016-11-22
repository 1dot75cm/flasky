# coding: utf-8
from flask import jsonify, request, g, url_for
from .. import db, cache
from ..models import Post, Permission
from ..schemas import post_schema, posts_schema
from . import api
from .decorators import permission_required
from .errors import forbidden
from .utils import get_data


@api.route('/posts/')
@cache.memoize(timeout=600)
def get_posts():
    '''获取文章列表'''
    query = Post.query
    items, prev, next, total = get_data(
        query, posts_schema, 'api.get_posts')
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/posts/<int:id>')
@cache.memoize(timeout=600)
def get_post(id):
    '''获取文章'''
    post = Post.query.get_or_404(id)
    return post_schema.jsonify(post)


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    '''创建新文章'''
    json_data = request.get_json()
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    post, errors = post_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return post_schema.jsonify(post), 201, \
        {'Location': url_for('api.get_post', id=post.id, _external=True)}


@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    '''编辑文章'''
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Insufficient permissions')
    post.title = request.json.get('title', post.title)
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    return post_schema.jsonify(post)
