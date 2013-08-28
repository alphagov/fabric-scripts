from __future__ import print_function

from collections import defaultdict
import os
import textwrap

from fabric import state
from fabric.api import (abort, env, get, hide, local, puts, run, runs_once,
                        settings, sudo, task, warn)
from fabric.task_utils import crawl

# Our command submodules
import app
import apt
import cache
import licensify
import mongo
import nginx
import ntp
import puppet
import rkhunter
import search
import vm

HERE = os.path.dirname(__file__)
SSH_DIR = os.path.join(HERE, '.ssh')

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

            cls = name.rstrip('-1234567890')
            self.roledefs['all'].append(short_host)
            self.roledefs['class-%s' % cls].append(short_host)
            self.roledefs['vdc-%s' % vdc].append(short_host)
            self.classes.add(cls)
            self.vdcs.add(vdc)

        self.fetched = True

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

def _fetch_hosts():
    """
    Fetch a list of hosts in this environment, regardless of whether we're
    executing from within the environment or via a gateway.
    """
    with hide('running', 'stdout'):
        if env.gateway:
            with settings(host_string=env.gateway, gateway=None):
                return run('govuk_node_list').splitlines()

        # Otherwise assume we're *in* the infrastructure
        else:
            return local('govuk_node_list').splitlines()

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

    if not os.path.exists(known_hosts_file):
        with settings(host_string=env.gateway, gateway=None):
            get('/etc/ssh/ssh_known_hosts', known_hosts_file)

    return known_hosts_file

def _set_gateway(name):
    """
    Set the remote gateway box by environment name. Sets the Fabric env.gateway
    setting and makes sure that the correct known_hosts file will be consulted,
    then dynamically fetches a list of hosts from the gateway box.
    """
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
def staging():
    """Select staging environment"""
    _set_gateway('staging')

@task
def preview():
    """Select preview environment"""
    _set_gateway('preview')

@task
def all():
    """Select all machines in current environment"""
    env.roles.append('all')

@task(name='class')
def klass(class_name):
    """Select a machine class"""
    env.roles.append('class-%s' % class_name)

@task
def vdc(vdc_name):
    """Select a virtual datacentre"""
    env.roles.append('vdc-%s' % vdc_name)

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
