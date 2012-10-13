from fabric.api import *

@task
def uptime():
    """Show uptime and load"""
    run('uptime')

@task
def free():
    """Show memory stats"""
    run('free')

@task
def disk():
    """Show disk usage"""
    run('df -kh')

@task
def updates():
    """Show package counts needing updates"""
    run("cat /var/lib/update-notifier/updates-available")

@task
def upgrade():
    """Upgrade packages with apt-get"""
    sudo("apt-get update; apt-get upgrade -y")
