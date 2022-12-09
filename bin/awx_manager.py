#!/usr/bin/env python

import redis
from pprint import pprint
import json
import requests
import hvac
import os
import sys


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
r.flushdb()
ansibletoken = vault.read_secret(engine_name="secret", secret="awx/ansible.openknowit.com")['data']['data']

def getawxdata(item):
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
        r.set(key, str(result), 600)
        key = "ansible.openknowit.com:" + item +":name:" + result['name']
        r.set(key, str(result['id']), 600 )
        key = "ansible.openknowit.com:" + item +":orphan:" + result['name']
        r.set(key, str(result), 600)

def vault_get_secret(path):
  secret = vault.read_secret(engine_name="secret", secret=path)['data']['data']
  return secret


def awx_get_id(item,name):
  key = "ansible.openknowit.com:" + item +":name:" + name
  myvalue =  r.get(key)
  mydevode = ""
  try: 
    mydecode = myvalue.decode()
  except:
    mydecode = ""
  return mydecode

  

def awx_delete(item, name):
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  itemid = (awx_get_id(item, name))
  url ="https://ansible.openknowit.com/api/v2/" + item + "/" + itemid
  resp = requests.delete(url,headers=headers)

def awx_purge_orphans():
  orphans = r.keys("*:orphan:*")
  for orphan in orphans:
    mykey = orphan.decode().split(":")
    awx_delete(mykey[1],mykey[3])

def awx_create_label(name, organization):
  orgid = (awx_get_id("organizations", organization))
  if ( orgid != "" ):
    data = {
       "name": name,
       "organization": orgid
       }
    mytoken = ansibletoken['token']
    headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
    url ="https://ansible.openknowit.com/api/v2/labels/"
    resp = requests.post(url,headers=headers, json=data)
      


def awx_create_inventory(name, description, organization, inventorytype, variables):
  print("Creating inventory")
  try:  
    invid = (awx_get_id("inventories", name))
  except:
    print("Unexcpetede error")
  if (invid == ""):
    orgid = (awx_get_id("organizations", organization))
    data = {
          "name": name,
          "description": description,
          "inventorytype": inventorytype,
          "organization": orgid
         }
    mytoken = ansibletoken['token']
    headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
    url ="https://ansible.openknowit.com/api/v2/inventories/"
    resp = requests.post(url,headers=headers, json=data)
    loop = True
    while ( loop ):
        getawxdata("inventories")
        try:
            invid = (awx_get_id("inventories", name))
        except:
            print("Unexpected error")
        if (invid != "" ):
          loop = False
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  url ="https://ansible.openknowit.com/api/v2/inventories/%s/variable_data/" % invid
  resp = requests.put(url,headers=headers, json=variables)
  print(resp.content)





def awx_create_host(name, description, inventory, organization):
  print("Create host")
  try:  
    invid = (awx_get_id("inventories", inventory))
  except:
    print("Unexcpetede error")
  orgid = (awx_get_id("inventories", organization))
  data = {
        "name": name,
        "description": description,
        "organization": orgid,
        "inventory": invid
       }
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  url ="https://ansible.openknowit.com/api/v2/hosts/"
  resp = requests.post(url,headers=headers, json=data)






def awx_create_organization(name, description, max_hosts, DEE):
  print("Creating org")
  try:  
    orgid = (awx_get_id("organizations", name))
  except:
    print("Unexcpetede error")
  if (orgid == ""):
    mytoken = ansibletoken['token']
    headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
    data = {
          "name": name,
          "description": description,
          "max_hosts": max_hosts
         }
    url ="https://ansible.openknowit.com/api/v2/organizations/"
    resp = requests.post(url,headers=headers, json=data)
  else:    
    mytoken = ansibletoken['token']
    headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
    data = {
          "name": name,
          "description": description,
          "max_hosts": max_hosts
         }
    url ="https://ansible.openknowit.com/api/v2/organizations/%s" % orgid
    resp = requests.put(url,headers=headers, json=data)
  getawxdata("organizations")


def awx_create_schedule(name, unified_job_template,  description, tz, start, run_frequency, run_every, end, scheduletype):
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  # The scheduling is tricky and must be refined
  if ( scheduletype == "Normal"):
     data = {
      "name": name,
      "unified_job_template": unified_job_template,
      "description": description,
      "local_time_zone": tz,
      "dtstart": start['year'] + "-" + start['month'] + "-" + start['day'] + "T" + start['hour'] + ":" + start['minute'] + ":" + start['second']  + "Z",
      "rrule": "DTSTART;TZID=" + tz + ":" + start['year'] + start['month'] + start['day'] + "T" + start['hour'] + start['minute'] + start['second'] +" RRULE:INTERVAL=" + run_frequency + ";FREQ=" + run_every
    }
  url ="https://ansible.openknowit.com/api/v2/schedules/"
  resp = requests.post(url,headers=headers, json=data)


