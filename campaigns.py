from fabric.api import env, roles, settings, sudo, task, execute


env['eagerly_disconnect'] = True


TEMPLATES = [
    'wrapper.html.erb',
    'homepage.html.erb',
    'header_footer_only.html.erb',
    'core_layout.html.erb',
]


@roles('class-frontend')
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


@roles('class-frontend')
def clear_frontend_cache():
    sudo("rm -rf /var/apps/frontend/tmp/cache/*")


@roles('class-frontend')
def clear_government_frontend_cache():
    sudo("rm -rf /var/apps/government-frontend/tmp/cache/*")


@roles('class-calculators_frontend')
def clear_finder_frontend_cache():
    sudo("rm -rf /var/apps/finder-frontend/tmp/cache/*")


@task
def clear_cached_templates():
    execute(clear_frontend_cache)
    execute(clear_static_generated_templates)
    execute(clear_government_frontend_cache)
    execute(clear_finder_frontend_cache)
