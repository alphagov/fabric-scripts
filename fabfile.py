from collections import defaultdict
import os
import random
import re
import sys

from fabric.api import *

env.hosts = []
env.roledefs = defaultdict(list)

with hide('running'):
    hosts = local("awk '!/github|#|^$/ {print $1}' /etc/ssh/ssh_known_hosts | sort | uniq", capture=True)
    hosts = hosts.splitlines()

for host in hosts:
    name, vdc, org = host.rsplit('.', 3)
    env.roledefs['org-%s' % org].append(host)
    env.roledefs['vdc-%s' % vdc].append(host)
    env.roledefs['class-%s' % name.rstrip('-1234567890')].append(host)

@task
def uptime():
    "Show uptime and load"
    run('uptime')

@task
def free():
    "Show memory stats"
    run('free')

@task
def updates():
    "Show package counts needing updates"
    run("cat /var/lib/update-notifier/updates-available")

@task
def upgrade():
    "Upgrade packages with apt-get"
    sudo("apt-get update; apt-get upgrade -y")

USE_PANOPTICON = ['calendars', 'smartanswers', 'licencefinder', 'publisher']
CLASS_APP_MAP = {
    'frontend': ['calendars', 'smartanswers', 'licencefinder', 'frontend'],
    'backend': ['publisher', 'whitehall-admin', 'recommended-links'],
}

@task
def reindex(app):
    "Rebuild search indices (usage: 'fab reindex:calendars')"
    rake_task = 'panopticon:register' if app in USE_PANOPTICON else 'rummager:index'
    govuk_class = None

    for c, apps in CLASS_APP_MAP.items():
        if app in apps:
            govuk_class = c
            break

    if govuk_class is None:
        abort("I don't know on what class of machine %s runs. Try updating CLASS_APP_MAP." % app)

    use_one_of(govuk_class)

    with cd('/var/apps/%s' % app):
        sudo('RAILS_ENV=production bundle exec rake "%s"' % rake_task, user='deploy')

@task
def reindex_all():
    "Rebuild all search indices"
    all_apps = [a for app_list in CLASS_APP_MAP.values() for a in app_list]
    for app in all_apps:
        puts("Rebuilding search index for application '%s'" % app)
        reindex(app)

@task
def puppet():
    "Run puppet on a specific host or role (usage: 'fab -P -R class-cache puppet')"
    run('govuk_puppet --verbose')

def use_one_of(govuk_class):
    env.host_string = random.choice(env.roledefs['class-%s' % govuk_class])


