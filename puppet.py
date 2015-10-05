from fabric.api import *


def puppet(*args):
    sudo('govuk_puppet %s' % ' '.join(args))


@task(default=True)
def agent(*args):
    """Run puppet agent"""
    puppet(*args)


@task
def disable(reason):
    """Disable puppet runs. Requires a reason as a string arg"""
    puppet('--disable "{0} (by {1})"'.format(reason, env.user))


@task
def enable():
    """Enable puppet runs"""
    puppet('--enable')


@task
def check_disabled():
    """Check if puppet runs are disabled"""
    lockfile = '/var/lib/puppet/state/agent_disabled.lock'

    with hide('running'):
        sudo('test -f {0} && echo DISABLED || echo ENABLED'.format(lockfile))


@task
def dryrun(*args):
    """Run puppet agent but make no changes to the system"""
    puppet('--noop', *args)


@task
@hosts('puppetmaster-1.management')
def lookup_hieradata(key):
    puppet_directory = '/usr/share/puppet/production/current'
    config_file = '{0}/hiera.yml'.format(puppet_directory)
    variables = '::environment=production ::lsbdistcodename=precise ::settings::manifestdir={0}/manifests'.format(puppet_directory)
    run('hiera --config {0} {1} {2}'.format(config_file, key, variables))
