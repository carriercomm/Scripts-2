from bottle import get, post, request, response, run, error, static_file, route, redirect, view
from socket import *
import mysql.connector		# from https://launchpad.net/myconnpy
import time
import subprocess, re
from subprocess import call


########################################################
#                                                      # 
# Web app that returns information about loadbalancers #
# and grapths bandwidth with Graphite in real time     #
#                                                      #
# V2.4                                                 #
# Konstantin Ivanov                                    #
#                                                      #
########################################################

head = '''<head>
        <meta charset="utf-8" />
        <LINK href="static/style.css" type=text/css rel=stylesheet>
        <LINK href="static/forms.css" type=text/css rel=stylesheet>
        <LINK href="static/lists.css" type=text/css rel=stylesheet>
        <LINK href="static/polls.css" type=text/css rel=stylesheet>
    </head>'''

mysqluser = "XXXX"
mysqlpwd = "XXXX"
trafficmanager = ""
accountid = ""

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')


@get('/login')
@view('login')
def login():
    failed = request.query.auth
    if request.get_cookie("account", secret='some-secret-key'):
        redirect('/')
    else:
        return dict(failed=failed)


@post('/login')
def login_submit():
    name     = request.forms.get('name')
    password = request.forms.get('password')

    if check_login(name, password):
        response.set_cookie("account", name, secret='some-secret-key')
        redirect('/')
    else:
        redirect('/login?auth=fail')


def check_login(name, password):
    if name == "XXXX" and password == "XXXX":
        return True
    else:
        return False


def getGeneralData(lbid,dc,mysqlhost1,mysqlhost2):
    global trafficmanager
    global accountid

    db = mysql.connector.Connect(host=mysqlhost1, user=mysqluser,password=mysqlpwd,database="loadbalancing")
    cursor = db.cursor()
    cursor.execute("SELECT account_id, name, protocol, port, algorithm, connection_logging, sessionPersistence, status, host_id, created, updated FROM loadbalancer where id=%s", tuple([lbid]))

    resultset = head

    if cursor.rowcount != 0:
        for account_id, name, protocol, port, algorithm, connection_logging, sessionPersistence, status, host_id, created, updated in cursor:
            
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">ID</th><td>''' + str(lbid) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Account</th><td>''' + str(account_id) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Name</th><td>''' + str(name) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Protocol</th><td>''' + str(protocol) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Port</th><td>''' + str(port) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Algotithm</th><td>''' + str(algorithm) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Logging</th><td>''' + str(connection_logging) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Persistence</th><td>''' + str(sessionPersistence) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Status</th><td>''' + str(status) + "</td></tr>"
            
            cursor.execute("SELECT traffic_manager_name FROM host where id = %s;", tuple([host_id]))

            if cursor.rowcount != 0:
                trafficmanagertupel = cursor.fetchone()
                trafficmanager = trafficmanagertupel[0]
            else:
                trafficmanager = "Unknown"

            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Hosted</th><td>''' + trafficmanager + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Created</th><td>''' + str(created) + "</td></tr>"
            resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Last Updated</th><td>''' + str(updated) + "</td></tr>"

            accountid = str(account_id) 

    else:
         resultset = "No data"

    cursor.execute("select ip_address from virtual_ip_ipv4 where id = (select virtualip_id from loadbalancer_virtualip where loadbalancer_id = %s limit 1);", tuple([lbid]))

    if cursor.rowcount != 0:
        lbip = cursor.fetchone()
    else:
        lbip = "Unknown"

    resultset = resultset + "<tr>" + '''<th vAlign="bottom" bgColor="#eeeffd">IP</th><td>''' + lbip[0] + "</td></tr>"

    cursor.close()
    db.close()

    resultset = '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd" colspan="3">Loadbalancer General Information</th></tr><tr>''' + resultset + "</table></center>"

    return resultset


