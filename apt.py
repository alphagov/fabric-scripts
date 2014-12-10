from fabric.api import *

@task
def updates():
    """Show package counts needing updates"""
    run("cat /var/lib/update-notifier/updates-available")

@task
def security_updates():
    """Show outstanding security updates"""
    run("/usr/local/bin/govuk_check_security_upgrades --human-readable")

@task
def upgrade():
    """Upgrade packages with apt-get"""
    sudo("apt-get update; apt-get upgrade -y")

@task
def dist_upgrade():
    """Perform non-interactive dist-upgrade using apt-get"""
    prompt('dist-upgrade is a dangerous operation, can remove packages and generally break all the things. Are you sure you want to proceed? (y/n)', validate=r'^[Yy]$')
    sudo("apt-get -q update && DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::=\"--force-confdef\" -o Dpkg::Options::=\"--force-confold\" -yuq dist-upgrade")

@task
def unattended_upgrade():
    """Perform an unattended-upgrade"""
    sudo("unattended-upgrade -d")

@task
def unattended_upgrade_dry_run():
    """Perform an unattended-upgrade dry run"""
    sudo("unattended-upgrade -d --dry-run")

@task(default=True)
def packages_with_reboots(*args):
    """Find out the packages that require a reboot"""
    package_reboot_file = '/var/run/reboot-required.pkgs'
    sudo('if [ -f {0} ]; then cat {0}; else echo No packages with reboots; fi'.format(package_reboot_file))

@task
def reset_reboot_needed(*args):
    """Delete the flag file that triggers the 'reboot required by apt' Nagios check"""
    sudo('rm -f /var/run/reboot-required')

@task
def autoremove():
    """Run `apt-get autoremove`"""
    sudo('apt-get autoremove')

@task
def autoremove_dry_run():
    """Run `apt-get autoremove` dry run"""
    sudo('apt-get autoremove --dry-run')