def awx_create_template(name, description, job_type, inventory,project,ee, credential, playbook, organization):
  orgid = (awx_get_id("organizations", organization))
  invid = (awx_get_id("inventories", inventory))
  projid = (awx_get_id("projects", project))
  credid = (awx_get_id("credentials", credential))
  eeid = (awx_get_id("execution_environments", ee))

  data = {
    "name": name,
    "description": description,
    "job_type": "run",
    "inventory": invid,
    "project": projid,
    "playbook": playbook,
    "scm_branch": "",
    "credential": credid,
    "forks": 0,
    "limit": "",
    "verbosity": 0,
    "extra_vars": "",
    "job_tags": "",
    "force_handlers": "false",
    "skip_tags": "",
    "start_at_task": "",
    "timeout": 0,
    "use_fact_cache": "false",
    "execution_environment": eeid,
    "host_config_key": "",
    "ask_scm_branch_on_launch": "false",
    "ask_diff_mode_on_launch": "false",
    "ask_variables_on_launch": "false",
    "ask_limit_on_launch": "false",
    "ask_tags_on_launch": "false",
    "ask_skip_tags_on_launch": "false",
    "ask_job_type_on_launch": "false",
    "ask_verbosity_on_launch": "false",
    "ask_inventory_on_launch": "false",
    "ask_credential_on_launch": "false",
    "survey_enabled": "false",
    "become_enabled": "false",
    "diff_mode": "false",
    "allow_simultaneous": "false",
    "job_slice_count": 1
}
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  url = "https://ansible.openknowit.com/api/v2/job_templates/"
  resp = requests.post(url,headers=headers, json=data)
  getawxdata("job_templates")
  jobid = awx_get_id("job_templates", name)

  associatecommand = "awx job_template associate %s --credential %s" % ( jobid, credid)
  print(associatecommand)
  #
  # This shouldnt be a command but i cant find the rest api call
  os.system(associatecommand)
  #


def awx_create_team():
  print("create team")

def awx_create_user():
  print("create team")

def awx_create_credential( name, description, credential_type, credentialuser, kind, organization ):
  try:
    credid = (awx_get_id("credentials", name))
  except:
    print("Unexcpetede error")

  orgid = (awx_get_id("organizations", organization))
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
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
    becomepass = vault_get_secret(credentialuser)['becomepassword']
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
            "become_username": becomeuser,
            "become_password": becomepass
          },
        "kind": kind
        }

  if ( credid == ""):
    url = "https://ansible.openknowit.com/api/v2/credentials/"
    resp = requests.post(url,headers=headers, json=data)
  else:
    url = "https://ansible.openknowit.com/api/v2/credentials/%s/" % credid
    resp = requests.put(url,headers=headers, json=data)
  getawxdata("credentials")


def awx_get_organization(orgid):
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  url ="https://ansible.openknowit.com/api/v2/organizations/%s" % orgid
  resp = requests.get(url,headers=headers)
  return   json.loads(resp.content)

def awx_get_project(projid, organization):
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  orgid = (awx_get_id("organizations", organization))
  url ="https://ansible.openknowit.com/api/v2/projects/%s" % projid
  resp = requests.get(url,headers=headers)
  return   json.loads(resp.content)
  
def awx_create_project(name, description, scm_type, scm_url, scm_branch, credential, organization):
  getawxdata("projects")
  try:  
    projid = (awx_get_id("projects", name))
  except:
    print("Unexpected error")
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  orgid = (awx_get_id("organizations", organization))
  credid = (awx_get_id("credentials", credential))
  data = {
        "name": name,
        "description": description,
        "scm_type": scm_type,
        "scm_url": scm_url,
        "organization": orgid,
        "scm_branch": scm_branch,
        "credential": credid
       }

  if (projid == ""):
    print("Creating a new project")
    url ="https://ansible.openknowit.com/api/v2/projects/"
    resp = requests.post(url,headers=headers, json=data)
    #loop until project is synced
    loop = True
    while ( loop ):
        getawxdata("projects")
        try:  
            projid = (awx_get_id("projects", name))
        except:
            print("Unexpected error")
        projectinfo = awx_get_project(projid, organization)
        try:
          if( projectinfo['status'] == "successful"):
              loop = False
        except:
          print("Project status unknown")

  else:
    print("Updating project %s " % name)
    url ="https://ansible.openknowit.com/api/v2/projects/%s/" % projid
    resp = requests.put(url,headers=headers, json=data)
    getawxdata("projects")
    try:
        projid = (awx_get_id("projects", name))
    except:
        print("Unexpected error")
    projectinfo = awx_get_project(projid, organization)
    if( projectinfo['status'] == "successful"):
        print ("project %s  is ok"  % name )
    else:    
        print ("project %s  is ok" % name )
  refresh_awx_data()


