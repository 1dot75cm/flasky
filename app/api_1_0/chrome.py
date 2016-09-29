# coding: utf-8
import time
from flask import jsonify, request, abort
from ..models import Chrome
from .. import cache
from . import api


@api.route('/chrome')
@cache.memoize(timeout=600)
def get_chrome():
    '''获取chrome版本'''
    platform = ['win', 'mac', 'linux']
    archs = ['x86', 'x64']
    channels = ['stable', 'beta', 'dev', 'canary']

    cache = request.args.get('cache', False)
    if cache in ['0', 'false']:
        cache = False
    system = request.args.get('os', platform)
    arch = request.args.get('arch', archs)
    channel = request.args.get('channel', channels)

    system = [system] if type(system) == unicode else system
    arch = [arch] if type(arch) == unicode else arch
    channel = [channel] if type(channel) == unicode else channel

    if system[0] in platform and arch[0] in archs and channel[0] in channels:
        pkgs, cache = Chrome.check_update(system, channel, arch, cache)
        pkglist = []
        for pkg in pkgs:
            pkglist.append(dict(
                name=pkg.name,
                version=pkg.version,
                os=pkg.os,
                arch=pkg.arch,
                channel=pkg.channel,
                size=pkg.size,
                sha256=pkg.hash,
                urls=pkg.urls.split(','),
                timestamp=time.mktime(pkg.timestamp.timetuple())))
        return jsonify({'results': pkglist, 'cache': cache})
    else:
        abort(404)
