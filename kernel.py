from fabric.api import *

@task
@parallel(pool_size=10)
def show_unused():
    """Show unused kernels using govuk_unused_kernels"""
    run('govuk_unused_kernels')

@task
@parallel(pool_size=10)
def remove_unused():
    """Remove unused kernels"""
    sudo('govuk_unused_kernels | xargs apt-get purge -y')