def refresh_awx_data():
  print("refresh data from awx")
  items = {"organizations", "projects", "credentials", "hosts", "inventories", "credential_types", "labels" , "instance_groups", "job_templates"}    
  for item in items:
    print("Refreshing %s" % item)
    getawxdata(item)


# Main:  start
########################################################################################################################

cfgfile = "etc/master.json"

if (len(sys.argv) == 1):
    print("Runnig standalone")
else:
    print("running custom config")
    if (sys.argv[1] == "master" ):
        cfgfile = "/opt/openknowit_ansibleautomation_feed/etc/master.json"
    if (sys.argv[1] == "custom" ):
        cfgfile = "/opt/openknowit_ansibleautomation_main/etc/custom.json"

print("Open config file %s " % cfgfile)

f = open(cfgfile)
config = json.loads(f.read())
f.close

refresh_awx_data()
print("Iterate over organizations")

for org in (config['organization']):
  orgname = org['name']
  key = "ansible.openknowit.com:organizations:orphan:" + orgname
  r.delete(key)
  max_hosts = org['max_hosts']
  default_environment = org['default_environment']
  description = org['description']
  awx_create_organization(orgname, description, max_hosts, default_environment)
  getawxdata("organizations")
  orgid = awx_get_id("organizations", orgname)
  loop = True
  while ( loop ):
    orgdata = awx_get_organization(orgid)
    if ( orgdata['name'] == orgname ):
      loop = False
  print("Organization is stable")
  refresh_awx_data()

  print("load data from configfile")

  projects = org['projects']
  credentials = org['credentials']
  inventories = org['inventories']
  hosts = org['hosts']
  users = org['users']
  labels = org['labels']
  templates = org['templates']
  schedules = org['schedules']




  for credential in credentials:
    credentialname = credential['name']
    credentialdesc = credential['description']
    credentialtype = credential['credential_type']
    credentialuser = credential['user_vault_path']
    credentialkind = credential['kind']
    key = "ansible.openknowit.com:credentials:orphan:" + credentialname
    r.delete(key)
    awx_create_credential( credentialname, credentialdesc, credentialtype, credentialuser, credentialkind, orgname)
    loop = True
    while (loop):
        print("Check if %s is created" % credentialname )
        credid = awx_get_id("credentials", credentialname)
        if ( credid != "" ):
          loop = False
          print("We have an ID called %s" % credid)




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
    awx_get_id("projects", projectname)
    projid = (awx_get_id("projects", projectname))

  for label in labels:
    labelname = label['name']
    awx_create_label(labelname, orgname)

  for inventory in inventories:
    inventoryname = inventory['name']
    inventorydesc = inventory['description']
    inventorytype = inventory['type']
    inventoryvariables = inventory['variables']
    awx_create_inventory(inventoryname, inventorydesc, orgname, inventorytype, inventoryvariables)

  for host in hosts:
    hostname = host['name']
    hostdesc = host['description']
    hostinventories = host['inventory']
    for hostinventory in hostinventories: 
      awx_create_host(hostname, hostdesc, hostinventory, orgname)


  for template in templates:
    templatename = template['name']
    templatedescription = template['description']
    templatejob_type = template['job_type']
    templateinventory =  template['inventory']
    templateproject = template['project']
    templateEE = template['EE']
    templatecredential = template['credentials']  
    templateplaybook = template['playbook']
    awx_create_template(templatename, templatedescription, templatejob_type, templateinventory, templateproject, templateEE, templatecredential, templateplaybook, orgname)


  for schedule in schedules:
    schedulename = schedule['name']

    if ( schedule['type'] == "job"):
      templatename = schedule['template']
      unified_job_template_id = awx_get_id("job_templates", templatename)

    if ( schedule['type'] == "project"):
      projectname = schedule['project']
      unified_job_template_id = awx_get_id("projects", projectname)

    tz = schedule['local_time_zone']

    if ( schedule ['start'] == "now" ):
      dtstart = { 
        "year": "2012",
        "month": "12",
        "day": "01",
        "hour": "12",
        "minute": "00",
        "second": "00"
        }

    if ( int(schedule['run_every_minute']) ):
      scheduletype="Normal"
      run_frequency =  schedule['run_every_minute']
      run_every = "MINUTELY"
  
    if ( schedule ['end'] == "never" ):
      dtend = "null"
    awx_create_schedule(schedulename, unified_job_template_id, description,tz, dtstart, run_frequency, run_every, dtend, scheduletype)

      
