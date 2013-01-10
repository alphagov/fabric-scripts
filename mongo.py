from fabric.api import *
from datetime import *

today = date.today().strftime("%a %b %d")

@task(default=True)
@roles('class-mongo')
def replsetlogs(*args):
    """Grep the mongod logs for replSet today"""
    sudo('grep replSet /var/log/mongodb/mongod.log | grep "%s"' % today )
