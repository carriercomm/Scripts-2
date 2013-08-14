import logging
import DNS
import MySQLdb
from random import choice
from pymemcache.client import *
import math
import datetime


class DNSManipulator(object):

    def __init__(self, data, glb_config, logger):
        self.data = data
        self.glb_config = glb_config
        self.logger = logger
        self.domain_name_offset = ''            # Will contain the offset (at the end of) the domain name

    def get_domain_record(self):

        #    16b trans ID       16b Flags       16b Question      16b Answer RR     16b Authority    16b Additional    lenght      w        w        w     lenght
        # 11001000 10100101 00000001 00000000 00000000 00000001 00000000 00000000 00000000 00000000 00000000 00000000 00000011 01110111 01110111 01110111 00000110
        #    d        e        e        k        o        n      lenght      c        o        m      end      Question Type    Question Class
        # 01100100 01100101 01100101 01101011 01101111 01101110 00000011 01100011 01101111 01101101 00000000 00000000 00000010 00000000 00000001

        #    C8     A5         01       00       00       01      00        00       00       00      00        00        03       77      77        77      06
        #    64     65         65       6B       6F       6E      03        63       6F       6D      00        00        02       00      01

        #if self.glb_config.debug:
        #    data_hex = self.data.encode("hex")
        #    data_bin = ""
        #    for i in range(0, len(data_hex), 2):
        #        data_bin += (bin(int(data_hex[i:i+2], 16)))[2:].zfill(8)

        #    log_event = "Hex Data: " + data_hex
        #    self.logger.info(log_event)
        #    log_event = "Binary Data: " + data_bin
        #    self.logger.info(log_event)

        dns_type1 = ord(self.data[-4:-3])      # Get the most  significant byte from the Question Type
        dns_type2 = ord(self.data[-3:-2])      # Get the least significant byte from the Question Type

        dns_type = str(dns_type1) + str(dns_type2)

        if dns_type == "01":
            record_type = 'A'
        elif dns_type == "015":
            record_type = 'MX'
        elif dns_type == "012":
            record_type = 'PTR'
        elif dns_type == "02":
            record_type = 'NS'
        elif dns_type == "10":
            record_type = "TXT"
        elif dns_type == "05":
            record_type = "CNAME"
        elif dns_type == "0255":
            record_type = "ANY"
        else:
            record_type = "A"

        dns_type_hex = self.data[-4:-2].encode("hex")

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

        return domain_name

    def query_auth_dns(self, domain_name, dns_type):

        # TODO: Pick a DNS server from a list of servers defined in the config file based on health check status

        if self.glb_config.debug:
            log_event = "Quering DNS server " + str(self.glb_config.dns_backends[0]) + " for " + domain_name + " type " + dns_type
            self.logger.debug(log_event)

        ip_list = []

        try:
            r = DNS.DnsRequest(domain_name, qtype=dns_type, server=self.glb_config.dns_backends[0], protocol='udp', timeout=300)
            res = r.req()
            res_list = res.answers

            for i in range(0, len(res_list)):
                if res_list[i]["typename"] == "A":
                    ip_list.append(res_list[i]["data"])

            if self.glb_config.debug:
                log_event = "DNS server returned " + str(ip_list)
                self.logger.debug(log_event)
        except (DNS.Base.SocketError) as dns_error:
                self.logger.error("Cant connect to back-end DNS server - %s" % (dns_error))

        return ip_list

    def geo_country_select(self, requestor, dns_resolved_list):                 # For the given list of A records, select the one that's closest to the requestors country
        seleted_geo_loc = "Unknown"
        requestor_location = "Unknown"
        selected_geo_ip = "Nowhere"

        try:
            memcache_client = Client((self.glb_config.memcached_host, self.glb_config.memcached_port))
            con = MySQLdb.connect(self.glb_config.geoip_store_host, self.glb_config.geoip_store_user, self.glb_config.geoip_store_pass, self.glb_config.geoip_store_db)
            cur = con.cursor(MySQLdb.cursors.DictCursor)

            requestor_key = "requestor_" + str(requestor)
            requestor_location  = memcache_client.get(requestor_key)                       # Check memcached for the requestors location, if not query the database and update the cache

            if requestor_location == None:
                if self.glb_config.debug:
                    log_event = "Requestor location not found in cache"
                    self.logger.debug(log_event)
                statement = "select country_code from " + self.glb_config.geoip_country + " where INET_ATON('" + requestor + "') BETWEEN begin_ip_num AND end_ip_num"
                cur.execute(statement)
                rows = cur.fetchall()
                if len(rows) != 0:
                    requestor_location = rows[0]['country_code']
                    memcache_client.set(requestor_key, requestor_location, 3 * 60)     # Cache the requestors location for 3 * 60 seconds
                else:
                    requestor_location = "Unknown"
            else:
                if self.glb_config.debug:
                    log_event = "Requestor location " + str(requestor_location) + " found in cache"
                    self.logger.debug(log_event)

            for i in range(0, len(dns_resolved_list)):
                a_record_key = "a_record_" + str(dns_resolved_list[i])
                selected_geo_loc = memcache_client.get(a_record_key)
                if selected_geo_loc == None:
                    if self.glb_config.debug:
                        log_event = str(a_record_key) + " not found in cache"
                        self.logger.debug(log_event)
                    continue
                elif selected_geo_loc == requestor_location:
                    if self.glb_config.debug:
                        log_event = str(a_record_key) + " found in cache and matches the requestor location"
                        self.logger.debug(log_event)
                    selected_geo_ip = dns_resolved_list[i]
                    break

            if self.glb_config.debug:
                        start_op = datetime.datetime.now()
            if selected_geo_ip == "Nowhere" or selected_geo_ip == None:
                for i in range(0, len(dns_resolved_list)):
                    statement = "select country_code from " + self.glb_config.geoip_country + " where INET_ATON('" + dns_resolved_list[i] + "') BETWEEN begin_ip_num AND end_ip_num"
                    cur.execute(statement)
                    rows = cur.fetchall()
                    if len(rows) != 0:
                        selected_geo_loc = rows[0]['country_code']
                        if selected_geo_loc == requestor_location:
                            selected_geo_ip = dns_resolved_list[i]
                            break
                        else:
                            selected_geo_ip = dns_resolved_list[0]
                    else:
                        selected_geo_ip = dns_resolved_list[0]
            if self.glb_config.debug:
                end_op = datetime.datetime.now()
                time_op = end_op - start_op
                log_event = "Total time to lookup all A records in the database: " + str(time_op.seconds) + " seconds and " + str(time_op.microseconds) + " microseconds"
                self.logger.debug(log_event)

                memcache_client.set("a_record_" + selected_geo_ip, selected_geo_loc, 3 * 60)     # Cache the A record location for 3 * 60 seconds

            cur.close()
            con.close()
            memcache_client.close()

        except (MemcacheUnexpectedCloseError, MySQLdb.OperationalError, socket.error) as conn_error:
            self.logger.error(conn_error)

        if self.glb_config.debug:
            log_event = "Requestor " + requestor + " located at " + requestor_location
            self.logger.debug(log_event)
            log_event = "Sending to " + selected_geo_ip + " at " + selected_geo_loc
            self.logger.debug(log_event)

        return selected_geo_ip

    def get_coordinates(self, ipaddress):
        coordinates = None
        if self.glb_config.debug:
            start_op = datetime.datetime.now()
        con = MySQLdb.connect(self.glb_config.geoip_store_host, self.glb_config.geoip_store_user, self.glb_config.geoip_store_pass, self.glb_config.geoip_store_db)
        cur = con.cursor(MySQLdb.cursors.DictCursor)

        statement = "select location_id from " + self.glb_config.geoip_city_blocks + " where INET_ATON('" + ipaddress + "') BETWEEN begin_ip_num AND end_ip_num"
        cur.execute(statement)
        rows = cur.fetchall()
        if len(rows) != 0:
            requestor_location_id = str(rows[0]['location_id']).rstrip('L')
            statement = "select latitude, longitude from " + self.glb_config.geoip_city_location  + " where location_id = " + requestor_location_id
            cur.execute(statement)
            rows = cur.fetchall()
            if len(rows) != 0:
                requestor_lon = rows[0]['longitude']
                requestor_lat = rows[0]['latitude']
                coordinates = rows[0]
                if self.glb_config.debug:
                    log_event = "Coordinates for " + str(ipaddress) + " " + str(requestor_lat) + ":" + str(requestor_lon)
                    self.logger.debug(log_event)
        else:
            if self.glb_config.debug:
                log_event = "Unknown coordinates for " + str(ipaddress)
                self.logger.debug(log_event)

        cur.close()
        con.close()

        if self.glb_config.debug:
            end_op = datetime.datetime.now()
            time_op = end_op - start_op
            log_event = "Total time to get coordinates for " + str(ipaddress) + ": " + str(time_op.seconds) + " seconds and " + str(time_op.microseconds) + " microseconds"
            self.logger.debug(log_event)

        return coordinates

    def get_distance(self, requestor_lon, requestor_lat, a_record_lon, a_record_lat):
        earth_radius = 3959

        dlat = math.radians(a_record_lat - requestor_lat)
        dlon = math.radians(a_record_lon - requestor_lon)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(requestor_lat)) * math.cos(math.radians(a_record_lat)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = earth_radius * c

        return distance

    def geo_city_select(self, requestor, dns_resolved_list):                 # For the given list of A records, select the one that's closest to the requestors city
        selected_geo_ip = "Nowhere"
        requestor_lon = 0
        requestor_lat = 0
        a_records_distance = {}

        if self.glb_config.debug:
            log_event = "Requestor: " + requestor
            self.logger.debug(log_event)

        requestor_coordinates = self.get_coordinates(requestor)
        if requestor_coordinates != None:
            requestor_lon = requestor_coordinates['longitude']
            requestor_lat = requestor_coordinates['latitude']

            for i in range(0, len(dns_resolved_list)):
                a_record_coordinates = self.get_coordinates(dns_resolved_list[i])
                if a_record_coordinates == None:
                    continue
                else:
                    a_record_lon = a_record_coordinates['longitude']
                    a_record_lat = a_record_coordinates['latitude']

                    # Calculate distance from the requestor to the A record and add to a dictionary that contains A records and the distances from the requstor
                    if self.glb_config.debug:
                        start_op = datetime.datetime.now()
                    a_records_distance[dns_resolved_list[i]] = self.get_distance(requestor_lon, requestor_lat, a_record_lon, a_record_lat)
                    if self.glb_config.debug:
                        end_op = datetime.datetime.now()
                        time_op = end_op - start_op
                        log_event = "Total time to calculate distance for " + str(dns_resolved_list[i]) + ": " + str(time_op.seconds) + " seconds and " + str(time_op.microseconds) + " microseconds"
                        self.logger.debug(log_event)
            if len(a_records_distance) > 0:
                if self.glb_config.debug:
                    log_event = "List of distances : " + str(a_records_distance)
                    self.logger.debug(log_event)
                selected_geo_ip = [key for (key,value) in a_records_distance.items() if value == sorted(a_records_distance.values())[0]][0]
                if self.glb_config.debug:
                    log_event = "Closest A record is: " + str(selected_geo_ip)
                    self.logger.debug(log_event)
        else:
            selected_geo_ip = dns_resolved_list[0]

        return selected_geo_ip

    def random_select(self, requestor, dns_resolved_list):                 # For the given list of A records, select one at random
        selected_random_ip = choice(dns_resolved_list)

        if self.glb_config.debug:
            log_event = "Requestor " + requestor
            self.logger.debug(log_event)
            log_event = "Sending to random server " + selected_random_ip
            self.logger.debug(log_event)

        return selected_random_ip

    def response(self, ip):
        packet = ''
        packet += self.data[:2] + "\x81\x80"                               # 10000001 10000000    (response recursive) (can handle recursive queries)
        packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'     # Questions and Answers Counts and Authority and Additional
        packet += self.data[12:self.domain_name_offset+5]                  # Original Domain Name Question plus 2 bytes for Type and 2 bytes for Class

        packet += '\xc0\x0c'                                               # Pointer to domain name
        packet += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'               # Response type (2 bytes x00 x01 A), class (2 bytes x00x01 IN), ttl (4 bytes x00x00x00x3c in seconds), data length (2 bytes x00x04)
        packet += str.join('', map(lambda x: chr(int(x)), ip.split('.')))  # 4bytes of IP

        # print "Reponse: " + packet.encode("hex")

        return packet
