from fabric.api import *


def run_mysql_command(cmd):
    with shell_env(HOME='/root'):
        sudo('mysql -e "{}"'.format(cmd))


def switch_slow_query_log(value):
    run_mysql_command('SET GLOBAL slow_query_log = "{}"'.format(value))


@task
def stop_slow_query_log(*args):
    switch_slow_query_log('OFF')


@task
def start_slow_query_log(*args):
    switch_slow_query_log('ON')


@task
def fix_replication_from_slow_query_log_after_upgrade():
    """
    Used to fix issues seen when upgrading mysql

    If you see the error
    'Error 'You cannot 'ALTER' a log table if logging is enabled' on query.

    when running show slave status, after a mysql upgrade, it is resolved by
    running this task
    """
    run_mysql_command("STOP SLAVE;")
    run_mysql_command("SET GLOBAL slow_query_log = 'OFF';")
    run_mysql_command("START SLAVE;")
    run_mysql_command("SET GLOBAL slow_query_log = 'ON';")
    run_mysql_command("show slave status\G;")
