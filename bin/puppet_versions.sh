#!/bin/sh

set -e

PS3='Please enter your choice: '
options=("integration" "staging" "production" "quit")
select opt in "${options[@]}"
do
    case $opt in
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
            echo "Exiting..."
            exit 0
            ;;
        *) echo invalid option;;
    esac
done

fab $environment all -P -z 10 puppet.config_version | grep -E "\[(.*)\] out: (.+)" | tr -d '[]' | awk -F ' out: ' ' { print $1 "," $2; }' > out.csv
python bin/show_puppet_versions.py $environment out.csv
rm out.csv
