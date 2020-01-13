from time import sleep
import json
import re

from fabric.tasks import task

def _strip_bson(raw_output):
    stripped = re.sub(
        r'(ISODate|ObjectId|NumberLong)\((.*?)\)', r'\2', raw_output)
    return re.sub(r'Timestamp\((.*?)\)', r'"\1"', stripped)


def _run_mongo_command(command):
    response = run("mongo --quiet --eval 'printjson(%s)'" % command)

    try:
        return json.loads(_strip_bson(response))
    except ValueError:
        print(response)


def _i_am_primary(primary=None):
    return _run_mongo_command("rs.isMaster()")["ismaster"]


def _wait_for_ok(context):
    while True:
        if _cluster_is_ok():
            return
        sleep(5)
        print("Waiting for cluster to be okay")


def _cluster_is_ok(context):
    member_statuses = _run_mongo_command("rs.status()")["members"]
    health_ok = all(s['health'] == 1 for s in member_statuses)

    state_ok = all(s['stateStr'] in ['PRIMARY', 'SECONDARY']
                   for s in member_statuses)

    one_primary = len([s for s in member_statuses
                       if s['stateStr'] == 'PRIMARY']) == 1

    return health_ok and state_ok and one_primary


@task
def force_resync(context):
    """Force a mongo secondary to resync by removing all its data."""
    if len(env.hosts) > 1:
        abort("This task should only be run on one host at a time")

    if _i_am_primary():
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


@task
def find_primary(context):
    """Find which mongo node is the master"""
    with hide("everything"):
        if _i_am_primary():
            print((colors.blue("%s is primary" %
                               env["host_string"], bold=True)))


@task
def status(context):
    """Check the status of the mongo cluster"""
    with hide("everything"):
        if _cluster_is_ok():
            print((colors.blue("Cluster is OK", bold=True)))
            return

        print((colors.blue("db.printReplicationInfo()", bold=True)))
        print((_run_mongo_command("db.printReplicationInfo()")))

        print((colors.blue("db.printSlaveReplicationInfo()", bold=True)))
        print((_run_mongo_command("db.printSlaveReplicationInfo()")))

        print((colors.blue("rs.status()", bold=True)))
        print((json.dumps(_run_mongo_command("rs.status()"), indent=4)))


@task
def step_down_primary(seconds='100'):
    """Step down as primary for a given number of seconds (default: 100)"""
    # Mongo returns an exit code of 252 when the primary steps down, as well
    # as disconnecting the current console session. We need to mark that as
    # okay so that run() won't error.
    with hide('output'), settings(ok_ret_codes=[0, 252]):
        if _i_am_primary():
            _run_mongo_command("rs.stepDown(%s)" % seconds)
            if _i_am_primary():
                print("I am still the primary")
            else:
                print("I am no longer the primary")
        else:
            print("I am not the primary")


@task
def safe_reboot(context):
    """Reboot a mongo machine, stepping down if it is the primary"""
    import vm
    if not vm.reboot_required():
        print("No reboot required")
        return

    with hide("everything"):
        _wait_for_ok()

    if _i_am_primary():
        execute(step_down_primary)

    with hide("everything"):
        _wait_for_ok()

    execute(vm.reboot, hosts=[env['host_string']])
