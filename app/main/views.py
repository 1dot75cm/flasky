# coding: utf-8
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, session, g
from flask_login import login_required, current_user
from flask_babel import gettext as _
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, SearchForm
from .. import db, cache, cache_key, cache_valid
from ..models import Permission, Role, User, Post, Comment, Tag, Category,\
    BlogView, Chrome, Package, Release
from ..decorators import admin_required, permission_required


@main.before_app_request
def before_request():
    '''记录访问信息'''
    BlogView.add_view()
    g.search_form = SearchForm()  # 表单类全局可用


@main.after_app_request
def after_request(response):
    '''记录数据库慢查询'''
    for query in get_debug_queries():  # 包含请求中执行的数据库查询相关的统计信息
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            # 若想保存日志, 必须配置日志记录器
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration, query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    '''关闭Web服务'''
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    '''搜索页面'''
    query = g.search_form.search.data or request.args.get('query', None)
    if g.search_form.validate_on_submit():
        session['allow_search'] = True  # 不允许直接用 GET 搜索
        return redirect(url_for('.search', query=query))
    if query and session.get('allow_search'):
        session['allow_search'] = False
        posts = Post.query.whoosh_search(
            query, current_app.config['MAX_SEARCH_RESULTS']).all()
        return render_template('search.html', query=query, posts=posts)
    return redirect(url_for('.index'))


@main.route('/locale/<lang>')
def set_locale(lang):
    '''设置默认语言, 保存至 session'''
    if lang in current_app.config['LANGUAGES'].keys():
        session['locale'] = lang
        session['nocache'] = True
        flash(_('Your current locale has been updated.'), 'success')
        return redirect(request.args.get('next') or url_for('main.index'))
    session['locale'] = ''
    flash(_('Invalid language code.'), 'danger')
    return redirect(request.args.get('next') or url_for('main.index'))


@main.route('/', methods=['GET', 'POST'])
@cache.memoize(timeout=600, make_name=cache_key, unless=cache_valid)
def index():
    '''主页视图函数'''
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():  # 验证用户权限和表单
        category = Category.query.filter_by(id=form.category.data).first()
        post = Post(title=form.title.data,
                    category=category,
                    body=form.body.data,
                    author=current_user._get_current_object())
                    # 使用 _get_current_object() 返回数据库需要的实际用户对象
                    # 更新 body 字段后, 会自动调用 on_changed_body 渲染 HTML
        db.session.add(post)
        Tag.process_tag(post, form.tag.data)
        flash(_('Your article has been updated.'), 'success')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)  # 默认第一页
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts  # 查询关注用户的文章
    else:
        query = Post.query  # 查询所有文章
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)  # 按时间戳排序, 查询某页数据
        # paginate(页数, per_page每页项数, error_out页数超出范围返回404)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/user/<username>')
