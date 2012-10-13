from collections import defaultdict
import os
import random
import re
import sys
import textwrap

from fabric import state
from fabric.colors import *
from fabric.api import *
from fabric.task_utils import crawl

import puppet
import search
import cache

env.hosts = []
env.roledefs = defaultdict(list)

with hide('running'):
    hosts = local("awk '!/github|#|^$/ {print $1}' /etc/ssh/ssh_known_hosts | sort | uniq", capture=True)
    hosts = hosts.splitlines()

    if not hosts:
        warn("Couldn't read any hosts from /etc/ssh/ssh_known_hosts!")

for host in hosts:
    name, vdc, org = host.rsplit('.', 3)
    env.roledefs['all'].append(host)
    env.roledefs['org-%s' % org].append(host)
    env.roledefs['vdc-%s' % vdc].append(host)
    env.roledefs['class-%s' % name.rstrip('-1234567890')].append(host)

@task
def help(name):
    """Show extended help for a task (e.g. 'fab help:search.reindex')"""
    task = crawl(name, state.commands)

    if task is None:
        abort("%r is not a valid task name" % task)

    puts(textwrap.dedent(task.__doc__).strip())

@task
def list():
    """List known hosts"""
    puts('\n'.join(sorted(hosts)))

@task
def list_roles():
    for role in sorted(env.roledefs.keys()):
        print "%s %s" % (role, len(env.roledefs[role]))

@task
def do(command):
    """Execute arbitrary commands"""
    run(command)

@task
def sdo(command):
    """Execute arbitrary commands with sudo"""
    sudo(command)

@task
def uptime():
    """Show uptime and load"""
    run('uptime')

@task
def free():
    """Show memory stats"""
    run('free')

@task
def updates():
    """Show package counts needing updates"""
    run("cat /var/lib/update-notifier/updates-available")

@task
def upgrade():
    """Upgrade packages with apt-get"""
    sudo("apt-get update; apt-get upgrade -y")

