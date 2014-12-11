from fabric.api import *
from fabric.decorators import serial

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


@task
@serial
@with_settings(warn_only=False)
def rolling_stop_start(app):
    """Perform a sequential forced reload of an app that stops at first failure"""
    stop(app)
    start(app)

def _service(app, command):
    sudo('service {} {}'.format(app, command))

@task
@runs_once
@roles('class-whitehall_backend')
def overdue_scheduled_publications():
    with cd('/var/apps/whitehall'):
        sudo('govuk_setenv whitehall bundle exec rake publishing:overdue:list', user='deploy')

@task
@runs_once
@roles('class-whitehall_backend')
def schedule_publications():
    with cd('/var/apps/whitehall'):
        sudo('govuk_setenv whitehall bundle exec rake publishing:overdue:publish', user='deploy')
