import redis
from pprint import pprint
import json
import requests
import hvac
import os
import sys
import datetime

#secrets = "environment"
secrets = "vault"



def prettyllog(function, action, item, organization, statuscode, text):
  d_date = datetime.datetime.now()
  reg_format_date = d_date.strftime("%Y-%m-%d %I:%M:%S %p")
  print("%-20s: %-12s %-20s %-50s %-20s %-4s %-50s " %( reg_format_date, function,action,item,organization,statuscode, text))

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


prettyllog("------------", "--------------------", "------------------------------------------", "--------------------", "----", "--------------------------------------------------------------------------------------")

vault = Hvac()
if (vault.client.is_authenticated()):
    prettyllog("init", "authenticate", "vault", "main", "000", "OK")
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
    response = json.loads(resp.content)
    prettyllog("manage", "inventories", name, organization, resp.status_code, response)
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
  response = json.loads(resp.content)
  prettyllog("manage", "inventories", name, organization, resp.status_code, response)


def awx_create_host(name, description, inventory, organization):
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
  response = json.loads(resp.content)
  try:
    hostid=response['id']
    prettyllog("manage", "host", name, organization, resp.status_code, "Host %s created with id: %s" % (name, hostid ))
  except:
    prettyllog("manage", "host", name, organization, resp.status_code, response)







def awx_create_organization(name, description, max_hosts, DEE, realm):
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
    response = json.loads(resp.content)
    try:
      orgid=response['id']
      prettyllog("manage", "organization", name, realm, resp.status_code, "organization %s created with id %s" % (orgid))
    except:
      prettyllog("manage", "organization", name, realm, resp.status_code, response)
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
    response = json.loads(resp.content)
    prettyllog("manage", "organization", name, realm, resp.status_code, response)
  getawxdata("organizations")


def awx_create_schedule(name, unified_job_template,  description, tz, start, run_frequency, run_every, end, scheduletype, organization):
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
  response = json.loads(resp.content)
  try:
    schedid=response['id']
    prettyllog("manage", "schedule", name, organization, resp.status_code, schedid)
  except:
    prettyllog("manage", "schedule", name, organization, resp.status_code, response)

#
# Create job template
#
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
  response = json.loads(resp.content)
  getawxdata("job_templates")
  tmplid = awx_get_id("job_templates", name )
  if ( tmplid != "" ):
    url = "https://ansible.openknowit.com/api/v2/job_templates/%s/" % tmplid
    resp = requests.put(url,headers=headers, json=data)
    response = json.loads(resp.content)
    try:
      tmplid=response['id']
      prettyllog("update", "template", name, organization, resp.status_code, tmplid)
    except:
      prettyllog("update", "template", name, organization, resp.status_code, response)
  getawxdata("job_templates")
  tmplid = awx_get_id("job_templates", name )
  getawxdata("credentials")
  credid = (awx_get_id("credentials", credential))
  associatecommand = "awx job_template associate %s --credential %s >/dev/null 2>/dev/null " % ( tmplid, credid)
  os.system(associatecommand)
  ############################################################################### end of create job template ##########################################


######################################
# function:  Create Team
######################################
def awx_create_team(name, description, organization):
  prettyllog("manage", "team", name, organization, "000", "-")

######################################
# function: create user
######################################
def awx_create_user(name, description, organization):
  prettyllog("manage", "user", name, organization, "000", "-")

######################################
# function: create Credential
######################################
def awx_create_credential( name, description, credential_type, credentialuser, kind, organization ):
  try:
    credid = (awx_get_id("credentials", name))
  except:
    print("Unexcpetede error")
  orgid = (awx_get_id("organizations", organization))
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  credentialtypeid = (awx_get_id("credential_types", credential_type))

  if ( secrets == "environment") and ( kind == "scm"):
    sshkey = os.getenv("GITKEY").strip('"') 
    myuser = os.getenv("GITUSER")
    mypass = os.getenv("GITPASS")

  if ( secrets == "environment") and ( kind == "ssh"):
    sshkey = os.getenv("SSHKEY").strip('"') 
    myuser = os.getenv("SSHUSER")
    mypass = os.getenv("SSHPASS")

  if ( secrets == "vault" ):
    sshkey = vault_get_secret(credentialuser)['key']
    myuser = vault_get_secret(credentialuser)['username']
    mypass = vault_get_secret(credentialuser)['password']

  if( kind == "hashivault_kv"):
    myurl = os.getenv(key="VAULT_URL")
    mytoken = os.getenv(key="VAULT_TOKEN")
    data = {
      "name": name,
      "description": description,
      "credential_type": credentialtypeid,
      "organization": orgid,
      "inputs":
        {
           "url": myurl,
           "token": mytoken
        },
      "kind": kind
    }
    



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
    response = json.loads(resp.content)
    try:
      credid=response['id']
      prettyllog("manage", "credential", name, organization, resp.status_code, credid)
    except:
      prettyllog("manage", "credential", name, organization, resp.status_code, response)
  else:
    url = "https://ansible.openknowit.com/api/v2/credentials/%s/" % credid
    resp = requests.put(url,headers=headers, json=data)
    response = json.loads(resp.content)
    try:
      credid=response['id']
      prettyllog("manage", "credential", name, organization, resp.status_code, credid)
    except:
      prettyllog("manage", "credential", name, organization, resp.status_code, response)
  getawxdata("credentials")


######################################
# function: get  organization
######################################
def awx_get_organization(orgid):
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  url ="https://ansible.openknowit.com/api/v2/organizations/%s" % orgid
  resp = requests.get(url,headers=headers)
  return   json.loads(resp.content)

