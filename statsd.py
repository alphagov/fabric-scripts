from fabric.api import *


@task
def create_counter(name):
    """Creates a statsd counter on the target host.

    Enter metric of the form foo-1_bar_production.giraffes.eating

    A prefix of 'stats.' is added to your counter automatically, you
    do not need to specify that with this command."""
    run("echo -n '%s:0|c' > /dev/udp/localhost/8125" % name)
