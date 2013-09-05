from fabric.api import *

@task
def gracefulstop(wait=True):
    """Gracefully shutdown Nginx by finishing any in-flight requests"""
    sudo('nginx -s quit')

    if wait:
        # Poll for Nginx, until it's no longer running.
        run('while pgrep nginx >/dev/null; do echo "Waiting for Nginx to exit.."; sleep 1; done')

@task
def killnginx():
    """Shut down Nginx immediately without waiting for it to finish running"""
    sudo('service nginx stop')

@task
def gracefulstart():
    """Start up Nginx on a machine"""
    sudo('service nginx start')

@task
def hello_it():
    """Turns Nginx off and on again"""
    killnginx()
    gracefulstart()
