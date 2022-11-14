#!/usr/bin/env bash
ssh knowit@zabbix.openknowit.com /home/knowit/venv/vlenv/bin/vl ansible_inventory > /tmp/inventory.ini.$$ 2>&1
SERVERS=`ansible-inventory -i  /tmp/inventory.ini --list 2>/dev/null | jq "._meta"|jq ".hostvars| keys[]" -r | tr '\n' ';'| sed "s/;$//"`

rm /tmp/inventory.ini.$$ >/dev/null 2>&1
echo $SERVERS
