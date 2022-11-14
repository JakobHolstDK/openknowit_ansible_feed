#!/usr/bin/env python
import os
import inspect
import subprocess
import json
import pprint



from pyzabbix.api import ZabbixAPI


def host_create_params(myname, mygroupid, mytemplateid):
    fqdn = myname + ".openknowit.com"
    hostparams = {
        "host": myname,
        "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 0,
                "ip": "",
                "dns": fqdn,
                "port": "10050"
            }
        ],
        "groups": [
            {
                "groupid": mygroupid
            }
        ],
        "templates": [
            {
                "templateid": mytemplateid
            }
        ],
        "inventory_mode": 0,
        "inventory": {
            "macaddress_a": "01234",
            "macaddress_b": "56768"
        }
    }
    return(hostparams)



zabbix_url = os.getenv("ZABBIX_URL")
zabbix_token = os.getenv("ZABBIX_TOKEN")
zabbix_user = os.getenv("ZABBIX_USER")
zabbix_password = os.getenv("ZABBIX_PASSWORD")

# Create ZabbixAPI class instance
zapi = ZabbixAPI(url='https://zabbix.openknowit.com', user='Admin', password='ixj90j2s')
templates = zapi.template.get()
templateid = -1
for template in templates:
    if (template['name'] == "Linux by Zabbix agent" ):
        templateid = template['templateid']

hostgroups = zapi.hostgroup.get()
groupid = -1
groupparam = { "name": "redhat" }
try:
  zapi.hostgroup.create(groupparam)
except: 
  print("Already exist")

for group in hostgroups:
  if (group['name'] == "redhat" ):
    groupid = group['groupid']





p = subprocess.Popen("./vlinventory.sh", stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
p_status = p.wait()
vlstatus = output.decode().split(";")
for host in vlstatus:
    hostparam = host_create_params(host, groupid, templateid)
    try:
        zapi.host.create(hostparam)
    except:
        print("Host already defined")

#
