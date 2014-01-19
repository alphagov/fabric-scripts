from fabric.api import *

@task
def updates():
    """Show package counts needing updates"""
    run("cat /var/lib/update-notifier/updates-available")

@task
def upgrade():
    """Upgrade packages with apt-get"""
    sudo("apt-get update; apt-get upgrade -y")

@task
def dist_upgrade():
    """Perform non-interactive dist-upgrade using apt-get"""
    sudo("apt-get -q update && DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::=\"--force-confdef\" -o Dpkg::Options::=\"--force-confold\" -yuq dist-upgrade")

@task(default=True)
def packages_with_reboots(*args):
    """Find out the packages that require a reboot"""
    sudo('cat /var/run/reboot-required.pkgs')

@task
def reset_reboot_needed(*args):
    """Delete the flag file that triggers the 'reboot required by apt' Nagios check"""
    sudo('rm -f /var/run/reboot-required')
