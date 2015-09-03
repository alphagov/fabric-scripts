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


@task
def setup_slave_from_master(master):
    """
    Sets up a slave from a master by taking a dump from the master,
    copying it to the slave and then restoring the dump.

    Usage: fab environment -H mysql-slave-1.backend mysql.setup_slave_from_master:'mysql-master-1.backend'
    """
    if len(env.hosts) > 1:
        print 'This job is currently only setup to run against one slave at a time'

    with settings(host_string=master):
        # The use of `--master-data` here implies `--lock-all-tables` per the
        # MySQL reference manual: http://dev.mysql.com/doc/refman/5.1/en/mysqldump.html#option_mysqldump_master-data
        run('sudo -i mysqldump -u root --all-databases --master-data --add-drop-database > dump.sql')

    with settings(host_string=master, forward_agent=True):
        run('scp dump.sql {0}:~'.format(env.hosts[0]))

    with settings(host_string=master):
        run('rm dump.sql')

    run_mysql_command("STOP SLAVE")
    run_mysql_command("SET GLOBAL slow_query_log=OFF")

    run('sudo -i mysql -uroot < dump.sql')

    run_mysql_command("START SLAVE")
    run_mysql_command("SET GLOBAL slow_query_log=ON")

    run_mysql_command("SHOW SLAVE STATUS\G")
