import re
from fabric.tasks import task


@task
def restart(app):
    """Restart a particular app"""
    _service(app, 'restart')


@task
def reload(app):
    """Reload a particular app.

    Unlike `restart`, this will tell the app to reload itself gracefully; for
    apps running under unicornherder, this will spin up a new process, then
    stop the old one after a short overlap period.

    """
    _service(app, 'reload')


@task
def stop(app):
    """Stop a particular app"""
    _service(app, 'stop')


@task
def start(app):
    """Start a particular app"""
    _service(app, 'start')


@task
def status(app):
    """Check status of a particular app"""
    _service(app, 'status')


def _service(app, command):
    sudo('service {} {}'.format(app, command))


@task
def respawn_large_unicorns(app):
    """Gracefully kill the unicorn worker using the most RAM for a particular app"""
    master_pid = run('cat /var/run/{}/app.pid'.format(app))
    if not re.match('^unicorn master', run('cat /proc/{}/cmdline'.format(master_pid))):
        abort('App not running unicorn')

    sudo("kill -QUIT $(ps -o rss,pid --ppid %s --sort +rss | tail -n1 | awk '{print $2}')" % master_pid)


def env_filename(app, name):
    return '/etc/govuk/{app}/env.d/{name}'.format(app=app, name=name)


@task
def setenv(app, name, value):
    """
    Set an environment variable for an application.

    Note: this does not restart the application or any relevant other services.
    """

    sudo('echo -n \'{value}\' > {filename}'.format(
        value=value, filename=env_filename(app, name)
    ))


@task
def rmenv(app, name):
    """
    Remove an environment variable for an application.

    Note: this does not restart the application or any relevant other services.
    """

    sudo('rm {filename}'.format(
        filename=env_filename(app, name)
    ))
