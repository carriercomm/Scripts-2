#########################################################
#                                                       #
# Script that creates iptables rules to gather traffic  #
# usage statistics for all load balancers on a host     #
#                                                       #
# V1.2                                                  #
# Konstantin Ivanov                                     #
#                                                       #
#########################################################

LOCATION=`/bin/hostname -f | cut -d"." -f2`

MYSQLHOST="mysql-XXXX.$LOCATION.XXXX.net"

TRAFFICLOG="/var/log/`hostname`-bandwidth.log"

/bin/cp /dev/null $TRAFFICLOG

IPLIST=$(/sbin/ifconfig | grep "inet addr" | awk '{print $2}' | cut -d ":" -f2 | grep -vi 127.0.0.1)

# Collect the current traffic stats

for IP in $IPLIST
do

  DATE=$(date "+%Y-%m-%d %H:%M:%S")

  echo -n $DATE >> $TRAFFICLOG
  echo -n " $IP " >> $TRAFFICLOG
  echo -n `/sbin/iptables -nvx -L INPUT | grep " $IP " | tr -s [:blank:] | cut -d' ' -f3 | awk '{sum+=$1} END {print sum;}'` >> $TRAFFICLOG
  echo " INPUT" >> $TRAFFICLOG

  echo -n $DATE >> $TRAFFICLOG
  echo -n " $IP " >> $TRAFFICLOG
  echo -n `/sbin/iptables -nvx -L OUTPUT | grep " $IP " | tr -s [:blank:] | cut -d' ' -f3 | awk '{sum+=$1} END {print sum;}'` >> $TRAFFICLOG
  echo " OUTPUT" >> $TRAFFICLOG
done

# Clear the stats

/sbin/iptables -Z

# Clean the iptalbes rules

for IP in $IPLIST
do
  /sbin/iptables -D INPUT -d $IP 2>/tmp/error.log
  /sbin/iptables -D OUTPUT -s $IP 2>/tmp/error.log
done

# Re-create the iptables rules to account for any new load balancers

for IP in $IPLIST
do
  /sbin/iptables -A INPUT -d $IP 2>/tmp/error.log
  /sbin/iptables -A OUTPUT -s $IP 2>/tmp/error.log
done

# Insert into MySQL

cat $TRAFFICLOG | while read DATE TIME IP COUNT FLOW
do 
  /usr/bin/mysql -h$MYSQLHOST -u$USER -p$PASS -e"insert into traffic_counter.traffic (ip, period, bytes, flow) values ('$IP','$DATE $TIME','$COUNT','$FLOW');" 2>/tmp/error.log
done
