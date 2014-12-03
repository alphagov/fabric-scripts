import random

from fabric.api import env, cd, sudo

def use_random_host(role):
    """Use a randomly chosen host from the given role"""
    hosts = env.roledefs[role]()
    env.host_string = random.choice(hosts)

def rake(app, task, *args, **params):
    """Run a rake task for the specified application

    If given positional arguments, converts them to rake's square bracket
    syntax (ie, rake foo[arg1,arg2,...])

    If given named arguments, converts them to environment variable syntax (ie,
    rake foo key1=val1 key2=val2)

    """
    with cd('/var/apps/%s' % app):
        cmd = "govuk_setenv '%s' bundle exec rake '%s'" % (app, task)

        if args:
            for arg in args:
                if ',' in arg or ']' in arg or "'" in arg:
                    raise RuntimeError("Can't pass arguments containing any of ,]' to rake")
            cmd += "'[" + ','.join(args) + "]'"

        if params:
            for key, value in params.items():
                if '=' in key or "'" in key:
                    raise RuntimeError("Can't have = or ' in rake environment keys")
                if "'" in value:
                    raise RuntimeError("Can't have ' in rake environment values")
            cmd += ' ' + ' '.join(
                "'%s=%s'" % (key, value)
                for (key, value) in params.items()
            )

        sudo(cmd, user='deploy')
