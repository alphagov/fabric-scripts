from fabric.api import *


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


def _service(app, command):
    sudo('service {} {}'.format(app, command))
