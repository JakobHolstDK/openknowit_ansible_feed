#!/usr/bin/env bash
LOCALKEY="$(jq -R -s '.' < ~/.ssh/id_rsa -r)"
REMOTEKEY="$(jq -R -s '.' < ~/.ssh/id_rsa -r)"
vault kv put secret/project/openknowit/demogituser username="${GITUSER}" password="${GITPASS}" key="$LOCALKEY" passphrase=""
vault kv put secret/project/openknowit/demosshuser username="knowit" password="" key="$REMOTEKEY" passphrase="" becomemethod="sudo" becomeusername="root"
vault kv put secret/project/openknowit/remotesshuser username="knowit" password="Run44Fun2!!!" key="$REMOTEKEY" passphrase="" becomemethod="sudo" becomeusername="root" becomepassword="Run44Fun2!!!"


