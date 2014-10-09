from fabric.api import *

@task
def reboot_safe_boxes_1():
  """GET THE BADGER BEFORE RUNNING THIS COMMAND

  Reboot all machines which are:
    * safe to reboot[1]
    * not a datastore such as mongo or elasticsearch
    * not a monitoring box which will cause alert confusion if rebooted
    * are numbered "1" in their group

  [1]: https://github.gds/pages/gds/opsmanual/2nd-line/rebooting-machines.html
  """
  from vm import reboot
  env.hosts.extend(['api-1.api',
                    'api-lb-1.api',
                    'apt-1.management',
                    'backend-1.backend',
                    'bouncer-1.redirector',
                    'cache-1.router',
                    'calculators-frontend-1.frontend',
                    'content-store-1.api',
                    'efg-mysql-slave-1.efg',
                    'elasticsearch-1.backend',
                    'frontend-1.frontend',
                    'frontend-lb-1.frontend',
                    'jenkins-1.management',
                    'licensify-backend-1.licensify',
                    'licensify-frontend-1.licensify',
                    'licensify-lb-1.licensify',
                    'mapit-server-1.backend',
                    'puppetmaster-1.management',
                    'whitehall-backend-1.backend',
                    'whitehall-frontend-1.frontend',
                ])
  reboot()
