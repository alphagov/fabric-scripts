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


@task
@runs_once
def homepage_env():
    """Promotes a campaign to the homepage of GOV.UK"""
    prompt("Heading for campaign:", key='homepage_heading')
    prompt("Extra information for campaign:", key='homepage_extra_info')
    prompt("Link for more information:", key='homepage_more_info')
    prompt("Campaign class:", key='homepage_campaign_class', validate=validate_classes)

@task
@roles('class-frontend')
def deploy_to_homepage():
    execute(homepage_env)
    template = Template("""<div id="campaign" class="{{ homepage_campaign_class }}">
  <div class="campaign-inner">
    <h1>{{ homepage_heading|e }}</h1>
    <p>{{ homepage_extra_info|e }}</p>
    <a href="{{ homepage_more_info|e }}">More information</a>
  </div>
</div>""")
    contents = template.render(env)

    remote_filename = '/var/apps/frontend/app/views/root/_campaign_notification.html.erb'
    put(StringIO.StringIO(contents), remote_filename, use_sudo=True, mirror_local_mode=True)
    sudo('chown deploy:deploy %s' % remote_filename)
    execute(reload_unicorn, name='frontend')
    print "Campaign deployed. Please ensure this is copied into the frontend repository to ensure it's stable across deploys"

@task
@roles('class-frontend')
def remove_from_homepage():
    remote_filename = '/var/apps/frontend/app/views/root/_campaign_notification.html.erb'
    put(StringIO.StringIO(''), remote_filename, use_sudo=True, mirror_local_mode=True)
    sudo('chown deploy:deploy %s' % remote_filename)
    execute(reload_unicorn, name='frontend')
