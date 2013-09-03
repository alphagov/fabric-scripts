from fabric.api import *

@task
def gracefulstop(wait=True):
    """Gracefully shutdown Nginx by finishing any in-flight requests"""
    sudo('nginx -s quit')

    if wait:
        # Poll for Nginx, until it's no longer running.
        run('while pgrep nginx >/dev/null; do echo "Waiting for Nginx to exit.."; sleep 1; done')

@task
def gracefulstart():
    """Start up Nginx on a machine"""
    sudo('service nginx start')

@task
def hello_it():
    """Turns Nginx off and on again"""
    gracefulstop()
    gracefulstart()
