#!/bin/bash


########################################################
#                                                      # 
# IRC bot that responds to commands and gathers info   #
#                                                      #
# V3.0                                                 #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

chan="#lbaas"
mode="+i"
nick="LBaaSInfoBot"
name="LBaaS Information Bot"
host="$1"
port="$2"

help()
{
	echo "PRIVMSG $REPLYTO :=========================================="
	echo "PRIVMSG $REPLYTO :Available bot commands:"
	echo "PRIVMSG $REPLYTO :=========================================="
	echo "PRIVMSG $REPLYTO :!help:   This List"
	echo "PRIVMSG $REPLYTO :!oncall: Engineers on call Schedule"
	echo "PRIVMSG $REPLYTO :!docs:   Helpfull Links for docs and tools"
	echo "PRIVMSG $REPLYTO :!stats:  Real time LBaaS Statistics"
	echo "PRIVMSG $REPLYTO :!api:    Current API versions"
	echo "PRIVMSG $REPLYTO :=========================================="


}

oncall()
{
	echo "PRIVMSG $REPLYTO :=========================================="
        echo "PRIVMSG $REPLYTO :Engineers on call:"
        echo "PRIVMSG $REPLYTO :=========================================="
	echo "PRIVMSG $REPLYTO :$(cat /home/kivanov/oncall.list)"
	echo "PRIVMSG $REPLYTO :=========================================="
}

docs()
{
	echo "PRIVMSG $REPLYTO :=========================================="
        echo "PRIVMSG $REPLYTO :Documentation and Support Tools Links:"
        echo "PRIVMSG $REPLYTO :=========================================="
        echo "PRIVMSG $REPLYTO :Some link here"
	echo "PRIVMSG $REPLYTO :=========================================="
}

stats()
{
	echo "PRIVMSG $REPLYTO :=========================================="
        echo "PRIVMSG $REPLYTO :Real time LBaaS Statistics:"
	echo "PRIVMSG $REPLYTO :=========================================="

}

api()
{
        echo "PRIVMSG $REPLYTO :=========================================="
        echo "PRIVMSG $REPLYTO :Current API Version:"
        echo "PRIVMSG $REPLYTO :=========================================="
        echo "PRIVMSG $REPLYTO :$(curl -I -s -u XXXX:XXXX -X GET -H 'Accept: application/json' -H 'bypass-auth: true' https://XXXX/v1.0/management/clusters | grep Server | cut -d':' -f2 | sed 's/^ //g')"
        echo "PRIVMSG $REPLYTO :=========================================="
}

exec 3<> irc-errors 2>&3-

if [ ! "$2" ]; then
	echo "usage: `basename $0` [hostname] [port]"
	exit 1
fi

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

while read; do

	# The received private or channel message format is:
	#                           $1                          $2     $3      $4 
	# :Konstantin!Konstantin@rackspace-6cm.6df.5t95an.IP PRIVMSG testBot :!help
	# :Konstantin!Konstantin@rackspace-6cm.6df.5t95an.IP PRIVMSG #botschool :!help

	set -- ${REPLY//$'\r'/}

	[ "$1" == "PING" ] && echo "PONG $2"

	echo "`date` $REPLY" >> /tmp/irc.log
  
	REQUEST=$4
	
	if [ "$3" == "$nick" ]
	then
		REPLYTO=$(echo $1 | cut -d':' -f2 | cut -d'!' -f1)
	else
		REPLYTO=$chan
	fi

	echo "Replying to $REPLYTO" >> /tmp/irc.log 

	case $REQUEST in
        	":!help")
             		 help
        	;;
        	":!oncall")
              		oncall
        	;;
		":!docs")
                        docs
                ;;
		":!stats")
                        stats
                ;;
		":!api")
                        api
                ;;
	esac
	
done

exec 1<&- 2<&-


