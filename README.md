# GOV.UK Fabric Scripts

[Fabric](http://fabfile.org) is a command-line tool for application deployment
and systems administration tasks. It allows the user to run commands across a
server farm.

At GDS, we use Fabric to simplify and automate common systems administration
tasks. These scripts are deployed on our "jumpbox" machines at
`/usr/local/share/govuk-fabric`, and can be executed using the `govuk_fab`
helper script, installed in `/usr/local/bin`

## Usage

In order to use the fabric scripts, you will need to enable ssh-agent
forwarding when you connect to the jumpboxes. For example:

    $ ssh -A jumpbox-1.management.production

## Local usage

You can also use the fabric scripts from an external machine with a small amount
of setup on your part. You will need to install Fabric,

    $ pip install fabric

NB:Iif you get a "pip: command not found" error, run this first:

    $ sudo easy_install pip

configure it (see [the fabric documentation][fabdoc] for more examples),

    $ echo 'user = jimbob' >> ~/.fabricrc

and then you should be able to run it:

    $ fab preview all hosts
    ...
    $ fab preview class:frontend do:'uname -a'
    ...

[fabdoc]: http://docs.fabfile.org/en/latest/usage/fab.html

