#!/bin/sh
set -eu

DEPLOY_TO="$(grep -E 'jumpbox-[0-9]+' /etc/ssh/ssh_known_hosts | awk '{ print $1 }' | xargs)"

for server in $DEPLOY_TO; do
  rsync -av --delete --exclude='.git' "$(pwd)/" "deploy@${server}":/usr/local/share/govuk-fabric/
done 
