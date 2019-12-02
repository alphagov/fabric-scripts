from fabric.api import sudo, task


@task
def list_plugins():
    """List installed plugins with friendly name and versions"""
    sudo('jenkins-cli list-plugins')


@task
def list_plugin_versions():
    """List installed plugins with current version number"""
    sudo(r"jenkins-cli list-plugins |awk '{ if ($NF ~ /\(.*\)/) print $1, $(NF-1); else print $1, $NF }'")


@task
def plugins_requiring_updates():
    """List plugins requiring an update"""
    sudo(r"jenkins-cli |awk '{ if ($NF ~ /\(.*\)/) print $1 }'")


@task
def reload():
    """Reload configuration from disk"""
    sudo('jenkins-cli reload-configuration')


@task
def version():
    """Print the Jenkins version"""
    sudo('jenkins-cli version')
