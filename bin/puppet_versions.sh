#!/bin/sh

set -e

PS3='Please enter your choice: '
options=("training" "integration" "staging" "production" "quit")
select opt in "${options[@]}"
do
    case $opt in
        "training")
            environment="training"
            break
            ;;
        "integration")
            environment="integration"
            break
            ;;
        "staging")
            environment="staging"
            break
            ;;
        "production")
            environment="production"
            break
            ;;
        "quit")
            exit 0
            ;;
        *) echo invalid option;;
    esac
done

echo "Querying all servers, this will take a while..."
fab $environment all -P -z 10 puppet.config_version | grep -E "\[(.*)\] out: (.+)" | tr -d '[]' | awk -F ' out: ' ' { print $1 "," $2; }' > out.csv

echo "Processing server results..."
python bin/show_puppet_versions.py $environment out.csv

echo "Removing remporary file..."
rm out.csv

echo "Done!"
