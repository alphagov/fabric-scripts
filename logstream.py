from fabric.tasks import task

@task
def restart_all(context):
    """Restart all the logstreams on a machine"""
    sudo("for logstream in `ls /etc/init/logstream*`; do BASE=`basename $logstream .conf`; service $BASE restart; done")
