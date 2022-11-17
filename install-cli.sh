#!/usr/bin/env bash


dnf config-manager --add-repo https://releases.ansible.com/ansible-tower/cli/ansible-tower-cli-el8.repo
dnf install ansible-tower-cli

#    pip3 install --user https://releases.ansible.com/ansible-tower/cli/ansible-tower-cli-latest.tar.gz


