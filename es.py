from fabric.api import *

@task
def delete(index):
    """Delete an index"""
    run("curl -XDELETE 'http://localhost:9200/%s'" % index)

@task
def status(index):
    """Get the status of an index"""
    run("curl -XGET 'http://localhost:9200/%s/_status'" % index)

@task
def cluster_health():
    """Get the status of an index"""
    run("curl -XGET 'http://localhost:9200/_cluster/health'")
