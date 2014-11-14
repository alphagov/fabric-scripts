import random

from fabric.api import env, cd, sudo

def use_random_host(role):
    """Use a randomly chosen host from the given role"""
    hosts = env.roledefs[role]()
    env.host_string = random.choice(hosts)

def rake(app, task, arguments = []):
    """Run a rake task for the specified application"""
    with cd('/var/apps/%s' % app):
        sudo('govuk_setenv "%s" bundle exec rake "%s[%s]"' % (app, task, (",").join(arguments)), user='deploy')
