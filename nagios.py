from urllib.parse import quote_plus
import json

from fabric.api import abort, env, hide, hosts, prompt, run, runs_once, sudo, task


NAGIOS_CMD_FILE = '/var/lib/icinga/rw/nagios.cmd'


def submit_nagios_cmd(command):
    # ugh, double-formatted string
    sudo("printf '[%%lu] %s\n' `date +%%s` >> %s" % (command, NAGIOS_CMD_FILE))


def _monitoring_hostname(host):
    """Returns the canonical name (according to our monitoring) for a host"""
    if env['environment'] == 'production':
        return "{0}.publishing.service.gov.uk".format(host)
    else:
        return "{0}.{1}.publishing.service.gov.uk".format(host, env['environment'])


@task
@hosts(['alert.cluster'])
def schedule_downtime(host, minutes='20'):
    """Schedules downtime for a host in nagios; default for 20 minutes"""

    # get timestamp from monitoring server to avoid clock skew issues.
    timestamp = int(run("date +%s"))
    minutes = int(minutes)
    seconds = minutes * 60

    host = _monitoring_hostname(host)

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
@hosts(['alert.cluster'])
def loadhosts(search_string=''):
    """Load hosts from an Icinga URL in jsonformat.

    Optionally takes a search string. If provided, searches for all unhandled problems.
    If not provided, prompts for a URL like:
        https://alert.cluster/cgi-bin/icinga/status.cgi?search_string=puppet+last+run&limit=0&start=1&servicestatustypes=29
    """

    if search_string:
        url_safe_search_string = quote_plus(search_string)
        url = 'https://alert.cluster/cgi-bin/icinga/status.cgi?search_string={0}&allunhandledproblems&jsonoutput'.format(
            url_safe_search_string)
    else:
        url = prompt("Icinga URL (jsonformat): ")

    with hide('running', 'stdout'):
        status_code = run(
            'curl --silent --write-out "%{{http_code}}" --output /dev/null --insecure "{0}"'.format(url))
        if status_code == '200':
            resp = run('curl --insecure "{0}"'.format(url))
        elif status_code == '401':
            basic_auth_password = prompt('HTTP basic auth password: ')
            resp = run(
                'curl --user betademo:{1} --insecure "{0}"'.format(url, basic_auth_password))
        else:
            abort('Could not connect to monitoring service')

    hosts = [
        service['host_name']
        for service in json.loads(resp)['status']['service_status']
    ]

    hosts = sorted(set(hosts))

    if len(hosts) == 0:
        exit('No hosts were found with that search')

    print("\nSelected hosts:\n  - %s\n" % "\n  - ".join(hosts))
    prompt("Type 'yes' to confirm: ", validate="yes")
    env.hosts = hosts
