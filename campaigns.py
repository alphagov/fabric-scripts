import StringIO

from fabric.api import *
from fabric.operations import prompt
from fabric.tasks import execute

from jinja2 import Template

import app


env['eagerly_disconnect'] = True


APPLICATIONS = ['frontend', 'static']
CAMPAIGN_CLASSES = ['red', 'black', 'green']


def validate_classes(campaign_class):
    """Checks that the campaign class is valid"""
    if campaign_class in CAMPAIGN_CLASSES:
        return campaign_class
    raise Exception, "Invalid class {}, valid values are {}".format(campaign_class, CAMPAIGN_CLASSES)


@runs_once
def set_context():
    env['context'] = {
        'heading': prompt("Heading for campaign:", 'heading'),
        'extra_info': prompt("Extra information for campaign:", 'extra_info'),
        'more_info': prompt("Link for more information:", 'more_info'),
        'campaign_class': prompt("Campaign class:", 'campaign_class', validate=validate_classes)
    }


def template(app):
    if app == 'frontend':
      template = Template("""<div id="campaign" class="{{ campaign_class }}">
    <div class="campaign-inner">
      <h1>{{ heading|e }}</h1>
      <p>{{ extra_info|e }}</p>
      <a href="{{ more_info|e }}">More information</a>
    </div>
  </div>""")
    elif app == 'static':
      template = Template("""<p>{{ heading|e }}<br />
    {{ extra_info|e }}</p>
  <a href="#" class="right">{{ more_info|e }}</a>""")

    env['template_contents'] = template.render(env.context)


@task
@roles('class-frontend')
def deploy_banner(application):
    execute(template, application)
    if application == 'frontend':
        remote_filename = '/var/apps/frontend/app/views/root/_campaign_notification.html.erb'
    elif application == 'static':
        remote_filename = "/var/apps/static/app/views/notifications/banner_{}.erb".format(env.campaign_class)
    content = env['template_contents']
    put(StringIO.StringIO(content), remote_filename, use_sudo=True, mirror_local_mode=True)
    sudo('chown deploy:deploy %s' % remote_filename)
    execute(app.reload, application)

def remove_banner(application):
    if application == 'frontend':
        remote_filenames = ['/var/apps/frontend/app/views/root/_campaign_notification.html.erb']
    elif application == 'static':
        remote_filenames = ["/var/apps/static/app/views/notifications/banner_%s.erb" % i for i in CAMPAIGN_CLASSES]
    content = ''
    for remote_filename in remote_filenames:
        put(StringIO.StringIO(content), remote_filename, use_sudo=True, mirror_local_mode=True)
        sudo('chown deploy:deploy %s' % remote_filename)
    execute(app.reload, application)


@task
@roles('class-frontend')
def deploy_emergency_banner():
    """Deploy an emergency banner to GOV.UK"""
    execute(set_context)
    for application in APPLICATIONS:
        deploy_banner(application)

@task
@roles('class-frontend')
def remove_emergency_banner():
    """Remove all banners from GOV.UK"""
    for application in APPLICATIONS:
        remove_banner(application)
