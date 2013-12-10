from fabric.api import *
from datetime import *
import json
import re
import time

today = date.today().strftime("%a %b %d")

def node_name(node_name):
    return node_name.split('.production').pop(0)

def strip_isodate(raw_output):
    return re.sub(r'ISODate\((.*?)\)', r'\1', raw_output)

def mongo_command(command):
    return "mongo --quiet --eval 'printjson(%s)'" % command

def run_mongo_command(command):
    return json.loads(
            strip_isodate(
                run(mongo_command(command))))

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
        for member_status in status['members']:
            name = node_name(member_status['name'])
            health = "OK" if member_status['health'] == 1 else "ERROR"
            state = member_status['stateStr']
            heartbeat = member_status.get('lastHeartbeat', '')
            print("%s %s % -10s %s" % (name, health, state, heartbeat))

@task
def step_down_primary(seconds='100'):
    """Step down as primary for a given number of seconds (default: 100)"""
    with hide('output'):
        result = run_mongo_command("rs.stepDown(%s)" % seconds)
        if result['ok'] == 1:
            print("Stepped down for %s seconds" % seconds)
        else:
            print("Failed to step down: %s\nTry running mongo.find_primary" % result['errmsg'])

