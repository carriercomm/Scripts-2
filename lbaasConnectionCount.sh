#!/bin/bash


########################################################
#                                                      # 
# Get the top 10 connections. Usefull to detect DDoS   #
# customers  					       #
#                                                      #
# V1.1                                                 #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

ethsvc=`ifconfig eth-svc | grep -w inet | awk '{print $2}' | cut -d":" -f2`
ethpub=`ifconfig eth-pub | grep -w inet | awk '{print $2}' | cut -d":" -f2`

netstat -antup | awk '{print $4}' | awk -F\: '{print $1}' | egrep -v "$ethsvc|$ethpub" | sort | uniq -c | sort -nr | head -n 10 > /tmp/ips.list

echo "
============================================================
           Top Ten Load Balancers by connection 
============================================================"

conn_list=$(cat /tmp/ips.list | while read x; 

  do

    conn_count=`echo $x | awk '{print $1}'`
    conn_ip=`echo $x | awk '{print $2}'`
    conn_tg=`grep -lw $conn_ip /opt/zeus/zxtm/conf/flipper/* | cut -d"/" -f7`
    conn_vs=`grep -lw $conn_tg /opt/zeus/zxtm/conf/vservers/* | cut -d"/" -f7 | wc -l`

    if [ $conn_vs -ge 2 ]; then

      conn_vs_final=`grep -lw $conn_tg /opt/zeus/zxtm/conf/vservers/* | cut -d"/" -f7 | while read format; do echo -n "${format}," ;done | sed 's/,$//'`

    else

      conn_vs_final=`grep -lw $conn_tg /opt/zeus/zxtm/conf/vservers/* | cut -d"/" -f7`

    fi


    echo "$conn_count $conn_ip $conn_tg $conn_vs_final"

  done)

echo "connections ip_address traffic_group virtual_server
$conn_list" | column -t 
echo

rm -f /tmp/ips.list
