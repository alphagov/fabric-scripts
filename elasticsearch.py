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
    """Get cluster status"""
    return run("curl -XGET 'http://localhost:9200/_cluster/health?pretty'")

@task
def cluster_nodes():
    """Get cluster nodes"""
    return run("curl -XGET 'http://localhost:9200/_cluster/nodes?pretty'")

@task
@serial
@runs_once
def safe_reboot():
    """Reboot only if the cluster is currently green"""
    health = json.loads(cluster_health())
    if (health['status'] != 'green'):
        abort("Cluster health is %s, won't reboot" % health['status'])
    execute(vm.reboot, hosts=[env['host_string']])


@task
@serial
@runs_once
def redis_safe_reboot():
    """Reboot only if no logs in queue"""
    log_length = run('redis-cli llen logs')
    if log_length == '(integer) 0':
        execute(vm.reboot, hosts=[env['host_string']])
