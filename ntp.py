from fabric.api import *

@task
def resync():
    """Forcibly resynchronise the VM's NTP clock.
    
    If a VM's clock manages to get sufficiently out of sync, ntp will give up,
    forcing a manual intervention.
    """
    sudo("service ntp stop")
    sudo("ntpdate ntp.ubuntu.com")
    sudo("service ntp start")
