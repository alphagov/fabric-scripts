from os.path import join
from fabric.tasks import task
# from fabric.utils import error
# import fabric.contrib.files

import puppet

config_file_locations = [
    '/home/deploy',
    '/var/lib/jenkins'
]

config_file_suffix = '.bundle/config'


def get_bundler_config(context):
    for prefix in config_file_locations:
        location = join(prefix, config_file_suffix)
        if fabric.contrib.files.exists(location, use_sudo=True):
            return location

    error('Could not find bundler config file.')


@task
def failover_to_rubygems(context):
    """Change bundler to use rubygems.org for gems rather than gemstash"""
    bundler_config = get_bundler_config()
    puppet.disable('Fabric failover_to_rubygems invoked')
    # Overwrite the bundler config with an empty file to force failover to default
    # Use an empty file rather than rm to avoid running rm as sudo.
    sudo('echo "" > {0}'.format(bundler_config))
    print('Disabled puppet and overwritten the bundler config file.')
    print('Run "bundler.revert_mirror" to start using gemstash again.')


@task
def revert_mirror(context):
    puppet.enable()
    puppet.agent()
    get_bundler_config()
    print('Puppet has been re-enabled. The bundler config file should be in it\'s usual state.')
