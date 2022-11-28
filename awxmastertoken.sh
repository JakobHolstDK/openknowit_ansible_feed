#!/usr/bin/env bash


BEFORE=$(awx tokens list |jq .results[].id)
TOKEN=$(awx --conf.color False tokens create |jq '{"id": .id, "token": .token }')
id=$(echo $TOKEN | jq .id -r)
t=$(echo $TOKEN | jq .token -r)
TH=$(echo $TOWER_HOST | awk -F'://' '{ print $2 }' )
vault kv put secret/awx/${TH}  token="${t}" id="${id}"

for DELID in $BEFORE;
do
	echo $DELID
	awx tokens delete $DELID
done

vault kv get secret/awx/${TH}

