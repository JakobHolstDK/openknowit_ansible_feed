inventory=`awx inventory list| jq ".results[0].id"`
for NEWHOSTNAME in `curl -X POST "https://randommer.io/api/Name/BrandName?startingWords=linux" -H  "accept: */*" -H  "X-Api-Key: df84ba4303a74c5cb2a394746a595b24" -d "" 2>/dev/null | jq .[] -r`
do

	IID=`echo $NEWHOSTNAME |base64`
	awx hosts create  \
	--name   $NEWHOSTNAME \
	--inventory 4  \
	--description "Auto generated for demo purpose" \
	--enabled 1  \
	--instance_id  $IID
done

