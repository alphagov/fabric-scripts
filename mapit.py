from fabric.api import task, settings, sudo, env, run
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


@task
def check_database_upgrade():
    """Replay yesterday's Mapit requests to ensure that a database upgrade works"""

    sudo("awk '$9==200 {print \"http://localhost\" $7}' /var/log/nginx/mapit.access.log.1 > mapit-200s")
    sudo("awk '$9==404 {print \"http://localhost\" $7}' /var/log/nginx/mapit.access.log.1 > mapit-404s")

    print "Replaying Mapit 200s. Ensure that they are all still 200s."
    run('while read line; do curl -sI $line | grep HTTP/1.1 ; done < mapit-200s | sort | uniq -c')
    print "Replaying Mapit 404s. Ensure that they are all either 200s or 404s."
    run('while read line; do curl -sI $line | grep HTTP/1.1 ; done < mapit-404s | sort | uniq -c')

    sudo('rm ~/mapit-200s ~/mapit-404s')
