from fabric.api import *

@task
@roles('class-licensify-frontend', 'class-licensify-backend')
def greplogs(pattern, context=100):
    "Grep the logs for a pattern"
    grep_cmd = "[ -f /var/apps/{app}/logs/application.log ] && egrep '{pattern}' -C{context} /var/apps/{app}/logs/application.log || :"
    run(grep_cmd.format(app='licensify',       pattern=pattern, context=context))
    run(grep_cmd.format(app='licensify-admin', pattern=pattern, context=context))
    run(grep_cmd.format(app='licensify-feed',  pattern=pattern, context=context))

