from fabric.api import task, execute, runs_once
import util


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
def dedupe_stats_announcement(duplicate_slug, authoritative_slug, noop=False):
    """De-duplicate Whitehall statistics announcement"""
    option = ' -n' if noop else ''
    command = './script/dedupe_stats_announcement{} {} {}'.format(
        option, duplicate_slug, authoritative_slug)

    util.bundle_exec('whitehall', command)


@task
@runs_once
def overdue_scheduled_publications():
    """List overdue scheduled publications"""
    util.rake('whitehall', 'publishing:overdue:list')


@task
@runs_once
def schedule_publications():
    """Publish overdue scheduled publications"""
    util.rake('whitehall', 'publishing:overdue:publish')


@task
@runs_once
def unpublish_statistics_announcement(*slugs):
    """Unpublish statistics announcements and register 410 GONE routes"""
    for slug in slugs:
        util.rake('whitehall', 'unpublish_statistics_announcement', slug)
