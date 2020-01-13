from fabric.tasks import task
from time import sleep


def puppet(context, *args):
    sudo('govuk_puppet --test %s' % ' '.join(args))


@task(default=True)
def agent(context, *args):
    """Run puppet agent"""
    puppet(context, *args)


@task
def disable(context, reason):
    """Disable puppet runs. Requires a reason as a string arg"""
    puppet('--disable "{0} (by {1})"'.format(reason, env.user))


@task
def enable(context):
    """Enable puppet runs"""
    puppet(context, '--enable')


@task
def check_disabled(context):
    """Check if puppet runs are disabled"""
    lockfile = '/var/lib/puppet/state/agent_disabled.lock'

    with hide('running'):
        sudo('test -f {0} && echo DISABLED || echo ENABLED'.format(lockfile))


@task
def dryrun(context, *args):
    """Run puppet agent but make no changes to the system"""
    puppet('--noop', *args)


@task(hosts='puppetmaster-1.management')
def lookup_hieradata(context, key):
    puppet_directory = '/usr/share/puppet/production/current'
    config_file = '{0}/hiera.yml'.format(puppet_directory)
    variables = '::environment=production ::lsbdistcodename=precise ::settings::manifestdir={0}/manifests'.format(puppet_directory)
    run('hiera --config {0} {1} {2}'.format(config_file, key, variables))


@task(hosts='puppetmaster-1.management')
def sign_certificates(context):
    """Sign Puppet certificates on the Puppetmaster when launching machines"""
    print('Signing certificates in a loop. Cancel this command to stop signing certificates.')
    while True:
        # 24 is the exit code that Puppet returns when there are no waiting certificate requests to sign
        with settings(hide('running'), ok_ret_codes=[0, 24]):
            sudo('puppet cert sign --all')
        sleep(10)


@task
def cert_clean(context):
    """Remove old puppet certificates from all clients except for puppetmaster."""
    print('Removing puppet client certificates in a loop. Cancel this command to stop removing certificates.')
    """We have to accept error code 1[The file doesn't have puppet master] 2[no such file] 3[puppet is not running]"""
    with settings(ok_ret_codes=[0, 1, 2, 3]):
        if run("sudo cat /var/lib/puppet/state/classes.txt|grep master"):
            print('I am a puppet master. Hence, we are skipping.')
        else:
            print('Stopping the puppet daemon.')
            sudo("/etc/init.d/puppet stop")
            print('Removing old certs.')
            sudo('rm -rf /etc/puppet/ssl')
            print('request a new cert')
            sudo('puppet agent -t')


@task
def agent_run(context):
    """This task will perform a puppet run while accepting exceptions for errors listed below."""
    with settings(ok_ret_codes=[0, 1, 2, 4, 6]):
        sudo('puppet agent -t')


@task
def config_version(context):
    """Fetch the current puppet config version"""
    sudo("awk '/config:/ { print \"sha:\" $2 }' /var/lib/puppet/state/last_run_summary.yaml | tr -d '\"'")
    sudo("awk '/last_run:/ { print \"time:\" $2 }' /var/lib/puppet/state/last_run_summary.yaml | tr -d '\"'")
