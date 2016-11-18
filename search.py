from fabric.api import abort, puts, task

import util

SEARCHABLE_APPS = {
    'calendars':               ('frontend',          ['panopticon:register']),

    # Includes the service-manual. Note: not included in gov.uk/search
    'designprinciples':        ('frontend',          ['rummager:index']),

    'frontend':                ('frontend',          ['rummager:index']),
    'licencefinder':           ('frontend',          ['panopticon:register']),
    'businesssupportfinder':   ('frontend',          ['panopticon:register']),
    'publisher':               ('backend',           ['panopticon:register']),
    'smartanswers':            ('frontend',          ['panopticon:register']),
    'tariff':                  ('frontend',          ['panopticon:register']),
    'travel-advice-publisher': ('backend',           ['panopticon:register', 'panopticon:reregister_editions']),
    'whitehall':               ('whitehall_backend', ['rummager:index']),
}


@task
def list():
    """List known searchable applications"""

    for app in sorted(SEARCHABLE_APPS.keys()):
        puts(app)


@task
def reindex(app=None):
    """

    Rebuild search indices

    To reindex all applications, run

      fab search.reindex

    To reindex only one application, e.g. calendars, you can do

      fab search.reindex:calendars

    """

    # If no argument is given, rebuild indices for all available applications
    if app is None:
        for app in SEARCHABLE_APPS.keys():
            reindex_app(app)

    else:
        if app not in SEARCHABLE_APPS:
            abort("I don't know anything about %s. Try updating SEARCHABLE_APPS in search.py." % app)
        reindex_app(app)


def reindex_app(app):
    puts("Rebuilding search index for application '%s'" % app)

    machine_class, rake_tasks = SEARCHABLE_APPS[app]
    util.use_random_host('class-%s' % machine_class)

    for rake_task in rake_tasks:
        util.rake(app, rake_task)


@task
def find_latest_snapshot():
    """Find the latest rummager snapshot"""
    util.rake('rummager', 'rummager:snapshot:latest')


@task
def find_snapshot_for_date(date):
    """Find the latest rummager snapshot before a date (YYYY-mm-dd HH:MM:SS)"""
    util.rake('rummager', 'rummager:snapshot:latest', date)


@task
def list_snapshots():
    """List rummager snapshots"""
    util.rake('rummager', 'rummager:snapshot:list')


@task
def restore_snapshot(snapshot, groups_to_restore):
    """Restore snapshots to new indices.

    `groups_to_restore` is either 'all' or a comma separated list of aliases.
    """
    util.rake(
        'rummager',
        'rummager:snapshot:restore',
        snapshot,
        RUMMAGER_INDEX=groups_to_restore
    )

    puts(
        "After the recovery is complete, switch to the new indexes with rummager.switch_group_to_index"
    )


@task
def switch_group_to_index(group, index_name):
    """Point a rummager index alias to a new index"""
    util.rake(
        'rummager',
        'rummager:switch_to_named_index',
        index_name,
        RUMMAGER_INDEX=group
    )
