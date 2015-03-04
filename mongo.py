from fabric.api import *
from fabric import colors
from datetime import *
from time import sleep
import json
import re

today = date.today().strftime("%a %b %d")

def node_name(node_name):
    return node_name.split('.production').pop(0)

def strip_dates(raw_output):
    stripped_isodates = re.sub(r'ISODate\((.*?)\)', r'\1', raw_output)
    return re.sub(r'Timestamp\((.*?)\)', r'"\1"', stripped_isodates)


def mongo_command(command):
    return "mongo --quiet --eval 'printjson(%s)'" % command


def run_mongo_command(command):
    response = run(mongo_command(command))

    try:
        return json.loads(strip_dates(response))
    except ValueError:
        print response


@task(default=True)
@roles('class-mongo')
def replsetlogs(*args):
    """Grep the mongod logs for replSet today"""
    sudo('grep replSet /var/log/mongodb/mongod.log | grep "%s"' % today)


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
            name = node_name(member_status['name'])
            health = "OK" if member_status['health'] == 1 else "ERROR"
            state = member_status['stateStr']
            heartbeat = member_status.get('lastHeartbeat', '')
            parsed_status = {'name': name,
                             'health': health,
                             'state': state,
                             'heartbeat': heartbeat}
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
def status():
    """Check the status of the mongo cluster"""
    
    member_statuses = get_cluster_status()
    format_string = "| {0:<22} | {1:<8} | {2:<10} | {3:<22} |"
    print(format_string.format('Name', 'Health', 'State', 'Heartbeat'))
    for status in member_statuses:
        print(format_string.format(status['name'],
                                   status['health'],
                                   status['state'],
                                   status['heartbeat']))


@task
def step_down_primary(seconds='100'):
    """Step down as primary for a given number of seconds (default: 100)"""
    # Mongo returns an exit code of 252 when the primary steps down, as well as disconnecting
    # the current console session. We need to mark that as okay so that run() won't error.
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
