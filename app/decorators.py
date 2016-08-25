# coding: utf-8
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


def permission_required(permission):
    '''检查一般权限'''
    def decorator(func):
        @wraps(func)  # 将传入函数的 __name__ 等属性复制到 decorated_function 函数
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)  # 如果用户不具有指定权限, 则返回403
            return func(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(func):
    '''检查管理员权限'''
    return permission_required(Permission.ADMINISTER)(func)
