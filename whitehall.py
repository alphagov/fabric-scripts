from fabric.api import task, hosts, sudo, cd, execute


@task
def dedupe_stats_announcement_from_file(filename):
    """De-duplicate Whitehall statistics accouncements from a CSV file"""
    with open(filename) as fd:
        duplicates = [line.strip().split(',') for line in fd]
        for duplicate_slug, authoritative_slug in duplicates:
            execute(
                dedupe_stats_announcement, duplicate_slug, authoritative_slug)


@task
@hosts('whitehall-backend-1.backend')
def dedupe_stats_announcement(duplicate_slug, authoritative_slug):
    """De-duplicate Whitehall statistics announcement"""
    command = 'govuk_setenv whitehall ./script/dedupe_stats_announcement {} {}'
    with cd('/var/apps/whitehall'):
        sudo(command.format(duplicate_slug, authoritative_slug),
             user='deploy')
