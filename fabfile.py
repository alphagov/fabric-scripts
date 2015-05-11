from __future__ import print_function

from collections import defaultdict
from hashlib import md5
import os
import re
import textwrap
import time

from fabric import state
from fabric.api import (abort, env, get, hide, hosts, local, puts, run,
                        runs_once, serial, settings, sudo, task, warn)
from fabric.task_utils import crawl

# Our command submodules
import app
import apt
import cache
import campaigns
import cdn
import elasticsearch
import graphite
import incident
import licensify
import locksmith
import logstream
import mongo
import mainstream_slugs
import mysql
import nagios
import nginx
import ntp
import puppet
import rabbitmq
import rkhunter
import search
import statsd
import topic_change
import vm
import whitehall

HERE = os.path.dirname(__file__)
SSH_DIR = os.path.join(HERE, '.ssh')

# How old a local hosts file can be before we check for an update
HOSTS_FILE_CACHE_TIME = 3600 * 24

ABORT_MSG = textwrap.dedent("""
    You must select an environment before running this task, e.g.

        fab production [task, [task, [...]]]

    If you've called fabric with the -R flag, please instead use one of the
    following tasks to select a set of machines:

        all
        class:<classname>
        vdc:<vdcname>

    For example:

        fab production class:cache do:uname

    To find a list of available classes and VDCs, you can run

        fab production classes
        fab production vdcs
    """)

class RoleFetcher(object):
    """
    RoleFetcher is a helper class, an instance of which can be bound to the
    Fabric env.roledefs setting. It allows lazy lookup of host names by machine
    class and vDC.
    """

    def __init__(self):
        self.hosts = None
        self.roledefs = defaultdict(list)
        self.classes = set()
        self.vdcs = set()
        self.fetched = False

    def fetch(self):
        if self.fetched:
            return

        self.hosts = _fetch_hosts()

        for host in self.hosts:
            try:
                name, vdc, _ = host.split('.', 3)
            except ValueError:
                warn("discarding badly formatted hostname '{0}'".format(host))
                continue

            # Don't refer to foo.bar.production, as it's confusing when doing
            # things in preview or staging. Refer to the machines exclusively by
            # short name.
            short_host = '{0}.{1}'.format(name, vdc)

            cls = name.rstrip('-1234567890').replace('-', '_')
            self.roledefs['all'].append(short_host)
            self.roledefs['class-%s' % cls].append(short_host)
            self.roledefs['vdc-%s' % vdc].append(short_host)
            self.classes.add(cls)
            self.vdcs.add(vdc)

        self.fetched = True

    def fetch_puppet_class(self, name):
        # These cannot be prefetched because there's too many variations.
        # But we only need to fetch once for each.
        if self.roledefs['puppet_class-%s' % name]:
            return

        hosts = _fetch_hosts('-C %s' % name)
        self.roledefs['puppet_class-%s' % name] = hosts

    def __contains__(self, key):
        return True

    def __getitem__(self, key):
        def _looker_upper():
            self._assert_fetched()
            return self.roledefs[key]
        return _looker_upper

    def _assert_fetched(self):
        if not self.fetched:
            abort(ABORT_MSG)

def _fetch_hosts(extra_args=''):
    """
    Fetch a list of hosts in this environment, regardless of whether we're
    executing from within the environment or via a gateway.
    """
    list_cmd = 'govuk_node_list %s' % extra_args
    with hide('running', 'stdout'):
        if env.gateway:
            with settings(host_string=env.gateway, gateway=None):
                return run(list_cmd).splitlines()

        # Otherwise assume we're *in* the infrastructure
        else:
            return local(list_cmd).splitlines()

def _fetch_known_hosts():
    """
    Fetch the system known_hosts file for the selected gateway. This downloads
    the remote gateway's system known_hosts file and installs it to where Fabric
    will look for it.

    If your host keys are out of date, you can simply blow away SSH_DIR and
    rerun the command. Fabric should re-download the known_hosts file from the
    gateway.
    """
    if env.gateway is None:
        raise RuntimeError("Tried to _fetch_known_hosts with no env.gateway set!")

    known_hosts_file = os.path.join(SSH_DIR, env.gateway)

    remote_known_hosts_file = "/etc/ssh/ssh_known_hosts"

    if _known_hosts_outdated(known_hosts_file, remote_known_hosts_file):
        print("Updating local copy of %s hosts" % env.gateway)
        with settings(host_string=env.gateway, gateway=None):
            get('/etc/ssh/ssh_known_hosts', known_hosts_file)

    return known_hosts_file

