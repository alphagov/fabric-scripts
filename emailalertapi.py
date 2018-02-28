from fabric.api import task, hosts
import util


@task
@hosts('email-alert-api-1.backend')
def deliver_test_email(address):
    """Delivers a test email to address"""
    util.rake('email-alert-api', 'deliver:to_test_email', address)
