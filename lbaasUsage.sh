#!/bin/bash

########################################################
#                                                      #
# Get usage for load balancers and send it to MySql    #
#                                                      #
# V1.0                                                 #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

LOCATION=$(hostname -f | cut -d"." -f2)
MYSQLSOURCE="XXXX"
MYSQLSTORE="XXXX"
MYSQLUSER="XXXX"
MYSQLPASS="XXXX"


EXCLUDE="127.0.0.1"

# Get a list of all SSL terminated load balancers, TCP transports

mysql -h$MYSQLSOURCE -u$MYSQLUSER -p$MYSQLPASS loadbalancing --skip-column-names -e "select loadbalancer_id, secure_port from lb_ssl where enabled=1" | while read LBID PORT
do
         # Get the IP from the account id
         IP=$(mysql -h$MYSQLSOURCE -u$MYSQLUSER -p$MYSQLPASS loadbalancing --skip-column-names -e "select ip_address from virtual_ip_ipv4 where id in (select virtualip_id from loadbalancer_virtualip where loadbalancer_id=$LBID)")
         
         # Generate an exlude list that contains only the SSL terminating load balancers
         EXCLUDE="$EXCLUDE|$IP:$PORT"
         echo $EXCLUDE > /tmp/exclude.list

         # Check if the IP is raised on the current traffic manager
         LBSSL=$(ip addr show | grep -w $IP)

         if [ "$LBSSL" != "" ]
         then
              # Get the counters
              BYTESIN=$(iptables -nvx -L INPUT | grep -w $IP | grep "dpt:$PORT" | tr -s [:blank:] | cut -d' ' -f3 | awk '{sum+=$1} END {print sum;}')
              BYTESOUT=$(iptables -nvx -L OUTPUT | grep -w $IP | grep "spt:$PORT" | tr -s [:blank:] | cut -d' ' -f3 | awk '{sum+=$1} END {print sum;}')

              if [ "$BYTESIN" = "" ]
              then
                  BYTESIN=0
              fi

              if [ "$BYTESOUT" = "" ]
              then
                  BYTESOUT=0
              fi

              # Remove the iptable rules
              iptables -D INPUT -d $IP -p tcp --dport $PORT 2>/dev/null
              iptables -D OUTPUT -s $IP -p tcp --sport $PORT 2>/dev/null

              # Re-add the iptable rules
              iptables -A INPUT -d $IP -p tcp --dport $PORT
              iptables -A OUTPUT -s $IP -p tcp --sport $PORT

              # Get the concurrent connections
              CCONN=$(ss -n state established src $IP | wc -l)

              # Send to MySql

	      CDATE=$(date +"%F %T")

              #echo "LBID: $LBID, IP: $IP, PORT: $PORT, SSL Terminated: YES, BYTES IN: $BYTESIN, BYTES OUT: $BYTESOUT, Connections: $CCONN"
	      mysql -h$MYSQLSTORE -u$MYSQLUSER -p$MYSQLPASS traffic_counter -e "insert into lb_usage (loadbalancer_id, ip, port, ssl_terminated, protocol, bytes_in, bytes_out, concurrent_conns, date) values ($LBID, '$IP', $PORT, 'YES', 'tcp', $BYTESIN, $BYTESOUT, $CCONN, '$CDATE')"


         fi
done

EXCLUDE=$(cat /tmp/exclude.list)

#Get a list of all non-SSL terminated load balancers, TCP and UDP transports

ss -n state listening -4 | awk '{print $3}' | sort | uniq | sed 's/:/ /g' | grep -vi local | while read IP PORT
do
        LBID=$(mysql -h$MYSQLSOURCE -u$MYSQLUSER -p$MYSQLPASS loadbalancing --skip-column-names -e "select loadbalancer_id from loadbalancer_virtualip where virtualip_id in (select id from virtual_ip_ipv4 where ip_address='$IP') and port='$PORT'")

        if [ "$LBID" = "" ]
        then
          continue
        fi

        # Get the transport protocol
        PROTO=$(mysql -h$MYSQLSOURCE -u$MYSQLUSER -p$MYSQLPASS loadbalancing --skip-column-names -e "select protocol from loadbalancer where protocol='UDP' and id='$LBID'")

        if [ "$PROTO" = "UDP" ]
        then
            PROTO="udp"
        else
            PROTO="tcp"
        fi

        # Get the counters
        BYTESIN=$(iptables -nvx -L INPUT | grep -w $IP | grep "dpt:$PORT" | tr -s [:blank:] | cut -d' ' -f3 | awk '{sum+=$1} END {print sum;}')
        BYTESOUT=$(iptables -nvx -L OUTPUT | grep -w $IP | grep "spt:$PORT" | tr -s [:blank:] | cut -d' ' -f3 | awk '{sum+=$1} END {print sum;}')

        if [ "$BYTESIN" = "" ]
        then
            BYTESIN=0
        fi

        if [ "$BYTESOUT" = "" ]
        then
            BYTESOUT=0
        fi


        # Remove the iptable rules
        iptables -D INPUT -d $IP -p $PROTO --dport $PORT 2>/dev/null
        iptables -D OUTPUT -s $IP -p $PROTO --sport $PORT 2>/dev/null

        # Re-add the iptable rules
        iptables -A INPUT -d $IP -p $PROTO --dport $PORT
        iptables -A OUTPUT -s $IP -p $PROTO --sport $PORT

        # Get the concurrent connections
        CCONN=$(ss -n state established src $IP | wc -l)

        # Send to MySql

	CDATE=$(date +"%F %T")

        #echo "LBID: $LBID, IP: $IP, PORT: $PORT, SSL Terminated: NO, PROTO: $PROTO, BYTES IN: $BYTESIN, BYTES OUT: $BYTESOUT, Connections: $CCONN"
        mysql -h$MYSQLSTORE -u$MYSQLUSER -p$MYSQLPASS traffic_counter -e "insert into lb_usage (loadbalancer_id, ip, port, ssl_terminated, protocol, bytes_in, bytes_out, concurrent_conns, date) values ($LBID, '$IP', $PORT, 'NO', '$PROTO', $BYTESIN, $BYTESOUT, $CCONN, '$CDATE')"


done



