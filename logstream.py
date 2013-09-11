from fabric.api import *

@task
def restart_all():
    """Restart all the logstreams on a machine"""
    sudo("for logstream in `ls /etc/init/logstream*`; do BASE=`basename $logstream .conf`; service $BASE restart; done")

