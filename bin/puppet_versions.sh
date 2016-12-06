#!/bin/sh

set -e

read -p "Enter the environment: " environment

fab $environment all -P -z 10 puppet.config_version | grep -E "\[(.*)\] out: (.+)" | tr -d '[]' | awk -F ' out: ' ' { print $1 "," $2; }' > out.csv
python bin/show_puppet_versions.py $environment out.csv
rm out.csv
