# coding: utf-8
from flask import request, current_app, url_for


def get_data(base_query, model_schema, endpoint, id=None, type='post'):
    '''获取 model 信息'''
    config_type = {
        'post': current_app.config['FLASKY_POSTS_PER_PAGE'],
        'comment': current_app.config['FLASKY_COMMENTS_PER_PAGE']
    }

    page = request.args.get('page', 1, type=int)
    pagination = base_query.paginate(
        page, per_page=config_type[type],
        error_out=False)
    items = model_schema.dump(pagination.items)

    # 生成 url
    prev = None
    if pagination.has_prev:
        prev = url_for(endpoint, page=page-1, id=id, _external=True)
    next = None
    if pagination.has_next:
        next = url_for(endpoint, page=page+1, id=id, _external=True)
    return (items, prev, next, pagination.total)
