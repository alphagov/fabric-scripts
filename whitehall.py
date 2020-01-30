from fabric.api import task, execute, runs_once
import util


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
