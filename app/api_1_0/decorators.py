# coding: utf-8
from functools import wraps
from flask import g
from .errors import forbidden


def permission_required(permission):
    '''检查一般权限'''
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return func(*args, **kwargs)
        return decorated_function
    return decorator
