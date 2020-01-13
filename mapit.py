import app
import nginx
import puppet

from fabric.tasks import task

@task
def update_database_via_app(context):
    """Update a Mapit database from a new database dump using scripts in the app (new mapit-*.api servers)"""

    if len(env.hosts) > 1:
        exit('This command should only be run on one Mapit machine at a time')

    _stop_mapit_services()

    # This script needs to run as a user that can sudo to become the postgres
    # user.  It's easiest if this is passwordless, so we can't use the
    # `command` helper to run the script as that becomes the deploy user who
    # can't sudo without a password
    with cd('/var/apps/mapit'):
        run('govuk_setenv mapit ./import-db-from-s3.sh')

    _restart_mapit_services()


def _stop_mapit_services(context):
    # Stop puppet so that any scheduled runs don't happen while we are doing
    # our work
    execute(puppet.disable, 'Updating mapit database which requires stopping some services we would not want a scheduled puppet run to restart before we were done')
    # Stop NginX so that no requests reach this machine
    execute(nginx.gracefulstop)
    # Stop mapit and collectd which are using the Mapit database so that we can drop it
    execute(app.stop, 'mapit')
    sudo('service collectd stop')
    # Make sure that cached mapit responses are cleared when the database is updated
    sudo('service memcached restart')


def _restart_mapit_services(context):
    # Restart services in reverse order so that nginx comes up last - we don't
    # want to start sending traffic to the app before the app itself is running
    sudo('service collectd start')
    execute(app.start, 'mapit')
    execute(nginx.start)
    execute(puppet.enable)


@task
def check_database_upgrade(context):
    """Replay yesterday's Mapit requests to ensure that a database upgrade works"""

    sudo("awk '$9==200 {print \"http://localhost:3108\" $7}' /var/log/nginx/mapit.publishing.service.gov.uk-access.log.1 | sort | uniq > mapit-200s")
    sudo("awk '$9==404 {print \"http://localhost:3108\" $7}' /var/log/nginx/mapit.publishing.service.gov.uk-access.log.1 | sort | uniq > mapit-404s")
    sudo("awk '$9==302 {print \"http://localhost:3108\" $7}' /var/log/nginx/mapit.publishing.service.gov.uk-access.log.1 | sort | uniq > mapit-302s")

    print("Replaying Mapit 200s. Ensure that they are all still 200s.")
    print("NOTE: Some 404s may result if internal ids have changed because /area/<code> will redirect to /area/<internal-id> - this should be a low number and for /area/ urls only")
    run('while read line; do curl -sI $line | grep HTTP/1 ; done < mapit-200s | sort | uniq -c')
    print("Replaying Mapit 404s. Ensure that they are all either 200s or 404s.")
    run('while read line; do curl -sI $line | grep HTTP/1 ; done < mapit-404s | sort | uniq -c')
    print("Replaying Mapit 302s. Ensure that they are all still 302s. (these should be the /area/<code> redirects mentioned above)")
    run('while read line; do curl -sI $line | grep HTTP/1 ; done < mapit-302s | sort | uniq -c')

    sudo('rm ~/mapit-200s ~/mapit-404s ~/mapit-302s')
