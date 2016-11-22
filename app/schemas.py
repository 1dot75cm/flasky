# coding: utf-8
from marshmallow import pre_load, ValidationError
from .models import (Role, User, Post, Comment, Tag, Category, BlogView, OAuth,
    OAuthType, Chrome, Package, Release)
from . import ma


USER_SCHEMA_ONLY = ('username', 'email', 'url', 'posts_url')
POST_SCHEMA_ONLY = ('title', 'timestamp', 'category', 'tags',
                    'url', 'author_url', 'comments_url')
COMMENT_SCHEMA_ONLY = ('body', 'timestamp', 'url', 'author_url', 'post_url')


class UserSchema(ma.ModelSchema):
    '''User 模型规则'''
    url = ma.Hyperlinks(ma.URLFor('api.get_user', id='<id>', _external=True), dump_only=True)
    posts_url = ma.Hyperlinks(ma.URLFor('api.get_user_posts', id='<id>', _external=True), dump_only=True)
    favorite_posts_url = ma.Hyperlinks(ma.URLFor('api.get_user_favorite_posts', id='<id>', _external=True), dump_only=True)
    followed_posts_url = ma.Hyperlinks(ma.URLFor('api.get_user_followed_posts', id='<id>', _external=True), dump_only=True)
    followers_url = ma.Hyperlinks(ma.URLFor('api.get_user_followers', id='<id>', _external=True), dump_only=True)
    following_url = ma.Hyperlinks(ma.URLFor('api.get_user_following', id='<id>', _external=True), dump_only=True)
    email = ma.String(required=True)
    username = ma.String(required=True)
    password = ma.String(required=True, load_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'confirmed', 'posts_url', 'followed_posts_url',
                  'name', 'location', 'about_me', 'member_since', 'last_seen',
                  'favorite_posts_url', 'followers_url', 'following_url', 'url')

    @pre_load
    def make_user(self, data):
        user = User.query.filter_by(email=data['email']).first()
        if user:
            raise ValidationError('User already exists')


class PostSchema(ma.ModelSchema):
    '''Post 模型规则'''
    url = ma.Hyperlinks(ma.URLFor('api.get_post', id='<id>', _external=True), dump_only=True)
    author_url = ma.Hyperlinks(ma.URLFor('api.get_user', id='<author_id>', _external=True), dump_only=True)
    comments_url = ma.Hyperlinks(ma.URLFor('api.get_post_comments', id='<id>', _external=True), dump_only=True)
    category = ma.Nested('CategorySchema', only='name')
    tags = ma.Nested('TagSchema')
    title = ma.String(required=True)
    body = ma.String(required=True)

    class Meta:
        model = Post
        fields = ('title', 'body', 'body_html', 'timestamp', 'category', 'tags',
                  'url', 'author_url', 'comments_url')

    @pre_load
    def make_post(self, data):
        if not data.get('title'):
            raise ValidationError('Post does not have a title')
        if not data.get('body'):
            raise ValidationError('Post does not have a body')


class CommentSchema(ma.ModelSchema):
    '''Comment 模型规则'''
    url = ma.Hyperlinks(ma.URLFor('api.get_comment', id='<id>', _external=True), dump_only=True)
    author_url = ma.Hyperlinks(ma.URLFor('api.get_user', id='<author_id>', _external=True), dump_only=True)
    post_url = ma.Hyperlinks(ma.URLFor('api.get_post', id='<post_id>', _external=True), dump_only=True)
    body = ma.String(required=True)

    class Meta:
        model = Comment
        fields = ('body', 'body_html', 'timestamp',
                  'url', 'author_url', 'post_url')

    @pre_load
    def make_comment(self, data):
        if not data.get('body'):
            raise ValidationError('Comment does not have a body')


class CategorySchema(ma.ModelSchema):
    '''Category 模型规则'''
    class Meta:
        model = Category


class TagSchema(ma.ModelSchema):
    '''Tag 模型规则'''
    class Meta:
        model = Tag


user_schema = UserSchema()
users_schema = UserSchema(many=True, only=USER_SCHEMA_ONLY)
post_schema = PostSchema()
posts_schema = PostSchema(many=True, only=POST_SCHEMA_ONLY)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True, only=COMMENT_SCHEMA_ONLY)


# class BlogViewSchema(ma.ModelSchema):
#     class Meta:
#         model = BlogView


# class OAuthSchema(ma.ModelSchema):
#     class Meta:
#         model = OAuth


# class OAuthTypeSchema(ma.ModelSchema):
#     class Meta:
#         model = OAuthType


# class ChromeSchema(ma.ModelSchema):
#     class Meta:
#         model = Chrome


# class PackageSchema(ma.ModelSchema):
#     class Meta:
#         model = Package


# class ReleaseSchema(ma.ModelSchema):
#     class Meta:
#         model = Release
