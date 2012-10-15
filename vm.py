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

@task
def stopped_govuk_jobs():
    """Find stopped govuk application jobs"""
    with hide('running'):
        run('grep -l govuk_spinup /etc/init/*.conf | xargs -n1 basename | while read line; do sudo status "${line%%.conf}"; done | grep stop')
