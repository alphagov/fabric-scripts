from fabric.api import roles, task
from fabric.tasks import execute
import nginx
import puppet


@task
@roles('class-cache')
def fail_to_mirror():
    """Fails the site to the mirror by stopping nginx on the cache nodes"""
    puppet.disable("Fabric fail_to_mirror task invoked")
    execute(nginx.kill)
    print('Disabled Puppet and switched off Nginx.')
    print('Run `incident.recover_origin` to start serving from origin again.')


@task
@roles('class-cache')
def recover_origin():
    """Recovers GOV.UK to serve from origin after incident.fail_to_mirror has been invoked"""
    puppet.enable()
    puppet.agent()
    print("Puppet has been re-enabled, has run and the site should now be serving from origin as normal.")
