from fabric.api import roles, run, sudo, task


@task
@roles('class-jenkins')
def engage_dr():
    """Failover openconnect to use the DR VPN and disable Puppet"""
    run('govuk_puppet --disable "Failed over to DR VPN"')
    sudo("sed -i 's/vpn.digital.cabinet-office.gov.uk/vpndr.digital.cabinet-office.gov.uk/' /etc/init/openconnect.conf")
    sudo("service openconnect restart")
