import puppet
from fabric.tasks import task


@task
def disable_logit(context):
    """Disable filebeat so we don't send data to Logit.io"""
    with hide('everything'):
        locked = sudo('test -f /var/lib/puppet/state/agent_disabled.lock && echo DISABLED || echo ENABLED')

    if locked == "ENABLED":
        puppet.disable("Disable sending to logit")

    sudo("service filebeat stop")


@task
def enable_logit(context):
    """Updates filebeat.yml and enables sending to logit"""
    puppet.enable()
    sudo("service filebeat start")
