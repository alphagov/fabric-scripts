from fabric.api import *

@task
def show_unused():
    """Show unused kernels using govuk_unused_kernels"""
    run('govuk_unused_kernels')

@task
def remove_unused():
    """Remove unused kernels"""
    sudo('govuk_unused_kernels | xargs apt-get purge -y')
