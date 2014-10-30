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
    sudo('grep replSet /var/log/mongodb/mongod.log | grep "%s"' % today )

@task
def find_primary():
    """Find which mongo node is the master"""
    with hide('output'):
        config = run_mongo_command("rs.isMaster()")
        out = None
        if 'primary' in config:
            out = node_name(config['primary']).split(':')[0]
        else:
            out = "No primary currently elected."
        print(out)
        return out


def i_am_primary(primary=None):
    if primary is None:
        primary = find_primary()
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


@task
def status():
    """Check the status of the mongo cluster"""
    with hide('output'):
        status = run_mongo_command("rs.status()")
        print("Status at %s" % status['date'])
        parsed_statuses = []
        parsed_statuses.append(['Name', 'Health', 'State', 'Heartbeat'])

        for member_status in status['members']:
            name = node_name(member_status['name'])
            health = "OK" if member_status['health'] == 1 else "ERROR"
            state = member_status['stateStr']
            heartbeat = member_status.get('lastHeartbeat', '')
            parsed_statuses.append([name, health, state, heartbeat])

        for status in parsed_statuses:
            print("| {0:<22} | {1:<8} | {2:<10} | {3:<22} |".format(status[0], status[1], status[2], status[3]))


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
    primary = find_primary()
    if primary == 'No primary currently elected':
        return primary

    for i in range(5):
        if i_am_primary(primary):
            if i == 0:
                execute(step_down_primary, primary)
            else:
                sleep(1)

    execute(vm.reboot, hosts=[env['host_string']])
