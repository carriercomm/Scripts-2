#!/bin/bash

########################################################
#                                                      #
# Check for high number of UDP packets on a traffic    #
# manager and report the targeted Load Balancer in     #
# Zenoss and IRC                                       #
#                                                      #
# V1.0                                                 #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

UDPTHRESHOLD="1000"
PACKETSTOCOUNT="2000"
HOST=$(hostname)
TIMESTAMP=$(date +%s)

echo $(route -n | grep pub | awk '{print $1}' | grep -vi "0.0.0.0" | awk -F"." '{print $1 "." $2}') > /tmp/ips

sed -i 's/ /|/g' /tmp/ips

IPS=`cat /tmp/ips`

tcpdump -n -c $PACKETSTOCOUNT -i eth-pub udp | awk '{print $5}' | awk -F"." '{print $1 "." $2 "." $3 "." $4}' | grep -vi ":" >> /tmp/udpdump-$TIMESTAMP.log

cat /tmp/udpdump-$TIMESTAMP.log | egrep $IPS | sort | uniq -c | sort -n | tail -1 | while read UDPCOUNT IP
do 
  if [ "$UDPCOUNT" -ge "$UDPTHRESHOLD" ]
  then
    echo "Detected $UDPCOUNT UDP Packets to $IP"
    
    ALERT="curl 'http://XXXX:XXXX.XXXX.net:8080/zport/dmd/ZenEventManager/manage_addEvent?device=$HOST&&summary=UDP%20DoS%20Detected%20on%20$HOST%20targeting%20$IP&severity=5&eventClass=/Cmd/Fail&DeviceGroups=/environments/production'"
    eval $ALERT
  fi
done

rm /tmp/ips
rm /tmp/udpdump-$TIMESTAMP.log
