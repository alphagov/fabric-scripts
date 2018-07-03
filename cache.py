from fabric.api import run, sudo, task


@task
def purge(*args):
    "Purge items from varnish, eg \"/one,/two,/three\""
    for path in args:
        run("curl -s -I --fail -X PURGE http://localhost:7999%s" % path.strip())


@task
def ban_all():
    """
    Invalidate all current cached objects in varnish.

    Note that this will not delete existing objects but does prevent them from being served.
    We use it instead of purging because it's more efficient when invalidating a large
    number of objects, i.e. all objects.

    See: https://www.varnish-cache.org/docs/3.0/tutorial/purging.html
    """
    sudo("varnishadm 'ban req.url ~ .'")


@task
def restart():
    """
    Restart Varnish caches
    """
    sudo('/etc/init.d/varnish restart')


@task(default=True)
def stats():
    "Show details about varnish performance"
    sudo('varnishstat -1')