def getMigratedData(lbid,dc,mysqlhost1,mysqlhost2):
    global trafficmanager
    db = mysql.connector.Connect(host=mysqlhost2, user=mysqluser,password=mysqlpwd,database="traffic_broker")
    cursor = db.cursor()
    cursor.execute("SELECT date, time FROM events where lb_id=%s", tuple([lbid]))

    resultset = head

    migrated = False

    if cursor.rowcount != 0:
        for date, time in cursor:
            resultset = resultset + "<tr>" + "<td>" + str(date) + "</td>" + "<td>" + str(time) + "</td>" + "</tr>"
    else:
         resultset = "No data"

    cursor.execute("SELECT lb_id, cluster FROM migrated where lb_id=%s", tuple([lbid]))
    
    if cursor.rowcount != 0:
        for lb_id, cluster in cursor:
            if str(lb_id).strip() == "":
                migrated = False
                resultset = resultset + "<tr>" + "<td colspan=2><font color=green><center><b>Not Currently Migrated</b></center></font></td></tr>"
            else:
                resultset = resultset + "<tr>" + "<td colspan=2><font color=red><center><b>Currently Migrated</b></center></font></td></tr>"
                migrated = True
                if str(cluster.strip()) == "1":
                    trafficmanager = "ztm-n08." + str(dc) + "XXX" 
                else:
                    trafficmanager = "ztm-n12." + str(dc) + "XXX" 
    else:
         resultset = resultset + "<tr>" + "<td colspan=2>No Data</td></tr>"

    if not migrated:
        resultset = resultset + "<tr>" + "<td colspan=2><font color=green><center><b>Not Currently Migrated</b></center></font></td></tr>"

    cursor.close()
    db.close()

    resultset = '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd" colspan="3">Loadbalancer Migration Events</th></tr><tr><TD class=sideboxtext>Date</TD><TD class=sideboxtext>Time</TD>''' + resultset + "</table></center>"

    return resultset


def getLBEvents(lbid,dc,mysqlhost1,mysqlhost2):
    db = mysql.connector.Connect(host=mysqlhost1, user=mysqluser,password=mysqlpwd,database="loadbalancing")
    cursor = db.cursor()
    cursor.execute("select created, event_Description from loadbalancer_event where loadbalancer_id = %s", tuple([lbid]))

    resultset = head

    if cursor.rowcount != 0:
        for lb_id, event in cursor:
            resultset = resultset + "<tr>" + "<td>" + str(lb_id) + "</td>" + "<td>" + str(event) + "</td>" + "</tr>"
    else:
         resultset = "No data"

    cursor.close()
    db.close()

    resultset = '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd" colspan="3">Loadbalancer General Events</th></tr><tr><TD class=sideboxtext>Date</TD><TD class=sideboxtext>Event Description</TD>''' + resultset + "</table></center>"

    return resultset


def getNodeDetails(lbid, mysqlhost1):
    db = mysql.connector.Connect(host=mysqlhost1, user=mysqluser,password=mysqlpwd,database="loadbalancing")
    cursor = db.cursor()
    cursor.execute("select ip_address, port, type, node_condition, status from node where loadbalancer_id = %s", tuple([lbid]))

    resultset = head

    if cursor.rowcount != 0:
        for ipaddress, port, type, condition, status in cursor:
            resultset = resultset + "<tr><td>" + str(ipaddress) + "</td><td>" + str(port) + "</td><td>" + str(type) + "</td><td>" + str(condition) + "</td><td>" + str(status) + "</td></tr>"
    else:
         resultset = "No data"

    cursor.close()
    db.close()

    resultset = '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd" colspan="5">Back-end Nodes General Information</th></tr><tr><TD class=sideboxtext>IP</TD><TD class=sideboxtext>Port</TD><TD class=sideboxtext>Type</TD><TD class=sideboxtext>Condition</TD><TD class=sideboxtext>Status</TD>''' + resultset + "</table></center>"

    return resultset


def getNodeEvents(lbid,dc,mysqlhost1,mysqlhost2):
    db = mysql.connector.Connect(host=mysqlhost1, user=mysqluser,password=mysqlpwd,database="loadbalancing")
    cursor = db.cursor()
    cursor.execute("select created, event_description from node_event where event_description not like %s and loadbalancer_id = %s", tuple(["%status changed%",lbid]))

    resultset = head

    if cursor.rowcount != 0:
        for lb_id, event in cursor:
            resultset = resultset + "<tr>" + "<td>" + str(lb_id) + "</td>" + "<td>" + str(event) + "</td>" + "</tr>"
    else:
         resultset = "No data"

    cursor.close()
    db.close()

    resultset = '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd" colspan="3">Back-end Nodes Events</th></tr><tr><TD class=sideboxtext>Date</TD><TD class=sideboxtext>Event Description</TD>''' + resultset + "</table></center>"

    return resultset


