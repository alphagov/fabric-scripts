from fabric.tasks import task


class HarvesterServiceStopped(Exception):
    pass


def restart_harvester_process(type):
    service_name = 'harvester_{type}_consumer-procfile-worker'.format(
        type=type)
    service_name_child = service_name + '_child'

    print('Checking status of:', service_name)

    with settings(abort_exception=HarvesterServiceStopped):
        try:
            check_started_command = 'initctl list | grep {service} | grep start'
            sudo(check_started_command.format(service=service_name_child))
        except HarvesterServiceStopped:
            print('Service has stopped, restarting...')
            sudo('initctl stop {service}'.format(service=service_name))
            sudo('initctl start {service}'.format(service=service_name))


@task
def restart_harvester_gather(context):
    """Restart gather harvester process."""

    restart_harvester_process('gather')


@task
def restart_harvester_fetch(context):
    """Restart fetch harvester process."""

    restart_harvester_process('fetch')


@task
def restart_harvester(context):
    """Restart harvester process."""

    restart_harvester_gather()
    restart_harvester_fetch()
