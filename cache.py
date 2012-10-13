from fabric.api import *

@task
@roles('cache')
def purge(*args):
    "Purge items from varnish, eg \"/one,/two,/three\""
    for path in args:
        run("curl -s -I -X PURGE http://localhost:7999%s" % path.strip())

@task
@roles('cache')
def restart():
    """
    Restart Varnish caches
    Runs sudo remotely in order to pick up permissions in sudoers
    """
    sdo('/etc/init.d/varnish restart')

@task
@roles('cache')
def stats():
    "Show details about varnish performance"
    sudo('varnishstat -1')
