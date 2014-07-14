from fabric.api import *

@task
def loadhosts(*classnames):
    """Load hosts that include given Puppet class(es)"""
    classnames = ','.join(classnames)
    with hide('running', 'stdout'):
          with settings(host_string=env.gateway, gateway=None):
              env.hosts = run('govuk_node_list -C %s' % classnames).splitlines()

def puppet(*args):
    sudo('govuk_puppet %s' % ' '.join(args))

@task(default=True)
def agent(*args):
    """Run puppet agent"""
    puppet(*args)

@task
def disable(reason):
    """Disable puppet runs. Requires a reason as a string arg"""
    puppet('--disable "%s"' % reason)

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