######################################
# function: get Project 
######################################
def awx_get_project(projid, organization):
  mytoken = ansibletoken['token']
  headers = {"User-agent": "python-awx-client", "Content-Type": "application/json","Authorization": "Bearer {}".format(mytoken)}
  orgid = (awx_get_id("organizations", organization))
  url ="https://ansible.openknowit.com/api/v2/projects/%s" % projid
  resp = requests.get(url,headers=headers)
  return   json.loads(resp.content)
  
######################################
# function: Create Project 
######################################
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
    url ="https://ansible.openknowit.com/api/v2/projects/"
    resp = requests.post(url,headers=headers, json=data)
    response = json.loads(resp.content)
    try:
      projid=response['id']
      prettyllog("manage", "project", name, organization, resp.status_code, projid)
    except:
      prettyllog("manage", "project", name, organization, resp.status_code, response)
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
    url ="https://ansible.openknowit.com/api/v2/projects/%s/" % projid
    resp = requests.put(url,headers=headers, json=data)
    response = json.loads(resp.content)
    try:  
      projid = (awx_get_id("projects", name))
      prettyllog("manage", "project", name, organization, resp.status_code, projid)
    except:
      prettyllog("manage", "project", name, organization, resp.status_code, response)
    getawxdata("projects")
    try:
        projid = (awx_get_id("projects", name))
    except:
        print("Unexpected error")
    projectinfo = awx_get_project(projid, organization)
    if( projectinfo['status'] == "successful"):
      prettyllog("manage", "project", name, organization, "000", "Project is ready")
    else:    
      prettyllog("manage", "project", name, organization, "666", "Project is not ready")
  refresh_awx_data()

######################################
# function: Refresh AWX data
######################################
def refresh_awx_data():
  items = {"organizations", "projects", "credentials", "hosts", "inventories", "credential_types", "labels" , "instance_groups", "job_templates"}    
  for item in items:
    getawxdata(item)


########################################################################################################################
# Main:  start
########################################################################################################################
cfgfile = "etc/aaoaa.json"
realm = "standalone"
if (len(sys.argv) == 1):
  prettyllog("init", "runtime", "config", "master", "001", "Running standalone : using local master config")
  realm = "standalone"
else:
    if (sys.argv[1] == "master" ):
        cfgfile = "/opt/openknowit_ansibleautomation_feed/etc/aaoaa.json"
        realm="master"
        prettyllog("init", "runtime", "config", "master", "002",  "Running Running as daemon")
    if (sys.argv[1] == "custom" ):
        prettyllog("init", "runtime", "config", sys.argv[2], "003" , "running cusom config file")
        cfgfile = "/opt/openknowit_ansibleautomation_main/etc/aaoaa.d/%s" % sys.argv[2]

f = open(cfgfile)
config = json.loads(f.read())
f.close
refresh_awx_data()

########################################################################################################################
# organizations
########################################################################################################################
for org in (config['organization']):
  orgname = org['name']
  key = "ansible.openknowit.com:organizations:orphan:" + orgname
  r.delete(key)
  max_hosts = org['meta']['max_hosts']
  default_environment = org['meta']['default_environment']
  description = org['meta']['description']
  awx_create_organization(orgname, description, max_hosts, default_environment, realm)
  getawxdata("organizations")
  orgid = awx_get_id("organizations", orgname)
  loop = True
  while ( loop ):
    orgdata = awx_get_organization(orgid)
    if ( orgdata['name'] == orgname ):
      loop = False
  refresh_awx_data()


  ######################################
  # Credentials
  ######################################
  try:
    credentials = org['credentials']
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
        credid = awx_get_id("credentials", credentialname)
        if ( credid != "" ):
          loop = False
  except:
    prettyllog("config", "initialize", "credentials", orgname, "000",  "No credentioals found")

  ######################################
  # Projects
  ######################################
  try:
    projects = org['projects']
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
  except:
    prettyllog("config", "initialize", "projects", orgname, "000",  "No projects found")

  ######################################
  # inventories
  ######################################
  try:
    inventories = org['inventories']
    for inventory in inventories:
      inventoryname = inventory['name']
      inventorydesc = inventory['description']
      inventorytype = inventory['type']
      inventoryvariables = inventory['variables']
      awx_create_inventory(inventoryname, inventorydesc, orgname, inventorytype, inventoryvariables)
  except:
    prettyllog("config", "initialize", "inventories", orgname, "000",  "No inventories found")

  ######################################
  # hosts
  ######################################
  try:
    hosts = org['hosts']
    for host in hosts:
      hostname = host['name']
      hostdesc = host['description']
      hostinventories = host['inventories']
      for hostinventory in hostinventories: 
        awx_create_host(hostname, hostdesc, hostinventory, orgname)
  except:
    prettyllog("config", "initialize", "hosts", orgname, "000",  "No hosts found")

  ######################################
  # users
  ######################################
  try:
    users = org['users']
  except:
    prettyllog("config", "initialize", "users", orgname, "000",  "No users found")

  ######################################
  # label
  ######################################
  try:
    labels = org['labels']
    for label in labels:
      labelname = label['name']
      awx_create_label(labelname, orgname)
  except:
    prettyllog("config", "initialize", "labels", orgname, "000",  "No labels found")

  ######################################
  # Templates
  ######################################
  try:
    templates = org['templates']
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
  except:
    prettyllog("config", "initialize", "templates", orgname, "000",  "No templates found")

  ######################################
  # Schedules
  ######################################
  try:
    schedules = org['schedules']
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
      awx_create_schedule(schedulename, unified_job_template_id, description,tz, dtstart, run_frequency, run_every, dtend, scheduletype, orgname)
  except:
    prettyllog("config", "initialize", "schedules", orgname, "000",  "No schedules found")
### The end
