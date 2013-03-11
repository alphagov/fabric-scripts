#!/bin/sh
set -eu

govuk_node_list -c jumpbox | while read server; do
  rsync -av --delete --exclude='.git' "$(pwd)/" "deploy@${server}":/usr/local/share/govuk-fabric/
done
logger -p INFO -t jenkins "DEPLOYMENT: ${JOB_NAME} ${BUILD_NUMBER} (${BUILD_URL})"
