#!/bin/bash

########################################################
#                                                      # 
# Get the top 5 established, syn_received, time_wait   #
# and last_ack connections                             #
#                                                      #
# V1.0                                                 #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

EXCLUDEIP=`echo $(cat /etc/network/interfaces | grep address | awk '{print $2}') | sed 's/ /|/g'`

TIME_WAIT=$(ss -n state time-wait | awk '{print $3}' | awk -F":" '{print $1}' | sort | uniq -c | sort -rn | egrep -vwi "$EXCLUDEIP" | head -5)
ESTABLISHED=$(ss -n state established | awk '{print $3}' | awk -F":" '{print $1}' | sort | uniq -c | sort -rn | egrep -vwi "$EXCLUDEIP" | head -5)
SYN_RECEIVED=$(ss -n state syn-recv | awk '{print $3}' | awk -F":" '{print $1}' | sort | uniq -c | sort -rn | egrep -vwi "$EXCLUDEIP" | head -5)
LAST_ACK=$(ss -n state last-ack | awk '{print $3}' | awk -F":" '{print $1}' | sort | uniq -c | sort -rn | egrep -vwi "$EXCLUDEIP" | head -5)

let i=0
for num in $TIME_WAIT
do
  array_timewait[i]="$num"
  let i=i+1
done

let i=0
for num in $ESTABLISHED
do
  array_established[i]="$num"
  let i=i+1
done

let i=0
for num in $SYN_RECEIVED
do
  array_synreceived[i]="$num"
  let i=i+1
done

let i=0
for num in $LAST_ACK
do
  array_lastack[i]="$num"
  let i=i+1
done

echo -e "ESTABLISHED           SYN_RECEIVED         TIME_WAIT               LAST_ACK"
echo -e "======================================================================================="
for i in 0 2 4 6 8
do
  echo -n "${array_established[$i]} " 
  echo -n -e "${array_established[$i+1]}\t" 
  echo -n "${array_synreceived[$i]} " 
  echo -n  -e "${array_synreceived[$i+1]}\t" 
  echo -n "${array_timewait[$i]} " 
  echo -n -e "${array_timewait[$i+1]}\t" 
  echo -n "${array_lastack[$i]} " 
  echo -e "${array_lastack[$i+1]}"
done | column -t
