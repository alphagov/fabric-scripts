from distutils.version import StrictVersion
from fabric.api import *
from time import sleep
import json
import re
import vm


@task
def delete(index):
    """Delete an index"""
    if re.match('^[^/]+$', index):
        run("curl -XDELETE 'http://localhost:9200/%s'" % index)
    else:
        abort("Invalid index provided '%s'" % index)


@task
def status(index):
    """Get the status of an index"""
    run("curl -XGET 'http://localhost:9200/%s/_status'" % index)


@task
def cluster_health():
    """Get cluster status"""
    return run("curl -XGET 'http://localhost:9200/_cluster/health?pretty'",
               warn_only=True)


@task
def cluster_nodes():
    """Get cluster nodes"""
    return run("curl -XGET 'http://localhost:9200/_cluster/nodes?pretty'")


def version():
    with hide('stdout'):
        elasticsearch_info = run("curl http://localhost:9200")
    version = json.loads(elasticsearch_info)['version']['number']
    return version


def put_setting(setting, value):
    result = run("""curl -XPUT 'http://localhost:9200/_cluster/settings' -d '{
        "transient": {"%s": "%s"}
    }'""" % (setting, value))
    parsed_result = json.loads(result)
    if not parsed_result.get("acknowledged"):
        raise RuntimeError("Failed to put setting: %s".format(result))
    if StrictVersion(version()) < StrictVersion('1.0'):
        if not parsed_result.get("ok"):
            raise RuntimeError("Failed to put setting: %s".format(result))


@task
def disable_reallocation():
    # Note - disable_allocation is deprecated in elasticsearch 1.0+, see
    # http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-cluster.html
    if StrictVersion(version()) > StrictVersion('1.0'):
        put_setting("cluster.routing.allocation.enable", "none")
    else:
        put_setting("cluster.routing.allocation.disable_allocation", "true")


@task
def enable_reallocation():
    # Note - disable_allocation is deprecated in elasticsearch 1.0+, see
    # http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-cluster.html
    if StrictVersion(version()) > StrictVersion('1.0'):
        put_setting("cluster.routing.allocation.enable", "all")
    else:
        put_setting("cluster.routing.allocation.disable_allocation", "false")


def wait_for_status(*allowed):
    with settings(hide('output', 'running', 'warnings'), abort_on_prompts=True):
        while True:
            try:
                output = cluster_health()
                health = json.loads(output)
            except (ValueError, SystemExit):
                # Catching SystemExit is horrible but abort_on_prompts
                # raises a SystemExit, this may change in fabric 2
                # https://github.com/fabric/fabric/issues/762
                status = "INVALID RESPONSE"
            else:
                status = health['status']
                if (status in allowed):
                    print("Cluster health is %s, matches %s" % (status, allowed))
                    return
            print("Cluster health is %s, waiting for %s" % (status, allowed))
            sleep(5)


@task
@serial
def safe_reboot():
    """Reboot only if the cluster is currently green"""
    import vm
    if not vm.reboot_required():
        print("No reboot required")
        return

    wait_for_status("green")
    disable_reallocation()

    try:
        execute(vm.reboot, hosts=[env['host_string']])

        # Give the reboot time to start, before we check for the status again.
        sleep(10)

        # Status won't usually go back to green while reallocation is turned
        # off, but should go to yellow.
        wait_for_status("green", "yellow")
        enable_reallocation()
    except:
        print(
            "Failed to re-enable allocation - "
            "you will need to enable it again using the "
            "'elasticsearch.enable_reallocation' fabric command"
        )
        raise


@task
@serial
@runs_once
def redis_safe_reboot():
    """Reboot only if no logs in queue"""
    log_length = run('redis-cli llen logs')
    if log_length == '(integer) 0':
        execute(vm.reboot, hosts=[env['host_string']])
