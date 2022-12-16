#!/usr/bin/env bash
if [[ $2 == "start" ]];
then
    tmux vaultdevserver -A -s myprogramsession \; send -t myprogramsession "nohup bin/vault server -dev &>/dev/null &" ENTER \; 
fi



