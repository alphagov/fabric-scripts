from fabric.api import run, task
from fabric.utils import error
import fabric.contrib.files

etcd_cluster = 'http://etcd-1.management:4001'
locksmithctl = '/usr/bin/locksmithctl'


def check_locksmithctl():
    if not fabric.contrib.files.exists(locksmithctl):
        error('locksmithctl is not installed. Perhaps unattended_reboots are disabled?')


@task
def status():
    """Get the status of locksmith"""
    check_locksmithctl()
    run("{0} -endpoint='{1}' status".format(locksmithctl, etcd_cluster))


@task
def unlock(machine_name):
    """Unlock a machine with locksmith"""
    check_locksmithctl()
    run("{0} -endpoint='{1}' unlock '{2}'".format(locksmithctl, etcd_cluster, machine_name))
