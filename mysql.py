from fabric.api import abort, env, hide, run, settings, task
from fabric.operations import prompt


def run_mysql_command(cmd):
    run('sudo -i mysql -e "{}"'.format(cmd))


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
    Sets up a slave from a master by:
      - configuring MySQL replication config
      - using the replicate_slave_from_master task to do an initial dump to the slave

    Usage: fab environment -H mysql-slave-1.backend mysql.setup_slave_from_master:'mysql-master-1.backend'
    """
    if len(env.hosts) > 1:
        exit('This job is currently only setup to run against one slave at a time')

    mysql_master = prompt("Master host (eg 'master.mysql' or 'whitehall-master.mysql'):")
    replication_username = 'replica_user'
    replication_password = prompt("Password for MySQL user {0}:".format(replication_username))

    run_mysql_command("STOP SLAVE;")
    run_mysql_command("CHANGE MASTER TO MASTER_HOST='{0}', MASTER_USER='{1}', MASTER_PASSWORD='{2}';".format(
        mysql_master, replication_username, replication_password))

    replicate_slave_from_master(master)


@task
def replicate_slave_from_master(master):
    """
    Updates a slave from a master by taking a dump from the master,
    copying it to the slave and then restoring the dump.

    Usage: fab environment -H mysql-slave-1.backend mysql.replicate_slave_from_master:'mysql-master-1.backend'
    """
    if len(env.hosts) > 1:
        exit('This job is currently only setup to run against one slave at a time')

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

    with hide('running', 'stdout'):
        database_file_size = run("stat --format='%s' dump.sql")

    print(('Importing MySQL database which is {0}GB, this might take a while...'.format(round(int(database_file_size) / (1024 * 1024 * 1024 * 1.0), 1))))
    run('sudo -i mysql -uroot < dump.sql')

    run('rm dump.sql')

    run_mysql_command("START SLAVE")
    run_mysql_command("SET GLOBAL slow_query_log=ON")

    slave_status()


@task
def reset_slave():
    """
    Used to reset a slave if MySQL replication is failing

    If you see that the slave is 'NULL' seconds behind the master,
    the problem may be resolved by running this task.

    See docs on 'RESET SLAVE':
    https://dev.mysql.com/doc/refman/5.5/en/reset-slave.html
    """

    # Confirm slave status in case we need to refer to the values later
    slave_status()
    run_mysql_command("STOP SLAVE;")

    with hide('everything'):
        # Store last known log file and position
        master_log_file = run("sudo -i mysql -e 'SHOW SLAVE STATUS\G' | grep '^\s*Relay_Master_Log_File:' | awk '{ print $2 }'")
        master_log_pos = run("sudo -i mysql -e 'SHOW SLAVE STATUS\G' | grep '^\s*Exec_Master_Log_Pos:' | awk '{ print $2 }'")

        if not master_log_file or not master_log_pos:
            abort("Failed to determine replication log file and position, aborting.")

    # Forget log file and position
    run_mysql_command("RESET SLAVE;")

    # Repoint log file and position to last known values
    run_mysql_command("CHANGE MASTER TO MASTER_LOG_FILE='{}', MASTER_LOG_POS={};"
                      .format(master_log_file, master_log_pos))
    run_mysql_command("START SLAVE;")

    with hide('everything'):
        seconds_behind_master = run("sudo -i mysql -e 'SHOW SLAVE STATUS\G' | grep '^\s*Seconds_Behind_Master:' | awk '{ print $2 }'")

    # Compare as a string to ensure we got a non-nil value from MySQL
    if seconds_behind_master != '0':
        abort("Slave is still behind master by {} seconds; run mysql.slave_status to check status"
              .format(seconds_behind_master))


@task
def slave_status():
    """
    Show status of MySQL replication on slave; must be run against the slave host
    """
    run_mysql_command("SHOW SLAVE STATUS\G;")
