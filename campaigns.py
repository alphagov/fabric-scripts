from fabric.api import env, roles, settings, sudo, task


env['eagerly_disconnect'] = True


TEMPLATES = [
    'wrapper.html.erb',
    'homepage.html.erb',
    'header_footer_only.html.erb',
    'core_layout.html.erb',
]


def clear_static_generated_templates():
    """
    Our various frontend applications use the wrapper.html.erb,
    header_footer_only.html.erb and core_layout.html.erb layout templates.
    They get these templates using the Slimmer gem, which fetches
    these templates from the static application, located using ASSET_ROOT.

    When static is deployed there are no generated layout templates
    on static At the first request to one these, static will generate
    the template. The template will be placed in the public/template
    directory. From that point on, the templates are served by nginx.

    This function clears the public/template directory to force it to
    be regenerated to include the emergency campaign.
    """
    for template in TEMPLATES:
        with settings(warn_only=True):
            sudo('rm /var/apps/static/public/templates/{}'.format(template))


def clear_frontend_cache():
    sudo("rm -rf /var/apps/frontend/tmp/cache/*")


def clear_government_frontend_cache():
    sudo("rm -rf /var/apps/government-frontend/tmp/cache/*")


@task
@roles('class-frontend')
def clear_cached_templates():
    clear_frontend_cache()
    clear_static_generated_templates()
    clear_government_frontend_cache()
