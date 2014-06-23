from fabric.api import *
import cache

@task
@runs_once
@roles('class-cache')
def fastly_purge(*args):
    "Purge items from Fastly, eg \"/one,/two,/three\""
    for path in args:
        run("curl -s -X PURGE -H 'Host: www.gov.uk' http://www-gov-uk.map.fastly.net%s" % path.strip())
