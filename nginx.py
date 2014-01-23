from fabric.api import *

@task
def gracefulstop(wait=True):
    """Gracefully shutdown Nginx by finishing any in-flight requests"""
    sudo('nginx -s quit')

    if wait:
        # Poll for Nginx, until it's no longer running.
        run('while pgrep nginx >/dev/null; do echo "Waiting for Nginx to exit.."; sleep 1; done')

@task
def disable_vhost(vhost_filename):
    """Disable a vhost by removing its symlink from /etc/nginx/sites-enabled"""
    sudo('rm -f /etc/nginx/sites-enabled/%s' % vhost_filename)

@task
def kill():
    """Shut down Nginx immediately without waiting for it to finish running"""
    sudo('service nginx stop')

@task
def start():
    """Start up Nginx on a machine"""
    sudo('service nginx start')

@task
def hello_it():
    """Turns Nginx off and on again"""
    kill()
    start()
