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
import vm

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
    """List available roles"""
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
