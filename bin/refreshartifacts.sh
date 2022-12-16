#!/usr/bin/env bash

wget -o /tmp/vault.log -O /tmp/vault.html https://releases.hashicorp.com/vault|html2text 
VERSIONS=$(cat /tmp/vault.html |html2text |grep vault |awk '{ print $2 }' |awk -F'vault_' '{ print $2 }' )
for VERS in $VERSIONS:
do
    if [[ $1 == "init" ]]
    then
        touch  artifacts/vault.$VERS.zip
    fi
    if [[  ! -f artifacts/vault.$VERS.zip ]];
    then
        wget -O artifacts/vault.$VERS.zip https://releases.hashicorp.com/vault/${VERS}/vault_${VERS}_linux_amd64.zip
    fi
done


