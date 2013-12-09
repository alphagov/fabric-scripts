from StringIO import StringIO
import string

from fabric.api import *


NAGIOS_CMD_FILE = '/var/lib/nagios3/rw/nagios.cmd'


def submit_nagios_cmd(command):
    # ugh, double-formatted string
    sudo("printf '[%%lu] %s\n' `date +%%s` >> %s" % (command, NAGIOS_CMD_FILE))


def _nagios_hostname(host):
    """Returns the canonical name (according to nagios) for a host"""
    name_parts = string.split(host,'.')
    if len(name_parts) > 3:
        raise ValueError("Don't understand name of nagios host: %s" % host)
    elif len(name_parts) == 3:
        return host
    elif len(name_parts) == 2:
        return "%s.production" % host
    elif len(name_parts) == 1:
        raise ValueError("Shortnames not supported for nagios commands")


@task
@hosts(['monitoring.management'])
def schedule_downtime(host,minutes='20'):
    """Schedules downtime for a host in nagios; default for 20 minutes"""

    # get timestamp from monitoring server to avoid clock skew issues.
    timestamp = int(run("date +%s"))
    minutes = int(minutes)
    seconds = minutes * 60

    host = _nagios_hostname(host)

    command = "SCHEDULE_HOST_DOWNTIME;%(host)s;%(now)d;%(end)d;1;0;%(duration)d;fabric;fabric" % {
        'now': timestamp,
        'host': host,
        'end': timestamp + seconds,
        'duration': seconds
    }
    comment = "ADD_HOST_COMMENT;%(host)s;0;%(user)s;downtime scheduled by %(user)s via fabric" % {
        'host': host,
        'user': env.user
    }
    submit_nagios_cmd(command)
    submit_nagios_cmd(comment)
