# coding: utf-8
from flask import jsonify, request
from . import api
from .utils import get_data
from .. import cache, db
from ..models import User, Post, Follow
from ..schemas import user_schema, users_schema, posts_schema


@api.route('/users/')
@cache.memoize(timeout=600)
def get_users():
    '''获取用户列表'''
    query = User.query
    items, prev, next, total = get_data(
        query, users_schema, 'api.get_users')
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/users/', methods=['POST'])
def new_user():
    '''创建新用户'''
    json_data = request.get_json()
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    user, errors = user_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    db.session.add(user)
    db.session.commit()
    result = user_schema.dump(user)
    return jsonify({
        'message': 'Created new user.',
        'self': result.data
    }), 201


@api.route('/users/<int:id>')
@cache.memoize(timeout=600)
def get_user(id):
    '''获取用户'''
    user = User.query.get_or_404(id)
    return user_schema.jsonify(user)


@api.route('/users/<int:id>/posts/')
@cache.memoize(timeout=600)
def get_user_posts(id):
    '''获取用户的文章列表'''
    user = User.query.get_or_404(id)
    query = user.posts.order_by(Post.timestamp.desc())
    items, prev, next, total = get_data(
        query, posts_schema, 'api.get_user_posts', id)
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/users/<int:id>/timeline/')
@cache.memoize(timeout=600)
def get_user_followed_posts(id):
    '''获取被关注用户的文章列表'''
    user = User.query.get_or_404(id)
    query = user.followed_posts.order_by(Post.timestamp.desc())
    items, prev, next, total = get_data(
        query, posts_schema, 'api.get_user_followed_posts', id)
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/users/<int:id>/favorite/')
@cache.memoize(timeout=600)
def get_user_favorite_posts(id):
    '''获取用户收藏文章'''
    user = User.query.get_or_404(id)
    query = user.favorite_posts.order_by(Post.timestamp.desc())
    items, prev, next, total = get_data(
        query, posts_schema, 'api.get_user_favorite_posts', id)
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/users/<int:id>/followers/')
@cache.memoize(timeout=600)
def get_user_followers(id):
    '''获取用户粉丝'''
    user = User.query.get_or_404(id)
    query = User.query.join(Follow, Follow.follower_id == User.id)\
        .filter(Follow.followed_id == user.id)
    items, prev, next, total = get_data(
        query, users_schema, 'api.get_user_followers', id)
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })


@api.route('/users/<int:id>/following/')
@cache.memoize(timeout=600)
def get_user_following(id):
    '''获取受关注的用户'''
    user = User.query.get_or_404(id)
    query = User.query.join(Follow, Follow.followed_id == User.id)\
        .filter(Follow.follower_id == user.id)
    items, prev, next, total = get_data(
        query, users_schema, 'api.get_user_following', id)
    return jsonify({
        'self': items.data,
        'prev': prev,
        'next': next,
        'count': total
    })
