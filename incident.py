from fabric.api import *
from nginx import kill as nginx_kill
from puppet import disable as puppet_disable

@task
@roles('class-cache')
def fail_to_mirror():
    """Fails the site to the mirror"""
    puppet_disable()
    nginx_kill()
    print("Disabled Puppet and stopped Nginx, remember to re-enable these")
