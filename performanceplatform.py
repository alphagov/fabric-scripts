import json

from fabric.api import (
    task, hosts, run, settings,
    sudo, get, shell_env, cd
)
from StringIO import StringIO


@task
@hosts('api-postgresql-primary-1.api')
def publish_dashboard(slug):
    """Publish the dashboard with the specified slug"""
    # This command is a temporary measure until the admin app supports a nice
    # workflow for publishing dashboards.
    sql_command = ("UPDATE dashboards_dashboard SET status='published'"
                   "WHERE slug='{0}'".format(slug))
    run_stagecraft_postgres_command(sql_command)


@task
@hosts('api-postgresql-primary-1.api')
def unpublish_dashboard(slug):
    """Unpublish the dashboard with the specified slug"""
    # This command is a temporary measure until the admin app supports a nice
    # workflow for publishing dashboards.
    sql_command = ("UPDATE dashboards_dashboard SET status='unpublished' "
                   "WHERE slug='{0}'".format(slug))
    run_stagecraft_postgres_command(sql_command)


@task
@hosts('performance-backend-1.backend')
def collect(data_group, data_type):
    """Run a collector config"""
    base_path = '/data/apps/performanceplatform-collector/current'

    with cd(base_path):
        query_path = './config/queries/{}/{}.json'.format(
            data_group, data_type)

        query = get_file_contents(query_path)

        command = get_command(query_path, query)
        print('Executing: {}'.format(command))
        with settings(sudo_user='deploy'):
            with shell_env(LOGLEVEL='debug'):
                sudo(command)


def get_command(query_path, query):
    """
    >>> get_command('/tmp/foo/bar', {'entrypoint': 'foo.bar.monkey', 'token': 'foo'})
    './venv/bin/pp-collector -q /tmp/foo/bar -c ./config/credentials/monkey.json -t ./config/tokens/foo.json -b ./config/performanceplatform.json --console-logging'
    """
    credentials = query['entrypoint'].split('.')[-1]

    # realtime uses GA credentials, gcloud needs none but pp-collector fails with none
    if credentials in ['realtime', 'gcloud', 'trending']:
        credentials = 'ga'

    pp_collector = './venv/bin/pp-collector'
    credentials_path = './config/credentials/{}.json'.format(credentials)
    token_path = './config/tokens/{}.json'.format(
    query['token'])
    platform_path = './config/performanceplatform.json'

    return '{} -q {} -c {} -t {} -b {} --console-logging'.format(
        pp_collector, query_path, credentials_path, token_path, platform_path)


def get_file_contents(path):
    fd = StringIO()
    get(path, fd)
    return json.loads(fd.getvalue())


def run_stagecraft_postgres_command(sql_command):
    run('sudo -iu postgres psql stagecraft -c "{0}"'.format(sql_command))
