#!/usr/bin/env python

import redis
from pprint import pprint
import json
import requests
import hvac
import os

class Hvac:
  def __init__(self):
    self.url = self._get_url()
    self.token = self._get_token()
    self.client = hvac.Client(url=self.url, token=self.token)


  @staticmethod
  def _get_url():
    return os.getenv(key="VAULT_URL")


  @staticmethod
  def _get_token():
    return os.getenv(key="VAULT_TOKEN")

  # Method to create a new KV pair
  def create_kv_engine(self, engine_name):
    self.client.sys.enable_secrets_engine(
      backend_type="kv",
      path=engine_name,
      options={"version": "2"}
    )

  # Method to create a password 
  def create_password(self, engine_name, username, password):
    self.client.secrets.kv.v2.create_or_update_secret(
      mount_point=engine_name,
      path=username,
      secret={"username": username, "password": password}
    )

  # Method to read an existing password 
  def read_password(self, engine_name, username):
    return self.client.secrets.kv.v2.read_secret_version(
      mount_point=engine_name,
      path=username
    )
  # Method to read an existing token
  def read_secret(self, engine_name, secret):
    return self.client.secrets.kv.v2.read_secret_version(
      mount_point=engine_name,
      path=secret
    )


vault = Hvac()
if (vault.client.is_authenticated()):
    print("We are in the vault")
else:
    exit

r = redis.Redis()

def getawxdata(item):
  print("AWX: %s" % item)
  ansibletoken = vault.read_secret(engine_name="secret", secret="awx/ansible.openknowit.com")['data']['data']
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  url ="https://ansible.openknowit.com/api/v2/" + item
  intheloop = "first"
  while ( intheloop == "first" or intheloop != "out" ):
    try:
      resp = requests.get(url,headers=headers)
    except:
      intheloop = "out"
    try:
      mydata = json.loads(resp.content)
    except:
      intheloop = "out"
    try:
      url = "https://ansible.openknowit.com/" + (mydata['next'])
    except: 
      intheloop = "out"
    savedata = True
    try:
      myresults = mydata['results'] 
    except:
      savedata = False
    if ( savedata == True ):
      for result in mydata['results']:
        key = "ansible.openknowit.com:" + item +":id:" + str(result['id'])
        print(key)
        r.set(key, str(result))
        key = "ansible.openknowit.com:" + item +":name:" + result['name']
        r.set(key, str(result['id']))
        key = "ansible.openknowit.com:" + item +":orphan:" + result['name']
        r.set(key, str(result))

def vault_get_secret(path):
  secret = vault.read_secret(engine_name="secret", secret=path)['data']['data']
  return secret


def awx_get_id(item,name):
  key = "ansible.openknowit.com:" + item +":name:" + name
  print("-----------------------------------------------------")
  print(key)
  print("-----------------------------------------------------")
  myvalue =  r.get(key)
  mydecode = False
  try: 
    mydecode = myvalue.decode()
  except:
    return "-"
  return mydecode

  

def awx_delete(item, name):
  ansibletoken = vault.read_secret(engine_name="secret", secret="awx/ansible.openknowit.com")['data']['data']
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  itemid = (awx_get_id(item, name))
  url ="https://ansible.openknowit.com/api/v2/" + item + "/" + itemid
  resp = requests.delete(url,headers=headers)
  print(resp.status_code)

def awx_purge_orphans():
  orphans = r.keys("*:orphan:*")
  for orphan in orphans:
    mykey = orphan.decode().split(":")
    awx_delete(mykey[1],mykey[3])


def awx_get_project(name):
    return 0

def awx_create_organization(name, description, max_hosts, DEE):
  print("Credentials:")
  try:  
    orgid = (awx_get_id("organizations", name))
    print("Organization has an id : %s" % orgid)
  except:
    print("Unexcpetede error")
  if(orgid == '-'):

    ansibletoken = vault.read_secret(engine_name="secret", secret="awx/ansible.openknowit.com")['data']['data']
    mytoken = ansibletoken['token']
    headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
    data = {
          "name": name,
          "description": description,
          "max_hosts": max_hosts
         }
    url ="https://ansible.openknowit.com/api/v2/organizations/"
    resp = requests.post(url,headers=headers, json=data)
    print(resp.content)
    print("Org %s created" % name )
    getawxdata("organizations")


def awx_create_credential( name, description, credential_type, credentialuser, kind, organization):
  try:
    credid = (awx_get_id("credentials", name))
  except:
    print("Unexcpetede error")

  ansibletoken = vault.read_secret(engine_name="secret", secret="awx/ansible.openknowit.com")['data']['data']
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  orgid = (awx_get_id("organizations", organization))
  print("The organizatiois %s %s" % (orgid, organization))
  credentialtypeid = (awx_get_id("credential_types", credential_type))
  sshkey = vault_get_secret(credentialuser)['key']
  myuser = vault_get_secret(credentialuser)['username']
  mypass = vault_get_secret(credentialuser)['password']

  if( kind == "scm"):
    data = {
        "name": name,
        "description": description,
        "credential_type": credentialtypeid,
        "organization": orgid,
        "inputs":
          {
            "ssh_key_data": sshkey,
            "username": myuser,
            "password": mypass
          },
        "kind": kind
        }
  if( kind == "ssh" ):
    becomemethod = vault_get_secret(credentialuser)['becomemethod']
    becomeuser = vault_get_secret(credentialuser)['becomeusername']
    data = {
        "name": name,
        "description": description,
        "credential_type": credentialtypeid,
        "organization": orgid,
        "inputs":
          {
            "ssh_key_data": sshkey,
            "username": myuser,
            "password": mypass,
            "become_method": becomemethod,
            "become_username": becomeuser
          },
        "kind": kind
        }

  if ( credid == '-'):
    url = "https://ansible.openknowit.com/api/v2/credentials/"
    resp = requests.post(url,headers=headers, json=data)
  else:
    url = "https://ansible.openknowit.com/api/v2/credentials/%s/" % credid
    resp = requests.put(url,headers=headers, json=data)
  getawxdata("credentials")



