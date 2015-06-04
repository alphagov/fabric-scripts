from fabric.api import *
import nginx
import puppet

@task
@roles('class-cache')
def fail_to_mirror():
    """Fails the site to the mirror"""
    puppet.disable("Fabric fail_to_mirror task invoked")
    nginx.disable_vhost("www.gov.uk")
    nginx.disable_vhost("default")
    nginx.hello_it()
    print("Disabled Puppet and www.gov.uk and default vhosts, remember to re-enable and re-run puppet to restore previous state")
