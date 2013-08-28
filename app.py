from fabric.api import *

@task
def restart(app):
    """Restart a particular app"""
    sudo("service %s restart" % app)
