from fabric.api import *
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
    """Get the status of an index"""
    return run("curl -XGET 'http://localhost:9200/_cluster/health'")

@task
def safe_reboot():
    """Reboot only if the cluster is currently green"""
    health = json.loads(cluster_health())
    if (health['status'] != 'green'):
        abort("Cluster health is %s, won't reboot" % health['status'])
    execute(vm.reboot)
