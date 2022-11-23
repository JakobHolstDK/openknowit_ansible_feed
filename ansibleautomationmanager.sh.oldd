#!/usr/bin/env bash

PREFIX="ansibleautomationmananger"

###############################################################################################################
# Save status to redis
###############################################################################################################
for list in credential_types inventory hosts credential organizations users execution_environments projects
do
    echo "`date`: $list"
   
    awx ${list} list|jq ".results[]  | {"id": .id, "name": .name}" -c 2>/dev/null >/tmp/$$.$list
    for item in `cat /tmp/$$.$list |tr ' ' '#' `
    do
       # echo "`date`: $item"
        ID=`echo $item |jq .id`
        RAWNAME=`echo $item |jq .name | tr '#' '_' |tr -d '"' `
        NAME=`echo $item |jq .name | tr '#' ' ' |tr -d '"' `
        KEY="${PREFIX}:${list}:id:${ID}"
        redis-cli set $KEY "$NAME" ex 6000 >/dev/null 2>&1
        KEY="${PREFIX}:${list}:name:${RAWNAME}"
        redis-cli set  $KEY $ID ex 6000 >/dev/null 2>&1
    done
done

###############################################################################################################
#  Create organizations
#######################A########################################################################################
echo "`date`: Create organizations"
redis-cli keys "*"  |grep ansibleautomationmananger:organizations:name | awk -F"ansibleautomationmananger:organizations:name:" '{ print $2 }'  > /tmp/$$.organizations.list
for org in `cat demo.json | jq .organization[].name -r | tr ' ' '_'`
do   
    JSON=`cat demo.json | jq ' .organization[]  | {"name": .name , "description": .description , "max_hosts": .max_hosts , "default_environment": .default_environment }' -c  |tr ' ' '_'  |grep $org` 
    NAME=`echo $JSON | jq .name -r | tr '_' ' '` 
    DESC=`echo $JSON | jq .description -r | tr '_' ' '` 
    EENAME=`echo $JSON | jq .default_environment -r | tr ' ' '_'` 
    MH=`echo $JSON | jq .max_hosts -r`
    EEID=`redis-cli get "ansibleautomationmananger:execution_environments:name:${EENAME}" |tr -d '"'`
    echo "`date`: $EEID  :    $EENAME"
    awx organization create --name "${NAME}"  >/dev/null 2>&1 
    myid=`awx organizations list --name "${NAME}"|jq ".results[].id"`
    echo "`date`: The org $org has mow the id $myid"
    awx organization modify $myid --name "${NAME}" --description "${DESC}" --default_environment $EEID --max_hosts $MH  >/dev/null 2>&1 
    sed -i "s/^$org$//" /tmp/$$.organizations.list
done




echo "`date`: Cleanup orphan organizations"
###############################################################################################################
# Save status to redis
###############################################################################################################
for orphanorg in `cat /tmp/$$.organizations.list | grep -i [a-z] |tr ' ' '_'` 
do
    echo "`date`: $orphanorg"
    KEY="${PREFIX}:organizations:name:${orphanorg}"
    ORGID=`redis-cli get $KEY 2>/dev/null`
    if [[ $? == 0 ]];
    then
        awx organization delete $ORGID
    fi
    redis-cli del $KEY >/dev/null 2>&1
done
rm /tmp/$$.organizations.list



for orgid in `cat demo.json | jq ".organization| keys[]"`
do   
	redis-cli keys "*"  |grep ansibleautomationmananger:credentials:name | awk -F"ansibleautomationmananger:credentials:name:" '{ print $2 }'  > /tmp/$$.credentials.list
	org=`cat demo.json | jq ".organization[$orgid].name" -r`
	###############################################################################################################
	#  Create Credentials
	###############################################################################################################
	echo "`date`: Create credentials for organization $org"
	for credential  in `cat demo.json | jq .organization[$orgid].credentials[].name -r`
	do  
    	   echo "`date`: Credential : $credential"	
    	   JSON=`cat demo.json | jq .organization[$orgid].credentials[]| jq '. | {"name": .name , "description": .description , "credential_type": .credential_type , "ssh_key_file": .ssh_key_file , "kind": .kind }' -c  |  grep "\"${credential}\""`
    	   NAME=`echo $JSON | jq .name -r ` 
    	   DESC=`echo $JSON | jq .description -r | tr '_' ' '` 
    	   TYPE=`echo $JSON | jq .credential_type -r | tr '_' ' '` 
    	   KIND=`echo $JSON | jq .credential_kind -r | tr '_' ' '` 
    	   awx credential create --name "${NAME}" --description "${DESC}"  --credential_type "${TYPE}" --organization "${org}"
    	   myid=`awx credentials list --name "${NAME}"|jq ".results[].id"`
    	   echo "`date`: The credential $credential has mow the id $myid"
    	   INPUTS="{\"username\": \"\",\"ssh_key_data\": \"`cat ~/.ssh/id_rsa`\"}"
    	   awx credential modify $myid --inputs "${INPUTS}"   
    	   sed -i "s/^$NAME$//" /tmp/$$.credentials.list
	done
	
	###############################################################################################################
	#  Create Master inventory  for the Organisation
	###############################################################################################################
	echo "`date`: Inventories"
	for inventory  in `cat demo.json | jq .organization[$orgid].inventories[].name -r`
	do  
    	   JSON=`cat demo.json | jq .organization[$orgid].inventories[]| jq '. | {"name": .name , "description": .description , "hosts": .hosts }' -c  |  grep "\"${inventory}\""`
    	   NAME=`echo $JSON | jq .name -r ` 
    	   DESC=`echo $JSON | jq .description -r | tr '_' ' '` 
    	   HOSTSLIST=`echo $JSON | jq .hosts -r` 
	   echo "`date`: create inventory : $HOSTSLIST"
           awx inventory create --name "$NAME" --organization "$org" --description "$DESC"
	   for invhost in  `cat $HOSTSLIST  | jq .hosts[].name -r `
	   do
		echo $invhost
    	   	INPUTS="{\"username\": \"\",\"ssh_key_data\": \"`cat ~/.ssh/id_rsa`\"}"
		awx host create --name "$invhost>" --inventory "$NAME" 
    	   	awx credential create --name "${invhost}" --description "${DESC}"  --credential_type "Machine" --organization "${org}" --inputs "${INPUTS}"
	   done
	done
done
exit








###############################################################################################################
#  Create projects
#######################A########################################################################################
echo "`date`: Create projects"
redis-cli keys "*"  |grep ansibleautomationmananger:projects:name | awk -F"ansibleautomationmananger:projects:name:" '{ print $2 }'  > /tmp/$$.projects.list
for project in `cat demo.json | jq .organization[].projects[].name -r`
do
    echo "`date`: Project : $project" 
    JSON=`cat demo.json | jq ' .organization[].projects[]  | {"name": .name , "description": .description }' -c  |  grep "\"${project}\""`
    echo "`date`: $JSON"
    NAME=`echo $JSON | jq .name -r | tr '_' ' '`
    DESC=`echo $JSON | jq .description -r | tr '_' ' '`
    awx projects create --name "${NAME}" --description "${DESC}" 
    myid=`awx projects list --name "${NAME}"|jq ".results[].id"`
    echo "`date`: The project $project has mow the id $myid"
    awx projects modify $myid --name "${NAME}" --description "${DESC}"   >/dev/null 2>&1
    sed -i "s/^$org$//" /tmp/$$.projects.list
done

cat /tmp/$$.projects.list



