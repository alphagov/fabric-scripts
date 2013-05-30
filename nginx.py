from fabric.api import *

@task
def gracefulstop(*args):
    """Gracefully shutdown Nginx by finishing any in-flight requests"""
    sudo('nginx -s quit')
