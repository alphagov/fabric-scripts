import random

from fabric.api import env, cd, sudo

def use_random_host(role):
    """Use a randomly chosen host from the given role"""
    env.host_string = random.choice(env.roledefs[role])

def rake(app, task):
    """Run a rake task for the specified application"""
    with cd('/var/apps/%s' % app):
        sudo('govuk_setenv "%s" bundle exec rake "%s"' % (app, task), user='deploy')
