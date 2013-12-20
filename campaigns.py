import StringIO

from fabric.api import *
from fabric.operations import prompt
from fabric.tasks import execute

from jinja2 import Template

from vm import reload_unicorn

def validate_classes(campaign_class):
    """Checks that the campaign class is valid"""
    if campaign_class in ['red', 'black', 'green']:
        return campaign_class
    raise Exception, "Invalid class %s, valid values are 'red', 'black', 'green'" % campaign_class


@runs_once
def homepage_template():
    """Promotes a campaign to the homepage of GOV.UK"""
    context = {
        'heading': prompt("Heading for campaign:"),
        'extra_info': prompt("Extra information for campaign:"),
        'more_info': prompt("Link for more information:"),
        'campaign_class': prompt("Campaign class:", validate=validate_classes)
    }

    template = Template("""<div id="campaign" class="{{ campaign_class }}">
  <div class="campaign-inner">
    <h1>{{ heading|e }}</h1>
    <p>{{ extra_info|e }}</p>
    <a href="{{ more_info|e }}">More information</a>
  </div>
</div>""")
    env['template_contents'] = template.render(context)

    print "Template contents:\n%s" % env['template_contents']

@task
@roles('class-frontend')
def deploy_to_homepage():
    execute(homepage_template)

    contents = env['template_contents']

    remote_filename = '/var/apps/frontend/app/views/root/_campaign_notification.html.erb'
    put(StringIO.StringIO(contents), remote_filename, use_sudo=True, mirror_local_mode=True)
    sudo('chown deploy:deploy %s' % remote_filename)
    execute(reload_unicorn, name='frontend')

@task
@roles('class-frontend')
def remove_from_homepage():
    remote_filename = '/var/apps/frontend/app/views/root/_campaign_notification.html.erb'
    put(StringIO.StringIO(''), remote_filename, use_sudo=True, mirror_local_mode=True)
    sudo('chown deploy:deploy %s' % remote_filename)
    execute(reload_unicorn, name='frontend')
