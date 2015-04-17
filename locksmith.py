from fabric.api import run, task
import util

etcd_cluster = 'http://etcd-1.management:4001,http://etcd-2.management:4001,http://etcd-3.management:4001'

@task
def status():
    """Get the status of locksmith"""
    util.use_random_host('class-etcd')
    run("/usr/bin/locksmithctl -endpoint='{0}' status".format(etcd_cluster))

@task
def unlock(machine_name):
    """Unlock a machine with locksmith"""
    util.use_random_host('class-etcd')
    run("/usr/bin/locksmithctl -endpoint='{0}' unlock '{1}'".format(etcd_cluster, machine_name))
