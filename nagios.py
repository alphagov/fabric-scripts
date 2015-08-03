from StringIO import StringIO
import string
import requests

from fabric.api import *


NAGIOS_CMD_FILE = '/var/lib/icinga/rw/nagios.cmd'


def submit_nagios_cmd(command):
    # ugh, double-formatted string
    sudo("printf '[%%lu] %s\n' `date +%%s` >> %s" % (command, NAGIOS_CMD_FILE))


def _nagios_hostname(host):
    """Returns the canonical name (according to nagios) for a host"""
    name_parts = string.split(host,'.')
    env_expected_name_length = 7 if (('preview' in name_parts) | ('staging' in name_parts)) else 6
    if len(name_parts) == 1:
        raise ValueError("Shortnames not supported for nagios commands")
    elif len(name_parts) > env_expected_name_length:
        raise ValueError("Don't understand name of nagios host: %s" % host)
    elif len(name_parts) == env_expected_name_length:
        return host


@task
@hosts(['alert.cluster'])
def schedule_downtime(host,minutes='20'):
    """Schedules downtime for a host in nagios; default for 20 minutes"""

    # get timestamp from monitoring server to avoid clock skew issues.
    timestamp = int(run("date +%s"))
    minutes = int(minutes)
    seconds = minutes * 60

    host = _nagios_hostname(host)

    command = "SCHEDULE_HOST_SVC_DOWNTIME;%(host)s;%(now)d;%(end)d;1;0;%(duration)d;fabric;fabric" % {
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


@task
@runs_once
def loadhosts():
    """Load hosts from an Icinga URL in jsonformat.

    Prompts for a URL like:
        https://nagios.example.com/cgi-bin/icinga/status.cgi?search_string=puppet+last+run&limit=0&start=1&servicestatustypes=29
    """

    url = prompt("Icinga URL (jsonformat): ")
    resp = requests.get(url, verify=False)
    hosts = [
        service['host_name'].split('.production').pop(0)
        for service in resp.json()['status']['service_status']
    ]

    print "\nSelected hosts:\n  - %s\n" % "\n  - ".join(hosts)
    prompt("Type 'yes' to confirm: ", validate="yes")
    env.hosts = hosts
