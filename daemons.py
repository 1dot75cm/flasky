#!venv/bin/python
from __future__ import print_function
import os
import time
import daemon
import lockfile
import manage
from app import create_app, db
from config import logdir

os.environ['IS_DAEMON'] = '1'

if not os.path.exists(logdir):
    os.makedirs(logdir)

context = daemon.DaemonContext(
    umask=0o002,
    working_directory=os.getcwd(),
    stdout=open(os.path.join(logdir, "STDOUT"), 'a+'),
    stderr=open(os.path.join(logdir, "STDERR"), 'a+'),
    pidfile=lockfile.FileLock(os.path.join(logdir, "daemon.pid")))


def echo(data):
    now = time.strftime('[%y/%m/%d %H:%M:%S] ', time.localtime())
    print(now + data)


if __name__ == '__main__':
    print('Run daemon.')
    with context:
        app = create_app('default')
        ctx = app.app_context()
        ctx.push()
        while True:
            echo('Run task.')
            manage.check_karma()
            db.session.commit()
            manage.create_repo()
            echo('Task finish.')
            time.sleep(app.config['INTERVAL'])
        ctx.pop()
