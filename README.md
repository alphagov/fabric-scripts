# GOV.UK Fabric Scripts

[Fabric](http://fabfile.org) is a command-line tool for application deployment
and systems administration tasks. It allows the user to run commands across a
server farm.

This repository is intended to be setup and run on your local workstation/laptop.

## Setup

To install the dependencies:

    $ pip install -Ur requirements.txt

NB: if you get a "pip: command not found" error, run this first:

    $ sudo easy_install pip

Configure it (see [the fabric documentation][fabdoc] for more examples),

    $ echo 'user = your_username' >> ~/.fabricrc

[fabdoc]: https://docs.fabfile.org/en/2.4/concepts/configuration.html

## Commands

You can view a list of the available tasks:

    $ fab -l

And execute against an environment and set of hosts like so:

    $ fab preview all hosts
    ...
    $ fab preview class:frontend do:'uname -a'
    ...

## Targeting groups of machines

Fabric tasks can be run on groups of machines in a variety of different ways.

By Puppet class:

    # target all machines that have the 'govuk::safe_to_reboot::yes' class
    $ fab preview puppet_class:govuk::safe_to_reboot::yes do:'uname -a'

By numeric machine suffix:

    # target all machines that end in '2'
    $ fab preview numbered:2 do:'uname -a'

By node type (as defined in Puppet):

    # target all 'frontend' machines
    $ fab preview node_type:frontend do:'uname -a'

By the node name:

    # target just one node
    $ fab production -H backend-3.backend do:'uname -a'

## Syncing postgres machines

An example

`fab <env> -H '<src_db>' postgresql.sync:<db_name>,<dst_db> -A`

the -A must be specified to forward the agent

This will sync the specified database `<db_name>` from the machine with the
hostname of `<src_db>` to the machine with hostaname `<dst_db>`. It will destroy
data on the destination db
