from fabric.api import abort, sudo, task, cd
import fabric.contrib.files
import puppet

maintenance_config = '/etc/nginx/includes/maintenance.conf'

valid_apps = set([
    "collections-publisher",
    "contacts-admin",
    "search-admin",
    "service-manual-publisher",
    "content-tagger",
    "content-publisher",
    "publisher",
    "manuals-publisher",
    "short-url-manager",
    "specialist-publisher",
    "hmrc-manuals-api",
    "maslow",
    "travel-advice-publisher",
])

maintenance_setting = 'set $maintenance 1'


@task
def enable_maintenance(*app_list):
    """Enables a maintenance page for publishers and serves a 503"""
    """Only to be run on loadbalancers"""
    if not fabric.contrib.files.exists(maintenance_config):
        abort("Sorry this task can only currently be run on loadbalancers")
    puppet.disable("Maintenance mode enabled")
    env_url_post = fabric.state.env.gateway.lstrip("jumpbox.")
    app_list = list(app_list)
    if not valid_apps.issuperset(app_list):
        print("{} are not valid apps for this maintenance.".format(
            list(set(app_list).difference(valid_apps))))
        exit(1)
    for app in app_list:
        app_hostname = "{}.{}".format(app, env_url_post)
        app_config_file = "/etc/nginx/sites-enabled/{}".format(app_hostname)
        if app == "content-publisher":
            maintenance_setting = "limit_except GET { deny all; }"
        else:
            maintenance_setting = "set $maintenance 1;"
        fabric.contrib.files.sed(
            app_config_file,
            "include includes/maintenance.conf;",
            maintenance_setting,
            use_sudo=True,
            backup=".maint-bak"
        )
    with cd('/etc/nginx/sites-enabled/'):
        sudo('rm -f *.maint-bak')
    sudo('service nginx reload')
