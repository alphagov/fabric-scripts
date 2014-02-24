from fabric.api import *

@task
def status():
    """Report the VM's NTP status."""
    run("ntpq -p")
    run("/usr/lib/nagios/plugins/check_ntp_time -q -H ntp.ubuntu.com -w 2 -c 3", warn_only=True)
    run("/usr/lib/nagios/plugins/check_ntp_peer -H 127.0.0.1 -w 0.5 -c 1 -m @1 -n @0", warn_only=True)

@task
def resync():
    """Forcibly resynchronise the VM's NTP clock.
    
    If a VM's clock manages to get sufficiently out of sync, ntp will give up,
    forcing a manual intervention.
    """
    sudo("service ntp stop")
    sudo("ntpdate -B ntp.ubuntu.com")
    sudo("service ntp start")
