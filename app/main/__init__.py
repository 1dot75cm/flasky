# coding: utf-8
from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_permissions():
    '''将权限常量注入模板上下文, 避免每次渲染模板都需要添加参数'''
    return dict(Permission=Permission)
