#!/usr/bin/env bash
INPUTS="$(jq -R -s '.' < ~/.ssh/id_rsa -r)"
vault kv put secret/project/openknowit/demogituser username="${GITUSER}" password="${GITPASS}" key="$INPUTS" passphrase=""
vault kv put secret/project/openknowit/demosshuser username="knowit" password="" key="$INPUTS" passphrase="" becomemethod="sudo" becomeusername="root"


