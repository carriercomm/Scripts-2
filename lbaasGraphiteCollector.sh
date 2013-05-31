#!/bin/bash

########################################################
#                                                      # 
# Script that collects various data and sends it to    #
# Graphite					       #
#						       #
# V1.3                                                 #
#						       #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

GSERVER="10.13.65.161"
GPORT="2003"

if [ ! -f /etc/graphite.servers ]
then
	echo "Missing /etc/graphite.servers configuration file!"
	echo "Create one and add the servers to be contacted via SNMP"
	echo "in the form of ztm-n01.ord1, or ztm-n08.lon3"
	exit 1
fi

get_nic_data()
{
	# Get bytes in/out on the eth-pub interface

	echo $LOCATION.prod.$ZTMNAME.pub.in $(snmpwalk -v 1 -c public $SERVER IF-MIB::ifInOctets.$(snmpwalk -v 1 -c public $SERVER IF-MIB::ifDescr | grep pub | cut -d"." -f2 | awk '{print $1}') | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT &
	echo $LOCATION.prod.$ZTMNAME.pub.out $(snmpwalk -v 1 -c public $SERVER IF-MIB::ifOutOctets.$(snmpwalk -v 1 -c public $SERVER IF-MIB::ifDescr | grep pub | cut -d"." -f2 | awk '{print $1}') | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT &

	# Get bytes in/out on the eth-svc interface

	echo $LOCATION.prod.$ZTMNAME.svc.in $(snmpwalk -v 1 -c public $SERVER IF-MIB::ifInOctets.$(snmpwalk -v 1 -c public $SERVER. IF-MIB::ifDescr | grep svc | cut -d"." -f2 | awk '{print $1}') | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT &
        echo $LOCATION.prod.$ZTMNAME.svc.out $(snmpwalk -v 1 -c public $SERVER IF-MIB::ifOutOctets.$(snmpwalk -v 1 -c public $SERVER IF-MIB::ifDescr | grep svc | cut -d"." -f2 | awk '{print $1}') | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT &

	# Get bytes in/out on the eth-exnet interface
	
        echo $LOCATION.prod.$ZTMNAME.exnet.in $(snmpwalk -v 1 -c public $SERVER IF-MIB::ifInOctets.$(snmpwalk -v 1 -c public $SERVER IF-MIB::ifDescr | grep exnet | cut -d"." -f2 | awk '{print $1}') | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT &
        echo $LOCATION.prod.$ZTMNAME.exnet.out $(snmpwalk -v 1 -c public $SERVER IF-MIB::ifOutOctets.$(snmpwalk -v 1 -c public $SERVER IF-MIB::ifDescr | grep exnet | cut -d"." -f2 | awk '{print $1}') | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT &

}

get_cpuload_data()
{
	# Get current CPU load
	
	echo $LOCATION.prod.$ZTMNAME.cpu.curload $(snmpwalk -v 1 -c public $SERVER.lbaas.rackspace.net UCD-SNMP-MIB::laLoad.1 | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT &
}

get_memoryfree_data()
{
	# Get the free memory in KB

	echo $LOCATION.prod.$ZTMNAME.mem.totalfree $(snmpwalk -v 1 -c public $SERVER.lbaas.rackspace.net UCD-SNMP-MIB::memTotalFree.0 | awk -F ": " '{print $2}' | cut -d" " -f1) $(date +%s) | nc $GSERVER $GPORT &
}

get_diskfree_data()
{
	# Get the disk space in use at / in percent

	echo $LOCATION.prod.$ZTMNAME.disk.rootfree $(snmpwalk -v 1 -c public $SERVER.lbaas.rackspace.net UCD-SNMP-MIB::dskPercent.1 | awk -F ": " '{print $2}') $(date +%s) | nc $GSERVER $GPORT & 
}

get_zendesk_data()
{
	# Get all Open and New tickets to LBaaS Operations and Escalations

	echo zendesk.prod.tickets $(curl -k -s -u $USER:$PASS -X GET "https://XXXX/rules/25456706" | grep "Rackspace Cloud Ticketing :" | cut -d"(" -f2 | cut -d")" -f1) $(date +%s) | nc $GSERVER $GPORT &
}

get_customers_data()
{
	# Get the total number of customers in ORD, DFW and LON

	echo ord1.prod.customers $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select distinct(account_id) from loadbalancer where status='active';" | wc -l) $(date +%s) | nc $GSERVER $GPORT &

	echo dfw1.prod.customers $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select distinct(account_id) from loadbalancer where status='active';" | wc -l) $(date +%s) | nc $GSERVER $GPORT &

	echo lon3.prod.customers $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select distinct(account_id) from loadbalancer where status='active';" | wc -l) $(date +%s) | nc $GSERVER $GPORT &
}

get_ips_data()
{
	# Get the total number of available IP's in ORD, DFW and LON

	echo ord1.prod.ips $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select count(*) from virtual_ip_ipv4 where type='public' and is_allocated=0 and cluster_id=1;" | grep -vi count) $(date +%s) | nc $GSERVER $GPORT &

	echo ord1.prod.ipsc2 $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e"select count(*) from virtual_ip_ipv4 where type='public' and is_allocated=0 and cluster_id=2;" | grep -vi count) $(date +%s) | nc $GSERVER $GPORT &

	echo ord1.prod.ipsc3 $(mysql -h$MYSQLHOST -u$USER -p$PASS-Dloadbalancing -e"select count(*) from virtual_ip_ipv4 where type='public' and is_allocated=0 and cluster_id=3;" | grep -vi count) $(date +%s) | nc $GSERVER $GPORT &

	echo dfw1.prod.ips $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e"select count(*) from virtual_ip_ipv4 where type='public' and is_allocated=0 and cluster_id=1;" | grep -vi count) $(date +%s) | nc $GSERVER $GPORT &

	echo dfw1.prod.ips2 $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e"select count(*) from virtual_ip_ipv4 where type='public' and is_allocated=0 and cluster_id=2;" | grep -vi count) $(date +%s) | nc $GSERVER $GPORT &
	
	echo lon3.prod.ips $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e"select count(*) from virtual_ip_ipv4 where type='public' and is_allocated=0 and cluster_id=1;" | grep -vi count) $(date +%s) | nc $GSERVER $GPORT &

	echo syd2.prod.ips $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e"select count(*) from virtual_ip_ipv4 where type='public' and is_allocated=0 and cluster_id=1;" | grep -vi count) $(date +%s) | nc $GSERVER $GPORT &

}

get_errors_data()
{
	# Get the load balancers in ERROR status in ORD, DFW and LON

	echo ord1.prod.lberror $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select status from loadbalancer;" | grep -i error | wc -l) $(date +%s) | nc $GSERVER $GPORT &

	echo dfw1.prod.lberror $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select status from loadbalancer;" | grep -i error | wc -l) $(date +%s) | nc $GSERVER $GPORT &

	echo lon3.prod.lberror $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select status from loadbalancer;" | grep -i error | wc -l) $(date +%s) | nc $GSERVER $GPORT &
}

get_lbcreate_data()
{
	# Get the create times for load balancers in ORD, DFW and LON for the last 24 hours

	for LOCATION in ord1 dfw1 lon3;
	do
        	mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select unix_timestamp(loadbalancer.created) as start_create, TIME_TO_SEC(TIMEDIFF(loadbalancer_event.created,loadbalancer.created)) as time_diff from loadbalancer, loadbalancer_event where loadbalancer.id=loadbalancer_event.loadbalancer_id and event_title='Load Balancer Successfully Created' and loadbalancer.created > CURDATE()  order by start_create;" | cut -d"|" -f1,2 | grep -vi start > /tmp/lbtimes-$(date +%F)

        	while read EPOCHTIME CREATETIME; do echo "$LOCATION.prod.lbcreatetimes $CREATETIME $EPOCHTIME" | nc $GSERVER $GPORT;done < /tmp/lbtimes-$(date +%F)
        	rm -f /tmp/lbtimes-$(date +%F)
	done
}


get_capacity_data()
{
	# Calculate the capacity for each cluster based on max of 1200 LBs per traffic manager

	totalCapacityCluster6=7200
	totalCapacityCluster3=3600

	totalLBORD1=$(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select count(*) from loadbalancer where host_id <=8 and status='ACTIVE';" | grep -vi count)
	let totalPercentORD1=(100*totalLBORD1)/totalCapacityCluster6

	totalLBORD2=$(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select count(*) from loadbalancer where host_id >8 and status='ACTIVE';" | grep -vi count)
        let totalPercentORD2=(100*totalLBORD2)/totalCapacityCluster3

	totalLBDFW1=$(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select count(*) from loadbalancer where host_id <=8 and status='ACTIVE';" | grep -vi count)
        let totalPercentDFW1=(100*totalLBDFW1)/totalCapacityCluster6

        totalLBDFW2=$(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select count(*) from loadbalancer where host_id >8 and status='ACTIVE';" | grep -vi count)
        let totalPercentDFW2=(100*totalLBDFW2)/totalCapacityCluster3

	totalLBLON1=$(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing -e "select count(*) from loadbalancer where host_id <=8 and status='ACTIVE';" | grep -vi count)
        let totalPercentLON1=(100*totalLBLON1)/totalCapacityCluster6

        echo ord1.prod.capacitycluster1 $totalPercentORD1 $(date +%s) | nc $GSERVER $GPORT &
	echo ord1.prod.capacitycluster2 $totalPercentORD2 $(date +%s) | nc $GSERVER $GPORT &
	echo dfw1.prod.capacitycluster1 $totalPercentDFW1 $(date +%s) | nc $GSERVER $GPORT &
	echo dfw1.prod.capacitycluster2 $totalPercentDFW2 $(date +%s) | nc $GSERVER $GPORT &
	echo lon3.prod.capacitycluster1 $totalPercentLON1 $(date +%s) | nc $GSERVER $GPORT &

	echo ord1.prod.lbinstancescluster1 $totalLBORD1 $(date +%s) | nc $GSERVER $GPORT &
	echo ord1.prod.lbinstancescluster2 $totalLBORD2 $(date +%s) | nc $GSERVER $GPORT &
	echo dfw1.prod.lbinstancescluster1 $totalLBDFW1 $(date +%s) | nc $GSERVER $GPORT &
	echo dfw1.prod.lbinstancescluster2 $totalLBDFW2 $(date +%s) | nc $GSERVER $GPORT &
	echo lon3.prod.lbinstancescluster1 $totalLBLON1 $(date +%s) | nc $GSERVER $GPORT &

}

get_pingdom_totaluptime()
{
	# Set the Product identifier to match servers in Pingdom

	PRODUCT="XXXX"

	# Pingdom Credentials

	PINGDOMUSER="XXX"
	PINGDOMPASS="XXXX"
	PINGDOMBASE64=`echo $(echo -n "$PINGDOMUSER:$PINGDOMPASS" | base64) | sed 's/ //g'`
	PINGDOMTOKEN="XXXX"

	# Graphite Server to send data to

	GSERVER="XXXX"
	GPORT="2003"

	# Get the start of the current year and current time in epoch format

	STARTOFYEAREPOCH=$(date +"%s" -d "01/01/`date +'%Y'`")
	CURRENTTIMEEPOCH=$(date +"%s")
	SECONDSSINCEYEAR=$(expr $CURRENTTIMEEPOCH - $STARTOFYEAREPOCH)

	# Send whatever data we have to graphite from the previous run, to avoid null values

	echo pingdom.prod.totaluptime $(cat /tmp/pingdom.tmp) $(date +%s) | nc $GSERVER $GPORT &

	# Get the list of all id's for LBAAS related checks from Pingdom

	LBAASCHECKID=$(curl -s -X GET -H "Authorization: Basic $PINGDOMBASE64" -H "App-Key: $PINGDOMTOKEN" 'https://api.pingdom.com/api/2.0/checks'  | python -mjson.tool | grep -B 4 $PRODUCT | grep id | awk '{print $2}' | cut -d"," -f1)

	# Get the count of uptime in seconds for each LBAAS id (Traffic Manager) and calculate the total downtime in percent for YTD

	TOTALDOWN=0

	DOWNTIMES=$(for i in $LBAASCHECKID;do curl -s -X GET -H "Authorization: Basic $PINGDOMBASE64" -H "App-Key: $PINGDOMTOKEN" "https://api.pingdom.com/api/2.0/summary.average/${i}?includeuptime=true&from=${STARTOFYEAREPOCH}" | python -mjson.tool;done | grep totaldown | awk -F":" '{print $2}' | cut -d"," -f1 | sed -e 's/^[ \t]*//')

	TOTALCHECKS=$(echo $DOWNTIMES | wc -w)

	for DOWNTIME in $(echo $DOWNTIMES);do let TOTALDOWN=$TOTALDOWN+$DOWNTIME;done

	let AVERAGEDOWN=$TOTALDOWN/$TOTALCHECKS

	TOTALPERCENTDOWN=$(echo "scale=3;$AVERAGEDOWN*100/$SECONDSSINCEYEAR" | bc)

	TOTALPERCENTUP=$(echo "scale=3;100-$TOTALPERCENTDOWN" | bc)
	
	echo $TOTALPERCENTUP > /tmp/pingdom.tmp
}


get_total_backend_nodes()
{
	echo ord1.prod.backendnodes $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing --skip-column-names -e "select count(distinct(ip_address)) from node") $(date +%s) | nc $GSERVER $GPORT &
	echo dfw1.prod.backendnodes $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing --skip-column-names -e "select count(distinct(ip_address)) from node") $(date +%s) | nc $GSERVER $GPORT &
	echo lon3.prod.backendnodes $(mysql -h$MYSQLHOST -u$USER -p$PASS -Dloadbalancing --skip-column-names -e "select count(distinct(ip_address)) from node") $(date +%s) | nc $GSERVER $GPORT &
}

# Main Program

while read SERVER
do
	ZTMNAME=$(echo $SERVER | cut -d"." -f1)
	LOCATION=$(echo $SERVER | cut -d"." -f2)

	get_nic_data

	get_cpuload_data

	get_memoryfree_data

	get_diskfree_data

done < /etc/graphite.servers

get_zendesk_data

get_customers_data

get_ips_data

get_errors_data

get_lbcreate_data

get_capacity_data

get_pingdom_hosts_status
get_pingdom_totaluptime

get_total_backend_nodes
