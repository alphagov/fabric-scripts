from distutils.version import StrictVersion
from fabric.api import abort, hide, run, task
import json
import re


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


@task
def check_recovery(index):
    """Check status of an index recovery"""
    return run("curl -XGET 'http://localhost:9200/{index}/_recovery'".format(index=index))
