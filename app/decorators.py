# coding: utf-8
from datetime import datetime
from functools import wraps, update_wrapper
from flask import abort, make_response
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


# http://arusahni.net/blog/2014/03/flask-nocache.html
def nocache(func):
    '''添加缓存头, 使浏览器缓存失效'''
    @wraps(func)
    def decorated_function(*args, **kwargs):
        response = make_response(func(*args, **kwargs))
        response.last_modified = datetime.now()  # Last-Modified
        response.expires = -1  # Expires
        response.cache_control.max_age = 0  # max-age
        response.cache_control.no_cache = True  # no-cache
        response.cache_control.no_store = True  # no-store
        response.cache_control.must_revalidate = True  # must-revalidate
        response.headers['Cache-Control'] += ', post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        return response
    return update_wrapper(decorated_function, func)  # 从原包装函数复制属性
