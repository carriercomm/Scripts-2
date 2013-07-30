import logging
import DNS
import MySQLdb


class DNSManipulator(object):

    def __init__(self, data, glb_config, logger):
        self.data = data
        self.glb_config = glb_config
        self.logger = logger
        self.domain_name_offset = ''            # Will contain the offset (the end of) the domain name

    def get_domain_record(self):

        #    16b trans ID       16b Flags       16b Question      16b Answer RR     16b Authority    16b Additional    lenght      w        w        w     lenght
        # 11001000 10100101 00000001 00000000 00000000 00000001 00000000 00000000 00000000 00000000 00000000 00000000 00000011 01110111 01110111 01110111 00000110 
        #    d        e        e        k        o        n      lenght      c        o        m      end      Question Type    Question Class
        # 01100100 01100101 01100101 01101011 01101111 01101110 00000011 01100011 01101111 01101101 00000000 00000000 00000010 00000000 00000001

        #    C8     A5         01       00       00       01      00        00       00       00      00        00        03       77      77        77      06
        #    64     65         65       6B       6F       6E      03        63       6F       6D      00        00        02       00      01

        if self.glb_config.debug:
            data_hex = self.data.encode("hex")
            data_bin = ""
            for i in range(0,len(data_hex),2):
                data_bin += (bin(int(data_hex[i:i+2],16)))[2:].zfill(8)
        
            log_event = "Hex Data: " + data_hex
            self.logger.info(log_event)
            log_event =  "Binary Data: " + data_bin
            self.logger.info(log_event)

        dns_type1 = ord(self.data[-4:-3])       # Get the most  significant byte from the Question Type
        dns_type2 = ord(self.data[-3:-2])       # Get the least significant byte from the Question Type

        dns_type = str(dns_type1) + str(dns_type2)

        if dns_type == "01":
            record_type='A'
        elif dns_type == "015":
            record_type='MX'
        elif dns_type == "012":
            record_type='PTR'
        elif dns_type == "02":
            record_type='NS'
        elif dns_type == "10":
            record_type="TXT"
        elif dns_type == "05":
            record_type="CNAME"
        elif dns_type == "0255":
            record_type="ANY"
        else:
            record_type="A"

        dns_type_hex = self.data[-4:-2].encode("hex")

        if self.glb_config.debug:
            self.logger.info("Record Type: %s %s %s" % (dns_type, dns_type_hex, record_type))

        return record_type

    def get_domain_name(self):

        domain_name = ''

        type = (ord(self.data[2]) >> 3) & 15     # Get the Flags bits
        if type == 0:                            # If 0 then standart query
            ini = 12                             # Construct the domain name untill the end byte (0) is reached, starting at byte 12
            lon = ord(self.data[ini])
            while lon != 0:
                domain_name += self.data[ini+1:ini+lon+1]+'.'
                ini += lon + 1
                lon = ord(self.data[ini])
                self.domain_name_offset = ini
            if self.glb_config.debug:
                log_event = "Domain name offset = " + str(self.domain_name_offset)
                self.logger.info(log_event)

        return domain_name

    def query_auth_dns(self, domain_name, dns_type):

        # TODO: Pick a DNS server from a list of servers defined in the config file based on health check status

        log_event = "Quering DNS server " + str(self.glb_config.dns_backends[0]) + " for " + domain_name + " type " + dns_type
        self.logger.info(log_event)

        ip_list = []

        try:
            r = DNS.DnsRequest(domain_name, qtype=dns_type, server=self.glb_config.dns_backends[0], protocol='udp', timeout=300)
            res = r.req()
            res_list = res.answers

            for i in range(0, len(res_list)):
                if res_list[i]["typename"] == "A":
                    ip_list.append(res_list[i]["data"])

            log_event =  "DNS server returned " + str(ip_list)
            self.logger.info(log_event)
        except (DNS.Base.SocketError) as dns_error:
                self.logger.info("Cant connect to back-end DNS server - %s" % (dns_error))

        return ip_list
    
    def geo_ip_select(self, requestor, dns_resolved_list):

        #pr = subprocess.Popen(["/usr/bin/geoiplookup", requestor], shell=False, stdout=subprocess.PIPE)
        #requestor_location = pr.stdout.readlines()
        #
        #for i in range(0,len(dns_resolved_list)):
        #  pr = subprocess.Popen(["/usr/bin/geoiplookup", dns_resolved_list[i]], shell=False, stdout=subprocess.PIPE)
        #  output = pr.stdout.readlines()
        #  seleted_geo_loc = output[0]
        #  if output[0] == requestor_location[0]:
        #    selected_geo_ip = dns_resolved_list[i]
        #    break
        #  else:
        #    selected_geo_ip = dns_resolved_list[0]

        seleted_geo_loc = "Unknown"
        requestor_location = "Unknown"
        selected_geo_ip = "Nowhere"

        try:
            con = MySQLdb.connect(self.glb_config.geoip_store_host, self.glb_config.geoip_store_user, self.glb_config.geoip_store_pass, self.glb_config.geoip_store_db)
            cur = con.cursor(MySQLdb.cursors.DictCursor)
            statement = "select country_code from " + self.glb_config.geoip_store_table + " where INET_ATON('" + requestor + "') BETWEEN begin_ip_num AND end_ip_num"
            cur.execute(statement)
            rows = cur.fetchall()
            if len(rows) != 0:
                requestor_location = rows[0]['country_code']
            else:
                requestor_location = "Unknown"

            for i in range(0, len(dns_resolved_list)):
                statement = "select country_code from " + self.glb_config.geoip_store_table + " where INET_ATON('" + dns_resolved_list[i] + "') BETWEEN begin_ip_num AND end_ip_num"
                cur.execute(statement)
                rows = cur.fetchall()
                if len(rows) != 0:
                    seleted_geo_loc = rows[0]['country_code']
                    if seleted_geo_loc == requestor_location:
                        selected_geo_ip = dns_resolved_list[i]
                        break
                    else:
                        selected_geo_ip = dns_resolved_list[0]
                else:
                    selected_geo_ip = dns_resolved_list[0]

            cur.close()
            con.close()
        except (MySQLdb.OperationalError) as mysql_error:
            self.logger.info(mysql_error)

        log_event =  "Requestor " + requestor + " located at " + requestor_location
        self.logger.info(log_event)
        log_event =  "Sending to " + selected_geo_ip + " at " + seleted_geo_loc
        self.logger.info(log_event)
    
        return selected_geo_ip

    def response(self, ip):
        packet = ''
        packet += self.data[:2] + "\x81\x80"                             # 10000001 10000000    (response recursive) (can handle recursive queries)
        packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Questions and Answers Counts and Authority and Additional
        packet += self.data[12:self.domain_name_offset+5]                # Original Domain Name Question plus 2 bytes for Type and 2 bytes for Class
            
        packet += '\xc0\x0c'                                             # Pointer to domain name
        packet += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             # Response type (2 bytes x00 x01 A), class (2 bytes x00x01 IN), ttl (4 bytes x00x00x00x3c in seconds), data length (2 bytes x00x04)
        packet += str.join('',map(lambda x: chr(int(x)), ip.split('.'))) # 4bytes of IP

        # print "Reponse: " + packet.encode("hex")

        return packet
