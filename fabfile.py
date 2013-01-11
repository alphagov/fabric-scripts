from collections import defaultdict
from socket import gethostname
import json
import os
import random
import re
import sys
import textwrap
import urllib
import urllib2

from fabric import state
from fabric.colors import *
from fabric.api import *
from fabric.task_utils import crawl

# Our command submodules
import cache
import licensify
import mongo
import puppet
import search
import vm

env.hosts = []
env.roledefs = defaultdict(list)

if re.match('^jumpbox', gethostname()) is None:
  print "govuk_fab is designed to run from a jumpbox"
  sys.exit(1)

with hide('running'):
    qs = urllib.urlencode({'query': '["=", ["node", "active"], true]'})
    req = urllib2.urlopen('http://puppet-1.management.production/nodes?{0}'.format(qs))
    hosts = json.load(res)

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
      print "%-30.30s : %s" % (role, len(env.roledefs[role]))

@task
def do(command):
    """Execute arbitrary commands"""
    run(command)

@task
def sdo(command):
    """Execute arbitrary commands with sudo"""
    sudo(command)
