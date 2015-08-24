from fabric.api import *

@task(default=True)
def check(*args):
    """Run rkhunter on the machine"""
    sudo('/etc/cron.daily/rkhunter-passive-check')

@task
def propupdate(*args):
    """Update rkhunter file property database on the machine"""
    sudo('/usr/bin/rkhunter --propupdate')