@cache.memoize(timeout=600, make_name=cache_key, unless=cache_valid)
def user(username):
    '''用户页视图函数'''
    user = User.query.filter_by(username=username).first_or_404()
    user.add_view()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)  # 通过关系查询用户发布的文章, 按时间戳排序, 查询某页数据
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/user/<username>/favorites')
@cache.memoize(timeout=1800, make_name=cache_key, unless=cache_valid)
def get_favorite_posts(username):
    '''用户收藏页视图'''
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.favorite_posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('favorite_posts.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    '''编辑用户页视图函数'''
    form = EditProfileForm()
    if form.validate_on_submit():  # 验证表单
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash(_('Your profile has been updated.'), 'success')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    '''管理员编辑用户页视图函数'''
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash(_('The profile has been updated.'), 'success')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
@cache.memoize(timeout=600, make_name=cache_key, unless=cache_valid)
def post(id):
    '''文章页视图函数'''
    post = Post.query.get_or_404(id)
    post.add_view()
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash(_('Your comment has been published.'), 'success')
        return redirect(url_for('.post', id=post.id, page=-1))  # -1 请求评论的最后一页
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1  # 计算最后一页页数
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)  # 传入列表为了复用 _posts.html 模板


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    '''编辑文章视图函数'''
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)  # 当前用户不是作者, 且不是管理员, 则拒绝编辑
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.category = Category.query.get(form.category.data)
        post.body = form.body.data
        db.session.add(post)
        Tag.process_tag(post, form.tag.data)
        flash(_('The post has been updated.'), 'success')
        return redirect(url_for('.post', id=post.id))
    form.title.data = post.title
    form.tag.data = ', '.join([tag.name for tag in post.tags.all()])
    form.category.data = post.category_id
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)  # 检查关注权限
def follow(username):
    '''关注用户'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'), 'danger')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash(_('You are already following this user.'), 'warning')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash(_('You are now following %(username)s.', username=username), 'success')
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    '''取消关注用户'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'), 'danger')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash(_('You are not following this user.'), 'warning')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash(_('You are not following %(username)s anymore.', username=username), 'success')
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
@cache.memoize(timeout=1800, make_name=cache_key, unless=cache_valid)
def followers(username):
    '''关注者视图, 关注该用户的账户'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'), 'danger')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='Followers of',
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
@cache.memoize(timeout=1800, make_name=cache_key, unless=cache_valid)
def followed_by(username):
    '''被关注者视图, 该用户关注的账户'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'), 'danger')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='Followed by',
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    '''设置cookie, 查询所有文章'''
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)  # 不指定max_age, 关闭浏览器cookie就失效
    return resp


@main.route('/followed')
@login_required
def show_followed():
    '''设置cookie, 查询关注用户的文章'''
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@cache.memoize(timeout=60, make_name=cache_key, unless=cache_valid)
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    '''管理评论视图'''
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    '''启用评论'''
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    '''禁用评论'''
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/tags')
@main.route('/tags/<int:id>')
@cache.memoize(timeout=600, make_name=cache_key, unless=cache_valid)
def get_tag(id=None):
    '''标签相关文章'''
    tags = Tag.query.all()
    tag = Tag.query.filter_by(id=id).first()
    if tag is None:
        query = Post.query
    else:
        query = tag.posts
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('tags.html', tag=tag, tags=tags,
                           posts=posts, pagination=pagination)


@main.route('/categories')
@main.route('/categories/<int:id>')
@cache.memoize(timeout=600, make_name=cache_key, unless=cache_valid)
def get_category(id=None):
    '''分类相关文章'''
    categories = Category.query.all()
    category = Category.query.filter_by(id=id).first()
    if category is None:
        query = Post.query
    else:
        query = category.posts
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('categories.html', category=category, categories=categories,
                           posts=posts, pagination=pagination)


@main.route('/favorites/<int:id>')
@cache.memoize(timeout=600, make_name=cache_key, unless=cache_valid)
def get_favorite_users(id):
    '''收藏文章的用户'''
    post = Post.query.filter_by(id=id).first()
    page = request.args.get('page', 1, type=int)
    pagination = post.favorite_users.order_by(User.username.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    users = pagination.items
    return render_template('favorite_users.html', users=users, post=post,
                           pagination=pagination)


@main.route('/favorites/<int:id>/follow')
@login_required
def add_favorite(id):
    '''收藏文章'''
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash(_('Invalid post.'), 'danger')
        return redirect(url_for('.index'))
    if current_user.is_favorite(post):
        flash(_('You are already favorite this post.'), 'warning')
        return redirect(url_for('.user', username=current_user.username))
    current_user.add_favorite(post)
    flash(_('You are now favorite <%(post)s>.', post=post.title), 'success')
    return redirect(url_for('.user', username=current_user.username))


@main.route('/favorites/<int:id>/unfollow')
@login_required
def del_favorite(id):
    '''取消收藏'''
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash(_('Invalid post.'), 'danger')
        return redirect(url_for('.index'))
    if not current_user.is_favorite(post):
        flash(_('You are not favorite this post.'), 'warning')
        return redirect(url_for('.user', username=current_user.username))
    current_user.del_favorite(post)
    flash(_('You are not favorite <%(post)s> anymore.', post=post.title), 'success')
    return redirect(url_for('.user', username=current_user.username))


@main.route('/tools/chrome')
@cache.memoize(timeout=600, make_name=cache_key, unless=cache_valid)
def get_chrome():
    '''获取chrome版本'''
    platform = ['win', 'mac', 'linux']
    archs = ['x86', 'x64']
    channels = ['stable', 'beta', 'dev', 'canary']

    cache = request.args.get('cache', True)
    if cache in ['0', 'false']:
        cache = False
    system = request.args.get('os', platform)
    arch = request.args.get('arch', archs)
    channel = request.args.get('channel', channels)

    tab_type = system if type(system) == unicode else None
    system = [system] if type(system) == unicode else system
    arch = [arch] if type(arch) == unicode else arch
    channel = [channel] if type(channel) == unicode else channel

    if system[0] in platform and arch[0] in archs and channel[0] in channels:
        pkgs, cache = Chrome.check_update(system, channel, arch, cache)
        return render_template('chrome.html', pkgs=pkgs, cache=cache, tab=tab_type)
    else:
        abort(404)


@main.route('/tools/updates/')
@cache.memoize(timeout=60, make_name=cache_key, unless=cache_valid)
def get_rpm_items():
    '''RPM包列表视图'''
    page = request.args.get('page', 1, type=int)
    release = request.args.get('release', 'F24')
    status = request.args.get('status', '')

    releases = Release.query.all()
    if release:
        _release = Release.query.filter_by(name=release).first()
    _query = _release.packages if _release else Package.query
    query = _query.order_by(Package.timestamp.desc()).filter_by(status=status) \
        if status else \
            _query.order_by(Package.timestamp.desc())
    pagination = query.paginate(
        page, per_page=current_app.config['FLASKY_PKGS_PER_PAGE'],
        error_out=False)
    pkgs = pagination.items
    return render_template('rpm_items.html', pkgs=pkgs, pagination=pagination,
                           tab=release, releases=releases)


@main.route('/tools/updates/<id>', methods=['GET', 'POST'])
@cache.memoize(timeout=60, make_name=cache_key, unless=cache_valid)
def get_rpm_task(id):
    '''RPM包视图'''
    package = Package.query.filter_by(task_id=id).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          package=package,
                          author=current_user._get_current_object())
        package.set_karma(form.body.data)
        db.session.add(comment)
        flash(_('Your comment has been published.'), 'success')
        return redirect(url_for('.get_rpm_task', id=package.task_id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (package.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1  # 计算最后一页页数
    pagination = package.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('rpm_vote.html', pkg=package, form=form,
                           comments=comments, pagination=pagination)
