#!/bin/bash
TS=$(date +%s)
docker build -t pknw1/notflix_adduser:$TS .

if [[ $# -eq 0 ]]
then
	docker tag pknw1/notflix_adduser:$TS pknw1/notflix_adduser:dev
else
	docker tag pknw1/notflix_adduser:$TS pknw1/notflix_adduser:$1	
	docker push pknw1/notflix_adduser:$1
fi

docker image ls | grep notflix_adduser