def getGraphiteBandwidth(lbid,dc,mysqlhost1,mysqlhost2):
    CARBON_SERVER = '10.13.65.161'
    CARBON_PORT = 2003

    sock = socket()
    sock.connect((CARBON_SERVER, CARBON_PORT))

    # Get the LB IP address

    db = mysql.connector.Connect(host=mysqlhost1, user=mysqluser,password=mysqlpwd,database="loadbalancing")
    cursor = db.cursor()
    cursor.execute("select ip_address from virtual_ip_ipv4 where id = (select virtualip_id from loadbalancer_virtualip where loadbalancer_id = %s limit 1);", tuple([lbid]))

    if cursor.rowcount != 0:
        for ip_address in cursor:
            lb_ip = str(ip_address[0])
    else:
        lb_ip = "No data"

    cursor.close()
    db.close()

    # Fetch bytes in and bytes out for the givven IP and send to graphite

    db = mysql.connector.Connect(host=mysqlhost2, user=mysqluser,password=mysqlpwd,database="traffic_counter")
    cursor = db.cursor()

    cursor.execute("SELECT period, bytes FROM traffic WHERE ip = %s AND flow = 'INPUT' AND period > ( NOW() - INTERVAL 1 WEEK)", tuple([lb_ip]))

    if cursor.rowcount != 0:
        for period, bytes in cursor:
            epochtime = str(int(time.mktime(time.strptime(str(period), '%Y-%m-%d %H:%M:%S'))))      # convert from 2012-08-03 00:00:06 to epoch
            bytescount = str(bytes)
            graphitedata = dc + ".prod." + str(lbid).strip() + ".in " + str(bytes) + " " + str(epochtime) + "\n"

            #print ('sending message:\n%s' % graphitedata)
            sock.sendall(graphitedata.encode())

    else:
         bytesin = "No data"

    cursor.execute("SELECT period, bytes FROM traffic WHERE ip = %s AND flow = 'OUTPUT' AND period > ( NOW() - INTERVAL 1 WEEK)", tuple([lb_ip]))

    if cursor.rowcount != 0:
        for period, bytes in cursor:
            epochtime = str(int(time.mktime(time.strptime(str(period), '%Y-%m-%d %H:%M:%S'))))
            bytescount = str(bytes)
            graphitedata = dc + ".prod." + str(lbid).strip() + ".out " + str(bytes) + " " + str(epochtime) + "\n"

            #print ('sending message:\n%s' % graphitedata)
            sock.sendall(graphitedata.encode())

    else:
         bytesout = "No data"

    cursor.close()
    db.close()

    sock.close()

    bytesin = '''<img src="http://graphite-n01.lbaas.rackspace.net/render?width=400&from=-5days&until=now&height=250&target=alias%28scale%28''' + dc + '''.prod.''' + str(lbid).strip() + '''.in%2C0.0011111111111111%29%2C%22BYTES%20IN%22%29&title=LB_''' + str(lbid) + '''&lineMode=connected&bgcolor=FFFFFF&fgcolor=000000&uniq=0.24366070086543334"/> '''

    bytesout = '''<img src="http://graphite-n01.lbaas.rackspace.net/render?width=400&from=-5days&until=now&height=250&target=alias%28scale%28''' + dc + '''.prod.''' + str(lbid).strip() + '''.out%2C0.0011111111111111%29%2C%22BYTES%20OUT%22%29&title=LB_''' + str(lbid) + '''&lineMode=connected&bgcolor=FFFFFF&fgcolor=000000&uniq=0.24366070086543334"/> '''

    resultset = head + '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd" colspan="2">Loadbalancer Bandwidth</th></tr><tr><TD class=sideboxtext>Incoming</TD><TD class=sideboxtext>Outgoing</TD><tr><td>''' + bytesin + "</td><td>" + bytesout + "</td></tr></table></center>"

    return resultset


