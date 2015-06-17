from fabric.api import task, roles, runs_once
from fabric.api import run, sudo, hide, settings, abort, execute, puts, env
from fabric import colors
from datetime import date
from time import sleep
import json
import re

today = date.today().strftime("%a %b %d")


def node_name(node_name):
    return node_name.split('.production').pop(0)


def node_health(health_code):
    return "OK" if health_code == 1 else "ERROR"


def strip_dates(raw_output):
    stripped_isodates = re.sub(r'ISODate\((.*?)\)', r'\1', raw_output)
    return re.sub(r'Timestamp\((.*?)\)', r'"\1"', stripped_isodates)


def mongo_command(command):
    return "mongo --quiet --eval '%s'" % command


def run_mongo_command(command):
    response = run(mongo_command('printjson(%s)' % command))

    try:
        return json.loads(strip_dates(response))
    except ValueError:
        print response


@task(default=True)
@roles('class-mongo')
def replsetlogs(*args):
    """Grep the mongod logs for replSet today"""
    sudo('grep replSet /var/log/mongodb/mongod.log | grep "%s"' % today)


@task
def force_resync():
    """Force a mongo secondary to resync by removing all its data."""
    if len(env.hosts) > 1:
        abort("This task should only be run on one host at a time")

    if i_am_primary():
        abort(colors.red("Refusing to force resync on primary", bold=True))

    execute("puppet.disable", "Forcing mongodb resync")
    execute("app.stop", "mongodb")
    # wait for mongod process to stop
    while run("ps -C mongod", quiet=True).return_code == 0:
        puts("Waiting for mongod to stop")
        sleep(1)
    sudo("rm -rf /var/lib/mongodb/*")
    execute("app.start", "mongodb")
    execute("puppet.enable")


def _find_primary():
    with hide('output', 'running'):
        config = run_mongo_command("rs.isMaster()")
        out = None
        if 'primary' in config:
            out = node_name(config['primary']).split(':')[0]
        else:
            out = "No primary currently elected."
        return out


@task
def find_primary():
    """Find which mongo node is the master"""
    print(_find_primary())


def i_am_primary(primary=None):
    if primary is None:
        primary = _find_primary()
    if primary == 'No primary currently elected.':
        return False

    backend_re = re.compile(r'^backend-(\d+).mongo$')
    if primary == env['host_string']:
        return True
    elif env['host_string'].split('.')[0] == primary.split('.')[0]:
        # lol licensify-mongo-n.licensify
        return True
    elif backend_re.match(primary):
        # lol mongo-n.backend
        match = backend_re.match(primary)
        real_primary = 'mongo-{}.backend'.format(match.group(1))
        if match and real_primary == env['host_string']:
            return True
    return False


def get_cluster_status():
    with hide('everything'):
        status = run_mongo_command('rs.status()')
        parsed_statuses = []

        for member_status in status['members']:
            parsed_status = {
                'name': node_name(member_status['name']),
                'health': node_health(member_status['health']),
                'state': member_status['stateStr'],
            }
            keys = [
                'uptime', 'optime', 'optimeDate',
                'lastHeartbeat', 'lastHeartbeatRecv',
                'lastHeartbeatMessage',
            ]
            for key in keys:
                parsed_status[key] = member_status.get(key, '')
            parsed_statuses.append(parsed_status)

        return parsed_statuses


def cluster_is_ok():
    member_statuses = get_cluster_status()
    health_ok = all(s['health'] == 'OK' for s in member_statuses)
    state_ok = all(s['state'] in ['PRIMARY', 'SECONDARY']
                   for s in member_statuses)
    one_primary = len([s for s in member_statuses
                       if s['state'] == 'PRIMARY']) == 1

    return health_ok and state_ok and one_primary


@task
@runs_once
def status():
    """Check the status of the mongo cluster"""
    with hide('output'), settings(host_string=_find_primary()):
        print(colors.blue(
            "Primary replication info - db.printReplicationInfo()",
            bold=True))
        print(run(mongo_command("db.printReplicationInfo()")))

        print(colors.blue(
            "Slave replication info - db.printSlaveReplicationInfo()",
            bold=True))
        print(run(mongo_command("db.printSlaveReplicationInfo()")))

        print(colors.blue(
            "Replication status - rs.status()",
            bold=True))
        for status in get_cluster_status():
            print(colors.cyan(
                "{} - {}".format(status['name'], status['state'])))

            keys = ['health', 'uptime', 'optime', 'optimeDate',
                    'lastHeartbeat', 'lastHeartbeatRecv',
                    'lastHeartbeatMessage']
            for key in keys:
                if status[key]:
                    print("{0:<22} {1}".format(key, status[key]))


@task
def step_down_primary(seconds='100'):
    """Step down as primary for a given number of seconds (default: 100)"""
    # Mongo returns an exit code of 252 when the primary steps down, as well
    # as disconnecting the current console session. We need to mark that as
    # okay so that run() won't error.
    with hide('output'), settings(ok_ret_codes=[0, 252]):
        if i_am_primary():
            run_mongo_command("rs.stepDown(%s)" % seconds)
            if i_am_primary():
                print("I am still the primary")
            else:
                print("I am no longer the primary")
        else:
            print("I am not the primary")


@task
def safe_reboot():
    """Reboot a mongo machine, stepping down if it is the primary"""
    import vm
    if not vm.reboot_required():
        print("No reboot required")
        return

    while True:
        if cluster_is_ok():
            break
        sleep(5)
        print("Waiting for cluster to be okay")

    primary = _find_primary()
    if primary == 'No primary currently elected':
        return primary

    if i_am_primary(primary):
        execute(step_down_primary)

    for i in range(5):
        if cluster_is_ok() and not i_am_primary():
            break
        sleep(1)

    if not cluster_is_ok() or i_am_primary():
        abort("Cluster has not recovered")

    execute(vm.reboot, hosts=[env['host_string']])


@task
def mount_licensify_encrypted_drive():
    with settings(ok_ret_codes=[0, 1]):
        result = run('grep /var/lib/mongodb /proc/mounts')
        if result.return_code == 0:
            exit('/var/lib/mongodb is already mounted on this host.')
    with settings(warn_only=True):
        sudo('service mongodb stop')
    sudo('rm -rf /var/lib/mongodb/*')
    sudo('mount /var/lib/mongodb')
    sudo('service mongodb start')
