from fabric.api import *
import re
import vm

SAFE_MACHINES = [
    'api-1.api',                       'api-2.api',
    'api-lb-1.api',                    'api-lb-2.api',
    'apt-1.management',
    'backend-1.backend',               'backend-2.backend',               'backend-3.backend',
    'bouncer-1.redirector',            'bouncer-2.redirector',            'bouncer-3.redirector',
    'cache-1.router',                  'cache-2.router',                  'cache-3.router',
    'calculators-frontend-1.frontend', 'calculators-frontend-2.frontend', 'calculators-frontend-3.frontend',
    'content-store-1.api',             'content-store-2.api',             'content-store-3.api',
    'frontend-1.frontend',             'frontend-2.frontend',             'frontend-3.frontend',
    'frontend-lb-1.frontend',          'frontend-lb-2.frontend',
    'jenkins-1.management',
    'licensify-backend-1.licensify',   'licensify-backend-2.licensify',
    'licensify-frontend-1.licensify',  'licensify-frontend-2.licensify',
    'licensify-lb-1.licensify',        'licensify-lb-2.licensify',
    'mapit-server-1.backend',          'mapit-server-2.backend',
    'puppetmaster-1.management',
    'whitehall-backend-1.backend',     'whitehall-backend-2.backend',     'whitehall-backend-3.backend',
    'whitehall-backend-4.backend',     'whitehall-backend-5.backend',
    'whitehall-frontend-1.frontend',   'whitehall-frontend-2.frontend',   'whitehall-frontend-3.frontend',
    'whitehall-frontend-4.frontend',   'whitehall-frontend-5.frontend',   'whitehall-frontend-6.frontend',
    'whitehall-frontend-7.frontend',
]

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
  ones = re.compile('-1\\.')
  env.hosts.extend(
      filter(ones.search, SAFE_MACHINES)
  )
  vm.reboot()

@task
def reboot_safe_boxes_2():
  """GET THE BADGER BEFORE RUNNING THIS COMMAND

  Reboot all machines which are:
    * safe to reboot[1]
    * not a datastore such as mongo or elasticsearch
    * not a monitoring box which will cause alert confusion if rebooted
    * are numbered "2" in their group

  [1]: https://github.gds/pages/gds/opsmanual/2nd-line/rebooting-machines.html
  """
  twos = re.compile('-2\\.')
  env.hosts.extend(
      filter(twos.search, SAFE_MACHINES)
  )
  vm.reboot()

@task
def reboot_safe_boxes_3():
  """GET THE BADGER BEFORE RUNNING THIS COMMAND

  Reboot all machines which are:
    * safe to reboot[1]
    * not a datastore such as mongo or elasticsearch
    * not a monitoring box which will cause alert confusion if rebooted
    * are numbered "3" in their group

  [1]: https://github.gds/pages/gds/opsmanual/2nd-line/rebooting-machines.html
  """
  from vm import reboot
  threes = re.compile('-3\\.')
  env.hosts.extend(
      filter(threes.search, SAFE_MACHINES)
  )
  vm.reboot()