def awx_create_project(name, description, scm_type, scm_url, scm_branch, credential, organization):
  try:  
    projid = (awx_get_id("projects", name))
  
  except:
    print("Unexpected error")

  ansibletoken = vault.read_secret(engine_name="secret", secret="awx/ansible.openknowit.com")['data']['data']
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  orgid = (awx_get_id("organizations", organization))
  credid = (awx_get_id("credentials", credential))
  data = {
        "name": organization + name,
        "description": description,
        "scm_type": scm_type,
        "scm_url": scm_url,
        "organization": orgid,
        "scm_branch": scm_branch,
        "credential": credid
       }
  url ="https://ansible.openknowit.com/api/v2/projects/"
  resp = requests.post(url,headers=headers, json=data)
  print(resp.content)
  getawxdata("projects")


items = {"organisations", "projects", "credentials", "hosts", "inventories", "credential_types"}    
#items = {"organizations", "projects"}    
for item in items:
  getawxdata(item)

f = open('demo.json')
config = json.loads(f.read())
f.close


for org in (config['organization']):
  orgname = org['name']
  key = "ansible.openknowit.com:organizations:orphan:" + orgname
  r.delete(key)
  max_hosts = org['max_hosts']
  default_environment = org['default_environment']
  description = org['description']
  awx_create_organization(orgname, description, max_hosts, default_environment)
  getawxdata("orgnizations")

  projects = org['projects']
  credentials = org['credentials']
  inventories = org['inventories']
  users = org['users']
  teams = org['teams']

  for credential in credentials:
    credentialname = credential['name']
    credentialdesc = credential['description']
    credentialtype = credential['credential_type']
    credentialuser = credential['user_vault_path']
    credentialkind = credential['kind']
    key = "ansible.openknowit.com:credentials:orphan:" + credentialname
    r.delete(key)
    awx_create_credential( credentialname, credentialdesc, credentialtype, credentialuser, credentialkind, orgname)


  for project in projects:
    projectname = project['name']
    projectdesc = project['description']
    projecttype = project['scm_type']
    projecturl  = project['scm_url']
    projectbrnc = project['scm_branch']
    projectcred = project['credential']
    key = "ansible.openknowit.com:projects:orphan:" + projectname
    r.delete(key)
    awx_create_project(projectname, projectdesc, projecttype, projecturl, projectbrnc, projectcred, orgname)

    





        

    




#PREFIX="ansibleautomationmananger"
#REDIS="redis-cli"
#AWX='awx'
#
#echo "`date`: Create organizations"
#${REDIS} keys "*"  |grep ansibleautomationmananger:organizations:name | awk -F"ansibleautomationmananger:organizations:name:" '{ print $2 }'  > /tmp/$$.organizations.list 2>/dev/null
#
#for org in `cat demo.json | jq .organization[].name -r | tr ' ' '_'`
#do
#    JSON=`cat demo.json | jq ' .organization[]  | {"name": .name , "description": .description , "max_hosts": .max_hosts , "default_environment": .default_environment }' -c  |tr ' ' '_'  |grep $org`
#    echo "$JSON"
#    NAME=`echo $JSON | jq .name -r | tr '_' ' '`
#    DESC=`echo $JSON | jq .description -r | tr '_' ' '`
#    EENAME=`echo $JSON | jq .default_environment -r | tr ' ' '_'`
#    MH=`echo $JSON | jq .max_hosts -r`
#    EEID=`${REDIS} get "ansibleautomationmananger:execution_environments:name:${EENAME}" |tr -d '"'`
#    echo "`date`: $EEID  :    $EENAME"
#    ${AWX} organization create --name "${NAME}"  >/dev/null 2>&1
#    myid=`${AWX} organizations list --name "${NAME}"|jq ".results[].id"`
#    echo "`date`: The org $org has mow the id $myid"
#    ${AWX} organization modify $myid --name "${NAME}" --description "${DESC}" --default_environment $EEID --max_hosts $MH  >/dev/null 2>&1
#    sed -i "s/^$org$//" /tmp/$$.organizations.list
#done
#
#
#
#
#echo "`date`: Cleanup orphan organizations"
##################################################################################################################
## Save status to redis
################################################################################################################
#for orphanorg in `cat /tmp/$$.organizations.list | grep -i [a-z] |tr ' ' '_'`
#do
#    echo "`date`: $orphanorg"
#    KEY="${PREFIX}:organizations:name:${orphanorg}"
#    ORGID=`${REDIS} get $KEY 2>/dev/null`
#    if [[ $? == 0 ]];
#    then
#        ${AWX} organization delete $ORGID
#    fi
#    ${REDIS} del $KEY >/dev/null 2>&1
#done
##rm /tmp/$$.organizations.list
#
#
#


