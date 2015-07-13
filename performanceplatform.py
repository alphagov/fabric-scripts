from fabric.api import (cd, task, hosts, sudo)


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


def run_stagecraft_postgres_command(sql_command):
    with cd('/'):
        # Run this command from the root directory so that we don't see errors
        # accessing the users
        # home directory as the postgres user.
        sudo('psql stagecraft -c "{0}"'.format(sql_command), user='postgres')
