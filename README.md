# Ansible AUTOMATION

## Hvad er Ansible automation v2:

* Et framework med en kæmpe potentiale. 
* Centraliset styring af playbooks
* dynamiske inventories
* Seperations of dyties
* et kæmpe bibliotek af pre backed playbooks

## HVad er det også 
* en tom skal
* kompliceret at bibeholde struktur
* organiske blob af data
* placeholder for future legacy
* 

Når vi sælger en automation platform til en kunde, sælger vi en tom skal, et interface til et imponerende framwork med uanede muligheder

Der er som reget 2 udfald når en kunde hopper på ansible automation.
1: Kunden køber det og kommer aldrig igang
2: Kunden burger det og der opstår en mere eller mindre strømlignet struktur. 
    2.1 Der er kaos og alt sejler. der er ikke styr på noget og systemet bliver mere og mere uoverskueligt
    2.2 Der er en "person" der bruger alt sin tid på at være gurdian of the galaxy. Her vil vi ikke kunne bidrage med det store. (endnu)
    
I de to andre scenarier skal og kan vi hjælpe.

## HVad vil Vi levere
I openstack er der et concept der hedder trippleO  : Openstanck on Openstack
jeg vil gerne ansible automation on ansible automantion


### installation and updating ansible automation
Installation af ansible automation er skåret ind til benet.

Hent et arkiv, 
lav nogle redhar servere
lav en config/invientory fil
kør setup.sh

vent.... pling

Ansible automation is here
Den er rimelig robust og kan efter sigende opgradere flyvende.

Versionsstyring er lidt shaky. man skal holde øje med om der er kommet en ny og deres krav til target os er lidt spooky.

Men det ser ud til at være skruet sammen således at der kommer en platform ud og at man kan "heale" setuppet ved at genkøre install.
Der er også tiltænkt hvis man skal have flere eller færre execution noder så tillføjes de til inventory og bum.... så er der opgraderet


### Opretholde basal struktur med ansible automation running anstible automation configuaration.

En ansible automation service beskrives af en json file
alle "hemmeligheder" gemmes i hashicorp vault

'''
{
  "organization": [
    {
      "name": "Openknowit",
      "description": "Demo of ansible automation",
      "max_hosts": 100,
      "default_environment": "Ansible Engine 2.9 execution environment",
      "projects": [
        {
          "name": "main",
          "description": "Main project ensure automation engine consistent",
          "scm_type": "git",
          "scm_url": "git@github.com:JakobHolstDK/openknowit_ansibleautomation_main.git",
          "scm_branch": "main",
          "credential": "github",
          "master": "True"
        }
      ],
      "credentials": [
        {
          "name": "github",
          "description": "Github service account for testing",
          "credential_type": "Source Control",
          "user_vault_path": "project/openknowit/demogituser",
          "kind": "scm"
        },
        { 
          "name": "main",
          "description": "maib service account for testing",
          "credential_type": "Machine",
          "user_vault_path": "project/openknowit/remotesshuser",
          "kind": "ssh"
        }
      ],
      "inventories": [
        {
          "name": "masterinventory",
          "description": "Inventorycontaining all servers under automation control",
          "hosts": "openknowit.org",
          "type": "static"
        }
      ],
      "hosts": [
        {
          "name": "ansible.openknowit.com",
          "description": "Server cabable for running selfmaintainance",
          "inventory": "masterinventory"
        }
      ],
      "templates": [
        {
          "name": "ansibleautomationmanager_checkup",
          "description": "Master job for self healing ansible automation as code",
          "job_type": "run",
          "inventory": "masterinventory",
          "project": "main",
          "EE": "Automation Hub Default execution environment",
          "credentials": "main",
          "playbook": "checkup.yml"
        },
        {
          "name": "ansibleautomationmanager_update",
          "description": "Maintain ansible manager and prereqs",
          "job_type": "run",
          "inventory": "masterinventory",
          "project": "main",
          "EE": "Automation Hub Default execution environment",
          "credentials": "main",
          "playbook": "ansiblemanager.yml"
        }
      ],
      "schedules": [
        {
          "name": "ansibleautomationmanager_checkup",
          "type": "job",
          "template": "ansibleautomationmanager_checkup",
          "description": "Master job for ensuring connectivity",
          "local_time_zone": "CET",
          "run_every_minute": "1",
          "start": "now",
          "end": "never"
        },
        {
          "name": "ansibleautomationmanager_update",
          "type": "job",
          "template": "ansibleautomationmanager_update",
          "description": "Master job updating automation manager",
          "local_time_zone": "CET",
          "run_every_minute": "5",
          "start": "now",
          "end": "never"
        },
        {
          "name": "Mainprojectschedule",
          "type": "project",
          "project": "main",
          "description": "Master job for syncing project main",
          "local_time_zone": "CET",
          "run_every_minute": "10",
          "start": "now",
          "end": "never"
        }
      ],
      "users": 
        {
          "user_vault_path": "project/openknowit/users",
          "description": "AD integration is mandatory"
        },
      "labels":
      [
        { 
          "name": "static"
        },
        {
          "name": "production"
        },
        {
           "name": "test"
        }
      ]
    }
  ]
}

'''





