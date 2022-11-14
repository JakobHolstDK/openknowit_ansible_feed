#!/usr/bin/env bash
# Install the awx cli
#sudo dnf install --enablerepo=ansible-automation-platform-2.2-for-rhel-8-x86_64-rpms automation-controller-cli >/dev/null 2>&1

# This uses vault and sets nessesary creds. can be run from .bashrc

#export CONTROLLER_USERNAME=`vault kv get secret/ansible |jq .data.data.user -r`
#export CONTROLLER_HOST=`vault kv get secret/ansible |jq .data.data.url -r`
#export CONTROLLER_TOKEN=`vault kv get secret/ansible |jq .data.data.token -r`
#export CONTROLLER_PASSWORD=`vault kv get ansibleautomation/allvars |jq .data.admin_password -r`

export CONTROLLER_OAUTH_TOKEN=`awx login |jq .token -r`

awx 

#Now we are in

