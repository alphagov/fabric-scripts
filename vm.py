from fabric.api import *

@task
def uptime():
    """Show uptime and load"""
    run('uptime')

@task
def free():
    """Show memory stats"""
    run('free')

@task
def disk():
    """Show disk usage"""
    run('df -kh')

@task
def stopped_jobs():
    """Find stopped govuk application jobs"""
    with hide('running'):
        run('grep -l govuk_spinup /etc/init/*.conf | xargs -n1 basename | while read line; do sudo status "${line%%.conf}"; done | grep stop || :')

@task
def bodge_unicorn(name):
    """
    Manually kill off (and restart) unicorn processes by name

    e.g. To kill off and restart contentapi on backend-1

      fab vm.bodge_unicorn:contentapi,hosts=backend-1.backend.production

    Yes. This is a bodge. Sorry.
    """
    pid = run("ps auxwww | grep '%s' | grep -F 'unicorn master' | grep -v grep | awk '{ print $2 }' | xargs" % name)
    if pid:
        sudo("kill -9 %s" % pid)
    sudo("start '{0}' || restart '{0}'".format(name))
