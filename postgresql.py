from fabric.tasks import task


@task
def sync(database, dest_machine):
    # the agent forwarding is required for the ssh command to the destination
    # postgres server to work - this saves copying a temporary file down and
    # back up again. We cant use fabrics sudo context manager because the
    # command after the pipe should not run as the postgres user.
    # The combination of "--schema public" and "--clean" in the pg_restore
    # command clears all existing tables in the public schema before restoring
    # the tables and data
    with settings(forward_agent=True):
        run('sudo -iupostgres pg_dump -Fc {0} | ssh {1} '
            '"sudo -upostgres pg_restore --clean --single-transaction '
            '--schema public --dbname {0}"'.format(database, dest_machine))


@task
def push_s3_backup(context):
    run('sudo -iu postgres /usr/local/bin/wal-e_postgres_base_backup_push')
