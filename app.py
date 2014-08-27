from fabric.api import *

@task
def restart(app):
    """Restart (hard) a particular app"""
    sudo("service %s restart" % app)

@task
def reload(app):
    """Reload (graceful) a particular app"""
    sudo("service %s reload" % app)