def _known_hosts_outdated(local_filename, remote_filename):
    """Check whether a local copy of a jumpbox hosts file is outdated.

    We keep a local copy of known hosts from each jumpbox to use when we want
    to run a command against a whole class of hosts (or indeed all of them). We
    need to make sure this is kept reasonably current, so we run commands
    against the right machines.

    """
    if not os.path.exists(local_filename):
        return True

    # Give the file a grace period, so we don't go checking every single time
    if time.time() - os.path.getmtime(local_filename) < HOSTS_FILE_CACHE_TIME:
        return False

    # Compare local and remote checksums to see whether we need to update
    local_checksum = md5(open(local_filename).read()).hexdigest()
    with hide('running', 'stdout'):
        with settings(host_string=env.gateway, gateway=None):
            remote_checksum = run("md5sum %s" % remote_filename).split()[0]

    return local_checksum != remote_checksum


def _set_gateway(name, draft=False):
    """
    Set the remote gateway box by environment name. Sets the Fabric env.gateway
    setting and makes sure that the correct known_hosts file will be consulted,
    then dynamically fetches a list of hosts from the gateway box.
    """
    if draft:
      env.gateway = 'jumpbox.draft.{0}.publishing.service.gov.uk'.format(name)
    else:
      env.gateway = 'jumpbox.{0}.alphagov.co.uk'.format(name)
    env.system_known_hosts = _fetch_known_hosts()
    env.roledefs.fetch()

@task
def help(name):
    """Show extended help for a task (e.g. 'fab help:search.reindex')"""
    task = crawl(name, state.commands)

    if task is None:
        abort("%r is not a valid task name" % task)

    puts(textwrap.dedent(task.__doc__).strip())

@task
def production():
    """Select production environment"""
    _set_gateway('production')

@task
def draft_production():
    """Select draft production environment"""
    _set_gateway('production', draft=True)

@task
def staging():
    """Select staging environment"""
    _set_gateway('staging')

@task
def draft_staging():
    """Select draft staging environment"""
    _set_gateway('staging', draft=True)

@task
def preview():
    """Select preview environment"""
    _set_gateway('preview')

@task
def draft_preview():
    """Select draft preview environment"""
    _set_gateway('preview', draft=True)

@task
def all():
    """Select all machines in current environment"""
    env.hosts.extend(env.roledefs['all']())

@task
@runs_once
@serial
def numbered(number):
    """Select only machines with a given number"""
    if (not re.match(r'\A[0-9]+\Z', number)):
        abort("Unrecognised number: %s" % number)
    env.hosts = [host for host in env.hosts if re.search((r'-%s\.' % number), host)]

@task(name='class')
def klass(class_name):
    """Select a machine class"""
    env.hosts.extend(env.roledefs['class-%s' % class_name]())

@task
@serial
@hosts('localhost')
def puppet_class(class_name):
    """Select all machines which include a given puppet class"""
    env.roledefs.fetch_puppet_class(class_name)
    env.hosts.extend(env.roledefs['puppet_class-%s' % class_name]())

@task
@hosts('localhost')
def node_type(node_name):
    """Select all machines of a given node type"""
    class_name = 'govuk::node::s_{}'.format(node_name.replace('-', '_'))
    puppet_class(class_name)
    
@task
def vdc(vdc_name):
    """Select a virtual datacentre"""
    env.hosts.extend(env.roledefs['vdc-%s' % vdc_name]())

@task
@runs_once
def hosts():
    """List selected hosts"""
    me = state.commands['hosts']
    hosts = me.get_hosts(None, None, None, env)
    print('\n'.join(sorted(hosts)))

@task
@runs_once
def classes():
    """List available classes"""
    for name in sorted(env.roledefs.classes):
        hosts = env.roledefs['class-%s' % name]
        print("%-30.30s %s" % (name, len(hosts())))

@task
@runs_once
def vdcs():
    """List available virtual datacentres"""
    for name in sorted(env.roledefs.vdcs):
        hosts = env.roledefs['vdc-%s' % name]
        print("%-30.30s %s" % (name, len(hosts())))

@task
def do(command):
    """Execute arbitrary commands"""
    run(command)

@task
def sdo(command):
    """Execute arbitrary commands with sudo"""
    sudo(command)

env.roledefs = RoleFetcher()
