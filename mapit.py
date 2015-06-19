from fabric.api import task, settings, sudo, env
from fabric.tasks import execute

import app
import nginx
import puppet

@task
def update_database():
    """Update a Mapit database using a new database dump"""

    if len(env.hosts) > 1:
      exit('This command should only be run on one Mapit machine at a time')

    execute(nginx.gracefulstop)
    execute(app.stop, 'mapit')
    sudo('service collectd stop')

    sudo('rm /data/vhost/mapit/data/mapit.sql.gz')

    with settings(sudo_user='postgres'):
      sudo("psql -c 'DROP DATABASE mapit;'")

    execute(puppet.agent, '--test')
