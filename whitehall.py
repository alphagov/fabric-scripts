from fabric.api import task, sudo, cd, execute, runs_once, roles


@task
def dedupe_stats_announcement_from_file(filename):
    """De-duplicate Whitehall statistics accouncements from a CSV file"""
    with open(filename) as fd:
        duplicates = [line.strip().split(',') for line in fd]
        for duplicate_slug, authoritative_slug in duplicates:
            execute(
                dedupe_stats_announcement, duplicate_slug, authoritative_slug)


@task
@runs_once
@roles('class-whitehall_backend')
def dedupe_stats_announcement(duplicate_slug, authoritative_slug, noop=False):
    """De-duplicate Whitehall statistics announcement"""
    option = ' -n' if noop else ''
    command = './script/dedupe_stats_announcement{} {} {}'.format(
        option, duplicate_slug, authoritative_slug)

    _run_whitehall_command(command)


@task
@runs_once
@roles('class-whitehall_backend')
def unarchive_content(*edition_ids):
    """Unarchive Whitehall content"""
    for edition_id in edition_ids:
        _run_whitehall_rake('unarchive_edition[{}]'.format(edition_id))


@task
@runs_once
@roles('class-whitehall_backend')
def overdue_scheduled_publications():
    """List overdue scheduled publications"""
    _run_whitehall_rake('publishing:overdue:list')


@task
@runs_once
@roles('class-whitehall_backend')
def schedule_publications():
    """Publish overdue scheduled publications"""
    _run_whitehall_rake('publishing:overdue:publish')


@task
@runs_once
@roles('class-whitehall_backend')
def unpublish_statistics_announcement(*slugs):
    """Unpublish statistics announcements and register 410 GONE routes"""
    for slug in slugs:
        _run_whitehall_rake(
            'unpublish_statistics_announcement[{}]'.format(slug))


def _run_whitehall_rake(task):
    _run_whitehall_command('rake {}'.format(task))


def _run_whitehall_command(command):
    with cd('/var/apps/whitehall'):
        sudo('govuk_setenv whitehall bundle exec {}'.format(command),
             user='deploy')
