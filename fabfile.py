from __future__ import print_function

from collections import defaultdict
from git import Repo
from hashlib import md5
import os
import re
import textwrap
import time

from fabric import state
from fabric.api import (abort, env, get, hide, hosts, local, puts, run,
                        runs_once, serial, settings, sudo, task, warn)
from fabric.task_utils import crawl

# Other submodules such as mapit depend on puppet, so include this one first
import puppet

# Our command submodules
import app
import apt
import bundler
import cache
import campaigns
import cdn
import elasticsearch
import emailalertapi
import incident
import jenkins
import locksmith
import logstream
import mapit
import mongo
import mysql
import nagios
import nginx
import ntp
import performanceplatform
import postgresql
import rabbitmq
import rbenv
import statsd
import vm
import vpn
import whitehall

HERE = os.path.dirname(__file__)
SSH_DIR = os.path.join(HERE, '.ssh')

# How old a local hosts file can be before we check for an update
HOSTS_FILE_CACHE_TIME = 3600 * 24

# When to warn that you haven't pulled the repo recently.
REPO_OUTDATED_TIME = 3600 * 24 * 5
REPO_OUTDATED_FILE = os.path.join(HERE, '.git/FETCH_HEAD')


def fetch_hosts(options=''):
    command = "govuk_node_list %s" % options

    with hide('running', 'stdout'):
        if env.gateway:
            with settings(host_string=env.gateway, gateway=None):
                hosts = run(command).splitlines()

        # Otherwise assume we're *in* the infrastructure
        else:
            hosts = local(command).splitlines()

    return map(lambda host: host.split(".")[0], hosts)


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


def _check_repo_age():
    if not os.path.exists(REPO_OUTDATED_FILE):
        return
    if time.time() - os.path.getmtime(REPO_OUTDATED_FILE) > REPO_OUTDATED_TIME:
        repo = Repo(os.getcwd())
        current_branch = repo.active_branch.name

        if current_branch == 'master':
            repo.remotes.origin.pull()
        else:
            warn('Your fabric-scripts may be out-of-date. Please `git pull` the repo')


def _set_gateway(jumpbox_domain):
    """
    Set the remote gateway box by environment name. Sets the Fabric env.gateway
    setting and makes sure that the correct known_hosts file will be consulted,
    then dynamically fetches a list of hosts from the gateway box.
    """
    env.gateway = 'jumpbox.{0}'.format(jumpbox_domain)
    env.system_known_hosts = _fetch_known_hosts()


@task
def help(name=""):
    """Show extended help for a task (e.g. 'fab help:search.reindex')"""
    from fabric.main import show_commands
    if not name:
        puts("\nFor more information on a task run `fab help:<task>`.\n")
        show_commands(None, 'short')
    task = crawl(name, state.commands)

    if task is None:
        abort("%r is not a valid task name" % task)

    puts(textwrap.dedent(task.__doc__).strip())


@task
def production(stackname=None):
    if not stackname:
        stackname = 'blue'

    """Select production environment"""
    env['environment'] = 'production'
    env['aws_migration'] = False
    _set_gateway('publishing.service.gov.uk')


@task
def staging(stackname=None):
    if not stackname:
        stackname = 'blue'

    """Select staging environment"""
    env['environment'] = 'staging'
    env['aws_migration'] = False
    _set_gateway('staging.publishing.service.gov.uk')


@task
def integration(stackname=None):
    if not stackname:
        stackname = 'blue'

    """Select integration environment"""
    env['environment'] = 'integration'
    env['aws_migration'] = True
    _set_gateway("{}.integration.govuk.digital".format(stackname))


@task
def aws_staging(stackname=None):
    if not stackname:
        stackname = 'blue'

    """Select GOV.UK AWS Staging  environment"""
    env['environment'] = 'staging'
    env['aws_migration'] = True
    _set_gateway("{}.staging.govuk.digital".format(stackname))


@task
def all():
    """Select all machines in current environment"""
    env.hosts.extend(fetch_hosts())


@task(name='class')
def klass(*class_names):
    """Select a machine class"""
    for class_name in class_names:
        class_name = class_name.replace("-", "_")
        env.hosts.extend(fetch_hosts("-c %s" % class_name))


@task
@serial
@hosts('localhost')
def puppet_class(*class_names):
    """Select all machines which include a given puppet class"""
    for class_name in class_names:
        env.hosts.extend(fetch_hosts("-C %s" % class_name))


@task
@runs_once
def application(app_name):
    """Select all machines which host a given application"""
    class_name = 'govuk::apps::{}'.format(app_name.replace('-', '_'))
    puppet_class(class_name)


@task
def node_type(node_name):
    """Select all machines of a given node type"""
    class_name = 'govuk::node::s_{}'.format(node_name.replace('-', '_'))
    puppet_class(class_name)


@task
@runs_once
@hosts(["localhost"])
def classes():
    """List available classes"""
    with hide("everything"):
        if not env["aws_migration"]:
            classes = set()

            for host in fetch_hosts():
                classes.add(re.split('-[0-9]', host)[0].replace('-', '_'))

            print("\n".join(classes))
        else:
            print(run("govuk_node_list --classes"))


@task
@runs_once
def hosts():
    """List selected hosts"""
    me = state.commands['hosts']
    hosts = me.get_hosts(None, None, None, env)
    print('\n'.join(sorted(hosts)))


@task
def do(command):
    """Execute arbitrary commands"""
    run(command)


@task
def sdo(command):
    """Execute arbitrary commands with sudo"""
    sudo(command)

_check_repo_age()
