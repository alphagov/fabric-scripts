from fabric.api import *
from datetime import *
import json
import re
import time

today = date.today().strftime("%a %b %d")

def node_name(node_name):
    return node_name.split('.production').pop(0)

def strip_dates(raw_output):
    stripped_isodates = re.sub(r'ISODate\((.*?)\)', r'\1', raw_output)
    return re.sub(r'Timestamp\((.*?)\)', r'"\1"', stripped_isodates)

def mongo_command(command):
    return "mongo --quiet --eval 'printjson(%s)'" % command

def run_mongo_command(command, command_warn_only=False):
    if command_warn_only:
        with settings(warn_only=True):
            response = run(mongo_command(command))
    else:
        response = run(mongo_command(command))

    if response.return_code == 252:
        dict_response = {"return_code": 252}
    else:
        dict_response = json.loads(strip_dates(response))

    return dict_response

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
        print("Current primary is %s" % node_name(config['primary']))

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
    with hide('output'):
        # Mongo returns an exit code of 252 when the primary steps down, as well as disconnecting
        # the current console session. This means that we have to run the command with Fabric's
        # warn_only enabled, or Fabric will error.
        result = run_mongo_command("rs.stepDown(%s)" % seconds, command_warn_only=True)

        if 'ok' in result and result['ok'] == 0:
            print("Failed to step down: %s\nTry running mongo.find_primary" % result['errmsg'])
            return 0

        if 'return_code' in result and result['return_code'] == 252:
            print "Received a 252 exit code from Mongo. There may have been disconnection warnings"
            print "during the step down from primary that caused this. Verify the primary with mongo.find_primary."
