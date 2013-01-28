#!/bin/sh
set -eu

govuk_node_list -c jumpbox | while read server; do
  rsync -av --delete --exclude='.git' "$(pwd)/" "deploy@${server}":/usr/local/share/govuk-fabric/
done 
