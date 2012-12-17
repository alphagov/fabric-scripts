from fabric.api import *

@task
@roles('class-licensify-frontend', 'class-licensify-backend')
def greplogs(pattern, context=100):
    "Grep the logs for a pattern"
    grep_cmd = "zgrep -E '{pattern}' -C{context} /var/log/{app}/*{{.log,.gz}} 2>/dev/null || true"
    run(grep_cmd.format(app='licensify',       pattern=pattern, context=context))
    run(grep_cmd.format(app='licensify-admin', pattern=pattern, context=context))
    run(grep_cmd.format(app='licensify-feed',  pattern=pattern, context=context))

