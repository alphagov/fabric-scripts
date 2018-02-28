from fabric.api import task, hosts
import util


@task
@hosts('email-alert-api-1.backend')
def deliver_test_email(address):
    """Delivers a test email to address"""
    util.rake('email-alert-api', 'deliver:to_test_email', address)


@task
@hosts('email-alert-api-1.backend')
def truncate_tables():
    """Truncates tables - ONLY USE ON INITIAL DEPLOY"""
    util.rake('email-alert-api', 'deploy:truncate_tables')
