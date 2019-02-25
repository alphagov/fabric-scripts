from fabric.api import abort, run, task
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
def check_recovery(index):
    """Check status of an index recovery"""
    return run("curl -XGET 'http://localhost:9200/{index}/_recovery'".format(index=index))
