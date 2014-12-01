from fabric.api import *


@task
def restart(app):
    """Restart a particular app"""
    _service(app, 'restart')


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
