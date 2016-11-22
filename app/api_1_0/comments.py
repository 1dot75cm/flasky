# coding: utf-8
from flask import jsonify, request, g, url_for
from .. import db, cache
from ..models import Post, Permission, Comment
from ..schemas import comment_schema, comments_schema
from . import api
from .decorators import permission_required
from .utils import get_data


@api.route('/comments/')
@cache.memoize(timeout=600)
def get_comments():
    '''获取评论列表'''
    query = Comment.query.order_by(Comment.timestamp.desc())
    items, prev, next, total = get_data(
        query, comments_schema, 'api.get_comments', type='comment')
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/comments/<int:id>')
@cache.memoize(timeout=600)
def get_comment(id):
    '''获取评论'''
    comment = Comment.query.get_or_404(id)
    return comment_schema.jsonify(comment)


@api.route('/posts/<int:id>/comments/')
@cache.memoize(timeout=600)
def get_post_comments(id):
    '''获取文章的评论列表'''
    post = Post.query.get_or_404(id)
    query = post.comments.order_by(Comment.timestamp.asc())
    items, prev, next, total = get_data(
        query, comments_schema, 'api.get_post_comments', type='comment')
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/posts/<int:id>/comments/', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_post_comment(id):
    '''为文章撰写新评论'''
    post = Post.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    comment, errors = comment_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    return comment_schema.jsonify(comment), 201, \
        {'Location': url_for('api.get_comment', id=comment.id,
                             _external=True)}
