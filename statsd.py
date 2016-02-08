import re
from fabric.api import run, task


@task
def create_counter(name):
    """Creates a statsd counter on the target host.

    Enter metric of the form foo-1_bar_production.giraffes.eating

    A prefix of 'stats.' is added to your counter automatically, you
    do not need to specify that with this command.

    Read about carbon-aggregator counters before using this task:
    https://github.gds/pages/gds/opsmanual/2nd-line/nagios.html#nginx-5xx-rate-too-high-for-many-apps-boxes"""
    # remove an initial stats. prefix if present
    name = re.sub(r"^stats\.", "", name)
    run("echo -n '%s:0|c' > /dev/udp/localhost/8125" % name)