def getSNMPData(lbid):
    snmpresult = ""
    timeouterror = "Timeout: No Response from " + trafficmanager + ":1161"
    snmpcommand="snmpwalk -M +./static -mAll -v1 -c public " + trafficmanager + ":1161 virtualserverCurrentConn.\\\"" + accountid + "_" + str(lbid).strip() + "\\\""
    p = subprocess.Popen(snmpcommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        snmpresult = line.decode("utf-8")

    print(snmpcommand)
    print(snmpresult)

    if len(snmpresult) != 0:
        if snmpresult.strip() != timeouterror:
            g32_re = re.compile(".*: ([0-9]+).*")
            virtualserverCurrentConn = g32_re.match(snmpresult).group(1)
        else:
            virtualserverCurrentConn = "No data"
    else:
        virtualserverCurrentConn = "No data"

    snmpcommand="snmpwalk -M +./static -mAll -v1 -c public " + trafficmanager + ":1161 virtualserverMaxConn.\\\"" + accountid + "_" + str(lbid).strip() + "\\\""
    p = subprocess.Popen(snmpcommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        snmpresult = line.decode("utf-8")

    if len(snmpresult) != 0:
        if snmpresult.strip() != timeouterror:
            g32_re = re.compile(".*: ([0-9]+).*")
            virtualserverMaxConn = g32_re.match(snmpresult).group(1)
        else:
            virtualserverMaxConn = "No data"
    else:
        virtualserverMaxConn = "No data"
    
    resultset = head
    resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Concurrent Connections</th><td>''' + str(virtualserverCurrentConn) + "</td></tr>"
    resultset = resultset + '''<tr><th vAlign="bottom" bgColor="#eeeffd">Max Connections</th><td>''' + str(virtualserverMaxConn) + "</td></tr>"

    resultset = '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd" colspan="3">Loadbalancer SNMP Information</th></tr><tr>''' + resultset + "</table></center>"

    return resultset


def validateLBID(lbid,mysqlhost1):
    db = mysql.connector.Connect(host=mysqlhost1, user=mysqluser,password=mysqlpwd,database="loadbalancing")
    cursor = db.cursor()
    cursor.execute("SELECT id FROM loadbalancer where id=%s and status != 'DELETED'", tuple([lbid]))

    if str(cursor.fetchone()) == 'None':
        cursor.close()
        db.close()
        return False
    else:
        cursor.close()
        db.close()
        return True


@route('/')
@view('index')
def index():
    lbidvalidated = request.query.lbid
    if not request.get_cookie("account", secret='some-secret-key'):
        print("Need to auth")
        redirect("/login")
    else:
        response.set_header('Validated', 'True')
        ip = request.get('REMOTE_ADDR')
        return dict(lbidvalidated=lbidvalidated)


@post('/')
def main_submit():
    if not request.get_cookie("account", secret='some-secret-key'):
        print("Need to auth")
        redirect("/login")
    else:
        lbid = request.forms.get('lbid')
        dc = request.forms.get('dc')

        print("Requesting information about LBID " + str(lbid) + " located in " + str(dc))

        if dc == "ord1":
            mysqlhost1 = "XXXX"
            mysqlhost2 = "XXXX"
        elif dc == "dfw1":
            mysqlhost1 = "XXXX"
            mysqlhost2 = "XXXX"
        else:
            mysqlhost1 = "XXXX"
            mysqlhost2 = "XXXX"

        if validateLBID(lbid,mysqlhost1):
            generalData = getGeneralData(lbid,dc,mysqlhost1,mysqlhost2)
            migratedData = getMigratedData(lbid,dc,mysqlhost1,mysqlhost2)
            lbEvents = getLBEvents(lbid,dc,mysqlhost1,mysqlhost2)
            graphiteBandwidth = getGraphiteBandwidth(lbid,dc,mysqlhost1,mysqlhost2)
            snmpData = getSNMPData(lbid)
            nodeDetails = getNodeDetails(lbid,mysqlhost1)
            nodeEvents = getNodeEvents(lbid,dc,mysqlhost1,mysqlhost2)

            resultset = head + '''<center><table cellSpacing="0" borderColorDark="white" cellPadding="3" borderColorLight="#a6a3de" border="1"><tr><th vAlign="bottom" bgColor="#eeeffd"><a href="/"><img src=static/CLB.png /></a><br>''' + "Informaion about Load Balancer " + str(lbid) + " in " + str(dc).upper() + '''</th></tr><tr><TD class=sideboxtext>''' + generalData + "<br>" + migratedData + "<br>" + lbEvents + "<br>" + graphiteBandwidth + "<br>" + snmpData + "<br>" + nodeDetails + "<br>" + nodeEvents + '''</td></tr><tr><th vAlign="bottom" bgColor="#eeeffd"><a href="/">Back</a></th></tr></table></center>'''

            return resultset
        else:
            print("LBID: " + str(lbid) + " does not exist in " + str(dc))
            redirect('/?lbid=unknown')


run(host='10.12.99.18', port=8080)

