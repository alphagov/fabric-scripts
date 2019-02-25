from fabric.api import abort, run, task
import re

ELASTICSEARCH_HOST = 'http://localhost:9200'


def query_elasticsearch(path, method='GET', host=ELASTICSEARCH_HOST, *args, **kwargs):
    curl_command = "curl -X{method} '{host}/{path}'".format(
        method=method,
        host=host,
        path=path
    )
    return run(curl_command, *args, **kwargs)


@task
def delete(index):
    """Delete an index"""
    if re.match('^[^/]+$', index):
        query_elasticsearch(index, method='DELETE')
    else:
        abort("Invalid index provided '%s'" % index)


@task
def status(index):
    """Get the status of an index"""
    query_elasticsearch(index + '/_status')


@task
def cluster_health():
    """Get cluster status"""
    return query_elasticsearch('/_cluster/health?pretty', warn_only=True)


@task
def check_recovery(index):
    """Check status of an index recovery"""
    return query_elasticsearch(index + '/_recovery')
