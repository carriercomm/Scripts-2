import json


class ParseConfig(object):

    def __init__(self, config_file):
        self.config_file = config_file

        try:
            with open(self.config_file, mode="r", ) as fh:
                glb_conf = json.load(fh)

            self.debug = glb_conf["properties"]["debug_mode"]
            self.udp_ip = str(glb_conf["properties"]["listening_ip"])
            self.udp_port = int(glb_conf["properties"]["listening_port"])
            self.workers_dns = glb_conf["properties"]["workers_dns"]
            self.workers_mon = glb_conf["properties"]["workers_mon"]

            self.geoip_store_host = str(glb_conf['geoip_store']['host'])
            self.geoip_store_user = str(glb_conf['geoip_store']['user'])
            self.geoip_store_pass = str(glb_conf['geoip_store']['password'])
            self.geoip_store_port = int(glb_conf['geoip_store']['port'])
            self.geoip_store_type = str(glb_conf['geoip_store']['type'])
            self.geoip_store_db = str(glb_conf['geoip_store']['database'])
            self.geoip_store_table = str(glb_conf['geoip_store']['geoiptable'])

            self.dns_backends = []
            for i in xrange(0, len(glb_conf['dns_backends'])):
                self.dns_backends.append(str(glb_conf['dns_backends'][i]['ip']))

            self.dns_backends_host = str(glb_conf['dns_backends_store']['host'])
            self.dns_backends_user = str(glb_conf['dns_backends_store']['user'])
            self.dns_backends_pass = str(glb_conf['dns_backends_store']['password'])
            self.dns_backends_port = int(glb_conf['dns_backends_store']['port'])
            self.dns_backends_type = str(glb_conf['dns_backends_store']['type'])
            self.dns_backends_db = str(glb_conf['dns_backends_store']['database'])
            self.dns_backends_zone_table = str(glb_conf['dns_backends_store']['zonetable'])

            self.accounts_store_host = str(glb_conf['accounts_store']['host'])
            self.accounts_store_user = str(glb_conf['accounts_store']['user'])
            self.accounts_store_pass = str(glb_conf['accounts_store']['password'])
            self.accounts_store_port = int(glb_conf['accounts_store']['port'])
            self.accounts_store_type = str(glb_conf['accounts_store']['type'])
            self.accounts_store_db = str(glb_conf['accounts_store']['database'])
            self.accounts_store_domains_table = str(glb_conf['accounts_store']['domainstable'])
            self.accounts_store_dns_records_talbe = str(glb_conf['accounts_store']['dnsrecordstalbe'])

            self.memcached_host = str(glb_conf['memcached_server']['host'])
            self.memcached_port = int(glb_conf['memcached_server']['port'])

        except IOError:
            print "Configuration file %s not found.\nExiting ..." % (config_file)
            exit()
