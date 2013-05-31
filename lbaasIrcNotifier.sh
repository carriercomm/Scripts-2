#!/bin/bash

########################################################
#                                                      # 
# Script that checks Zenoss for alerts and notifies    #
# in IRC. Run it locally on the Zenoss server.         #
#                                                      #
# V2.0                                                 #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

chan="#lbaas"
mode="+i"
nick="LBaaSZenossBot"
name="Zenoss Alert Bot"
host="irc.XXXX.com"
port="6667"


exec 3<> irc-errors 2>&3-

echo -n "Connecting to $host on port $port ... "
if ! exec 3<> /dev/tcp/$host/$port; then
        echo "`basename $0`: unable to connect to $host:$port"
        exit 1
fi
echo "Done"

exec 0<&3 1>&3-

echo "USER $nick ${mode:-+iw} $nick :$name"
echo "NICK $nick"

sleep 5

echo "JOIN $chan"

SLEEPER="0";

while true
do

        echo "PONG"

        if [ "$SLEEPER" -eq "0" ]
        then

                ALERT=$(curl -s -X POST -H "Accept: application/json" -H "Content-Type: application/json" -u XXXX:XXXX http://zenoss.XXXX.net:8080/zport/dmd/Events/evconsole_router -d '{"action":"EventsRouter","method":"query","data":[{"sort":"severity","dir":"DESC","params":"{\"severity\":[5],\"eventState\":[0]}","start":0,"limit":100}],"type":"rpc","tid":5}' | python -mjson.tool | grep totalCount | awk -F":" '{print $2}' | sed -e 's/^[ \t]*//')

                if [ "$ALERT" -gt "0" ]
                then
                        echo "PRIVMSG $chan :============================ Zenoss Active Alerts: $ALERT ============================"
                        curl -s -X POST -H "Accept: application/json" -H "Content-Type: application/json" -u XXXX:XXXX http://zenoss.XXXX.net:8080/zport/dmd/Events/evconsole_router -d '{"action":"EventsRouter","method":"query","data":[{"sort":"severity","dir":"DESC","params":"{\"severity\":[5],\"eventState\":[0]}","start":0,"limit":100}],"type":"rpc","tid":5}' | python -mjson.tool | grep summary | awk -F"\"" '{print $4}' | while read MESSAGE;do echo "PRIVMSG $chan :$MESSAGE";done
                        echo "PRIVMSG $chan :========= Visit zenoss.lbaas.rackspace.net:8080 for more information ============"

                fi
        fi

        sleep 30

        let SLEEPER=$SLEEPER+1

        if [ "$SLEEPER" -ge "10" ]
        then
                SLEEPER="0"
        fi


done

exec 1<&- 2<&-
