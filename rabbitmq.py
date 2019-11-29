from fabric.api import env, execute, hide, sudo, task
from time import sleep
import re


@task
def status():
    """Output the RabbitMQ cluster status"""
    sudo('rabbitmqctl cluster_status', warn_only=True)


def cluster_is_ok():
    """Check if the cluster is okay.

    Returns True if so.  Prints a message and returns False if not.

    """
    with hide('everything'):
        status = sudo('rabbitmqctl cluster_status')
    # Expected status is something like:
    #
    # [{nodes,[{disc,['rabbit@rabbitmq-1','rabbit@rabbitmq-2',
    #                 'rabbit@rabbitmq-3']}]},
    # {running_nodes,['rabbit@rabbitmq-2','rabbit@rabbitmq-3','rabbit@rabbitmq-1']},
    # {cluster_name,<<"rabbit@rabbitmq-1.backend.production">>},
    # {partitions,[]}]
    #
    # We need to ensure that partitions is empty, and the list of running nodes
    # is the same as the list of known nodes.

    status = re.sub(r'\s', '', status)
    known_nodes = re.search(r'\{nodes,\[\{disc,\[([^]]+)\]', status)
    running_nodes = re.search(r'\{running_nodes,\[([^]]+)\]', status)
    partitions = re.search(r'\{partitions,\[([^]]*)\]', status)

    if not known_nodes or not running_nodes or not partitions:
        print(("No matches found in output: %r" % status))
        return False

    known_nodes = ','.join(sorted(known_nodes.group(1).split(',')))
    running_nodes = ','.join(sorted(running_nodes.group(1).split(',')))
    partitions = partitions.group(1)

    if known_nodes != running_nodes:
        print(("Known nodes differ from running nodes: %r and %r" %
              (known_nodes, running_nodes)))
        return False

    if partitions:
        print(("Cluster currently has a partition: %r" % partitions))
        return False

    return True


@task
def safe_reboot():
    """Reboot rabbitmq machines, waiting for cluster to be healthy first"""
    import vm
    while True:
        if cluster_is_ok():
            break
        print("Waiting for cluster to be okay")
        sleep(5)

    execute(vm.reboot, hosts=[env['host_string']])
    sleep(10)
