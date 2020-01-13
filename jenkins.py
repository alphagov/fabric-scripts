from fabric.tasks import task


@task
def list_plugins(context):
    """List installed plugins with friendly name and versions"""
    sudo('jenkins-cli list-plugins')


@task
def list_plugin_versions(context):
    """List installed plugins with current version number"""
    sudo(r"jenkins-cli list-plugins |awk '{ if ($NF ~ /\(.*\)/) print $1, $(NF-1); else print $1, $NF }'")


@task
def plugins_requiring_updates(context):
    """List plugins requiring an update"""
    sudo(r"jenkins-cli |awk '{ if ($NF ~ /\(.*\)/) print $1 }'")


@task
def reload(context):
    """Reload configuration from disk"""
    sudo('jenkins-cli reload-configuration')


@task
def version(context):
    """Print the Jenkins version"""
    sudo('jenkins-cli version')
