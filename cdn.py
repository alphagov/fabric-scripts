from fabric.api import *
from fabric.utils import abort

import cache

@task
@runs_once
@roles('class-cache')
def fastly_purge(*args):
    "Purge items from Fastly, eg \"/one,/two,/three\". Wildcards not supported."
    govuk_fastly = 'http://www-gov-uk.map.fastly.net'
    hostnames_to_purge = ['www.gov.uk', 'assets.digital.cabinet-office.gov.uk']
    for path in args:
        if "*" in path:
            abort("Sorry, purging paths containing wildcards is not supported "
                "(you requested to purge '%s'). "
                "See https://github.gds/pages/gds/opsmanual/2nd-line/cache-flush.html?highlight=fastly#purging-a-page-from-fastly-with-fabric"
                % path)
    for govuk_path in args:
        for hostname in hostnames_to_purge:
            run("curl -s -X PURGE -H 'Host: {0}' {1}{2} | grep 'ok'".format(hostname, govuk_fastly, govuk_path.strip()))

@task
def purge_all(*args):
    "Purge items from Fastly and cache machines, eg \"/one,/two,/three\""
    execute(cache.purge, *args)
    execute(fastly_purge, *args)
