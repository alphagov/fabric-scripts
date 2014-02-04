from fabric.api import *

def puppet(*args):
    sudo('govuk_puppet %s' % ' '.join(args))

@task(default=True)
def agent(*args):
    """Run puppet agent"""
    puppet(*args)

@task
def disable():
    """Disable puppet runs"""
    puppet('--disable')

@task
def enable():
    """Enable puppet runs"""
    puppet('--enable')

@task
def check_disabled():
    """Check if puppet runs are disabled"""
    lockfile = '/var/lib/puppet/state/agent_disabled.lock'

    with hide('running'):
        run('test -f {0} && echo DISABLED || echo ENABLED'.format(lockfile))

@task
def dryrun(*args):
    """Run puppet agent but make no changes to the system"""
    puppet('--noop', *args)
