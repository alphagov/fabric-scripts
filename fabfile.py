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
import ckan
import elasticsearch
import filebeat
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
import postgresql
import rabbitmq
import rbenv
import statsd
import vm
import whitehall

HERE = os.path.dirname(__file__)
SSH_DIR = os.path.join(HERE, '.ssh')

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
def production():
    """Select production environment"""
    env['environment'] = 'production'
    env['aws_migration'] = False
    env.gateway = 'jumpbox.publishing.service.gov.uk'


@task
def staging():
    """Select staging environment"""
    env['environment'] = 'staging'
    env['aws_migration'] = False
    env.gateway = 'jumpbox.staging.publishing.service.gov.uk'


@task
def integration():
    """Select integration environment"""
    env['environment'] = 'integration'
    env['aws_migration'] = True
    env.gateway = 'jumpbox.blue.integration.govuk.digital'


@task
def training():
    """Select training environment"""
    env['environment'] = 'training'
    env['aws_migration'] = True
    env.gateway = 'jumpbox.training.govuk.digital'


@task
def aws_staging(stackname=None):
    if not stackname:
        stackname = 'blue'

    """Select GOV.UK AWS Staging  environment"""
    env['environment'] = 'staging'
    env['aws_migration'] = True
    env.gateway = 'jumpbox.blue.staging.govuk.digital'


@task
def staging_aws(stackname=None):
    return aws_staging(stackname)


@task
def aws_production(stackname=None):
    if not stackname:
        stackname = 'blue'

    """Select GOV.UK AWS Production  environment"""
    env['environment'] = 'production'
    env['aws_migration'] = True
    env.gateway = 'jumpbox.blue.production.govuk.digital'


@task
def production_aws(stackname=None):
    return aws_production(stackname)


@task
def ci():
    """Select CI environment"""
    env['environment'] = 'ci'
    env['aws_migration'] = False
    env.gateway = 'ci-jumpbox.integration.publishing.service.gov.uk'


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
