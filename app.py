import re

from fabric.api import abort, sudo, task, run


@task
def restart(app):
    """Restart a particular app"""
    _service(app, 'restart')


@task
def reload(app):
    """Reload a particular app.

    Unlike `restart`, this will tell the app to reload itself gracefully; for
    apps running under unicornherder, this will spin up a new process, then
    stop the old one after a short overlap period.

    """
    _service(app, 'reload')


@task
def stop(app):
    """Stop a particular app"""
    _service(app, 'stop')


@task
def start(app):
    """Start a particular app"""
    _service(app, 'start')


@task
def status(app):
    """Check status of a particular app"""
    _service(app, 'status')


def _service(app, command):
    sudo('service {} {}'.format(app, command))


@task
def respawn_large_unicorns(app):
    """Gracefully kill the unicorn worker using the most RAM for a particular app"""
    master_pid = run('cat /var/run/{}/app.pid'.format(app))
    if not re.match('^unicorn master', run('cat /proc/{}/cmdline'.format(master_pid))):
        abort('App not running unicorn')

    sudo("kill -QUIT $(ps -o rss,pid --ppid %s --sort +rss | tail -n1 | awk '{print $2}')" % master_pid)
