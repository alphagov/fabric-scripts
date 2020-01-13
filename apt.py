from fabric.tasks import task


@task
def updates(context):
    """Show package counts needing updates"""
    run("cat /var/lib/update-notifier/updates-available")


@task
def security_updates(context):
    """Show outstanding security updates"""
    run("/usr/local/bin/govuk_check_security_upgrades --human-readable")


@task
def unattended_upgrade(context):
    """Perform an unattended-upgrade"""
    sudo("unattended-upgrade -d")


@task
def unattended_upgrade_dry_run(context):
    """Perform an unattended-upgrade dry run"""
    sudo("unattended-upgrade -d --dry-run")


@task(default=True)
def packages_with_reboots(context, *args):
    """Find out the packages that require a reboot"""
    package_reboot_file = '/var/run/reboot-required.pkgs'
    sudo('if [ -f {0} ]; then cat {0}; else echo No packages with reboots; fi'.format(package_reboot_file))


@task
def reset_reboot_needed(context, *args):
    """Delete the flag file that triggers the 'reboot required by apt' Nagios check"""
    sudo('rm -f /var/run/reboot-required')


@task
def autoremove(context):
    """Run `apt-get autoremove`"""
    sudo('apt-get autoremove')


@task
def autoremove_dry_run(context):
    """Run `apt-get autoremove` dry run"""
    sudo('apt-get autoremove --dry-run')


@task
def update(context):
    """Run `apt-get update`"""
    sudo('apt-get update')
