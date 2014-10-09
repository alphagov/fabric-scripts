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
def reboot_safe_boxes(number="1"):
  """(NEEDS BADGER) Safely reboot a block of machines

  Reboot all machines which are:
    * safe to reboot[1]
    * not a datastore such as mongo or elasticsearch
    * not a monitoring box which will cause alert confusion if rebooted
    * are numbered "number" (default 1) in their group

  [1]: https://github.gds/pages/gds/opsmanual/2nd-line/rebooting-machines.html
  """
  if re.match('\A[1-7]\Z', number):
    numbered = re.compile('-{number}\\.'.format(number=number))
    env.hosts.extend(
        filter(numbered.search, SAFE_MACHINES)
    )
    vm.reboot()
