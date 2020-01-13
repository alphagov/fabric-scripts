from fabric.tasks import task

@task
def version_in_use(version):
    """Tests whether an rbenv version is in use on a machine."""

    rbenv_path = '/usr/lib/rbenv/versions/{0}/'.format(version)

    with hide('running'):
        with hide('output'):
            if exists(rbenv_path):
                pids = sudo("lsof +D {0} | tail -n +2 | tr -s ' ' | cut -f 2 -d ' ' | sort -n | uniq".format(rbenv_path)).split('\r\n')
            else:
                pids = []
        for pid in pids:
            if pid == '':
                continue
            run('ps --no-headers {0}'.format(pid))
