import random
import re

from fabric.api import env, cd, sudo


def use_random_host(role):
    """Use a randomly chosen host from the given role"""
    hosts = env.roledefs[role]()
    env.host_string = random.choice(hosts)


def rake(app, task, *args, **params):
    """Run a rake task for the specified application

    If given positional arguments, converts them to rake's square bracket
    syntax (ie, rake foo[arg1,arg2,...])

    If given named arguments, converts them to environment variables (ie.
    KEY1=val1 KEY2=val2 rake foo)
    """
    if args:
        _validate_strings("rake variable",
                          args, bad_chars=",]'")
        task = "{}[{}]".format(task, ','.join(args))

    bundle_exec(app, task, **params)


def bundle_exec(app, cmd, **params):
    """Run any command through bundle exec for the specified application

    If given named arguments, converts them to environment variables (ie.
    KEY1=val1 KEY2=val2 command)
    """
    command(app, "bundle exec {}".format(cmd), **params)


def command(app, cmd, **params):
    """Run any command for the specified application

    If given named arguments, converts them to environment variables (ie.
    KEY1=val1 KEY2=val2 command)
    """
    env_vars = ""
    if params:
        _validate_strings("environment variable name",
                          params.keys(), pattern=r"^[A-Z_][A-Z_0-9]*$")
        _validate_strings("environment variable value",
                          params.values(), pattern=r"^[^']*$")
        env_vars = ' '.join(
            "{}='{}'".format(name, value)
            for (name, value) in params.items()) + ' '

    with cd('/var/apps/{}'.format(app)):
        sudo("{}govuk_setenv '{}' {}".format(env_vars, app, cmd),
             user='deploy')


def _validate_strings(label, strings, pattern=None, bad_chars=None):
    if pattern is not None:
        pattern = re.compile(pattern)

    for string in strings:
        if pattern is not None and not pattern.match(string):
            raise RuntimeError("Invalid {} '{}' must match {}".format(
                label, string, pattern.pattern))
        if bad_chars is not None and any(c in string for c in bad_chars):
            raise RuntimeError("Invalid {} '{}' must not contain {}".format(
                label, string, bad_chars))
