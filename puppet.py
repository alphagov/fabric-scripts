from fabric.api import *

def puppet(*args):
    sudo('RUBYOPT="-W0" puppet %s' % ' '.join(args))

@task(default=True)
def agent(*args):
    """Run puppet agent"""
    puppet('agent', '--onetime', '--no-daemonize', *args)

@task
def disable():
    """Disable puppet runs"""
    puppet('agent', '--disable')

@task
def enable():
    """Enable puppet runs"""
    puppet('agent', '--enable')

@task
def check_disabled():
    """Check if puppet runs are disabled"""
    lockfile = '/var/lib/puppet/state/puppetdlock'

    # Puppet is disabled if the lockfile exists and has zero size (whereas a
    # running puppet agent will write its PID to the lockfile)
    with hide('running'):
        run('test -e {0} -a ! -s {0} && echo DISABLED || echo ENABLED'.format(lockfile))

@task
def dryrun(*args):
    """Run puppet agent but make no changes to the system"""
    puppet('agent', '--onetime', '--no-daemonize', '--noop', *args)
