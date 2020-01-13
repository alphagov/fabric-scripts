from fabric.tasks import task

etcd_cluster = 'http://etcd.cluster:2379'
locksmithctl = '/usr/bin/locksmithctl'


def check_locksmithctl(context):
    if not fabric.contrib.files.exists(locksmithctl):
        error('locksmithctl is not installed. Perhaps unattended_reboots are disabled?')


@task
def status(context):
    """Get the status of locksmith"""
    check_locksmithctl()
    run("{0} -endpoint='{1}' status".format(locksmithctl, etcd_cluster))


@task
def unlock(context, machine_name):
    """Unlock a machine with locksmith"""
    check_locksmithctl()
    run("{0} -endpoint='{1}' unlock '{2}'".format(locksmithctl, etcd_cluster, machine_name))
