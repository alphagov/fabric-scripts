import re
from fabric.tasks import task

ELASTICSEARCH_HOST = 'http://elasticsearch6:80'


def query_elasticsearch(path, method='GET', host=ELASTICSEARCH_HOST, *args, **kwargs):
    curl_command = "curl -X{method} '{host}/{path}'".format(
        method=method,
        host=host,
        path=path
    )
    return run(curl_command, *args, **kwargs)


@task
def delete(index, host=ELASTICSEARCH_HOST):
    """Delete an index"""
    if re.match('^[^/]+$', index):
        query_elasticsearch(index, method='DELETE', host=host)
    else:
        abort("Invalid index provided '%s'" % index)


@task
def status(index, host=ELASTICSEARCH_HOST):
    """Get the status of an index"""
    query_elasticsearch(index + '/_status', host=host)


@task
def cluster_health(host=ELASTICSEARCH_HOST):
    """Get cluster status"""
    return query_elasticsearch('/_cluster/health?pretty', host=host, warn_only=True)


@task
def check_recovery(index, host=ELASTICSEARCH_HOST):
    """Check status of an index recovery"""
    return query_elasticsearch(index + '/_recovery', host=host)
