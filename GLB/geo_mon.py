import Queue
import threading
import time
import MySQLdb
import httplib
import socket


class ThreadHealthCheck(threading.Thread):

    def __init__(self, queue, logger, glb_config):
        threading.Thread.__init__(self)
        self.queue = queue
        self.logger = logger
        self.glb_config = glb_config

    def remove_node(self, node):
        # Mark the node as OFFLINE
        try:
            con = MySQLdb.connect(self.glb_config.accounts_store_host, self.glb_config.accounts_store_user, self.glb_config.accounts_store_pass, self.glb_config.accounts_store_db)
            cur = con.cursor(MySQLdb.cursors.DictCursor)
            statement = "UPDATE " + self.glb_config.accounts_store_dns_records_talbe + " SET status = 'OFFLINE' WHERE ip = '" + node['ip'] + "' AND port = " + str(node['port']).strip('L') + " AND domain_id = (SELECT id FROM " + self.glb_config.accounts_store_domains_table + " WHERE cname = '" + node['cname'] + "')"
            cur.execute(statement)
            cur.close()
            con.close()
        except (MySQLdb.OperationalError) as mysql_error:
            self.logger.error(mysql_error)

        # Remove the node from the BIND zone table
        try:
            con = MySQLdb.connect(self.glb_config.dns_backends_host, self.glb_config.dns_backends_user, self.glb_config.dns_backends_pass, self.glb_config.dns_backends_db)
            cur = con.cursor(MySQLdb.cursors.DictCursor)
            statement = "DELETE FROM " + self.glb_config.dns_backends_zone_table + " WHERE name = '" + node['cname'] + "' AND rdata = '" + node['ip'] + "'"
            cur.execute(statement)
            cur.close()
            con.close()
        except (MySQLdb.OperationalError) as mysql_error:
            self.logger.error(mysql_error)

    def add_node(self, node):
        # Mark the node as ONLINE
        try:
            con = MySQLdb.connect(self.glb_config.accounts_store_host, self.glb_config.accounts_store_user, self.glb_config.accounts_store_pass, self.glb_config.accounts_store_db)
            cur = con.cursor(MySQLdb.cursors.DictCursor)
            statement = "UPDATE " + self.glb_config.accounts_store_dns_records_talbe + " SET status = 'ONLINE' WHERE ip = '" + node['ip'] + "' AND port = " + str(node['port']).strip('L') + " AND domain_id = (SELECT id FROM " + self.glb_config.accounts_store_domains_table + " WHERE cname = '" + node['cname'] + "')"
            cur.execute(statement)
            cur.close()
            con.close()
        except (MySQLdb.OperationalError) as mysql_error:
            self.logger.error(mysql_error)

        # Add the node to the BIND zone table
        try:
            con = MySQLdb.connect(self.glb_config.dns_backends_host, self.glb_config.dns_backends_user, self.glb_config.dns_backends_pass, self.glb_config.dns_backends_db)
            cur = con.cursor(MySQLdb.cursors.DictCursor)
            statement = "INSERT INTO " + self.glb_config.dns_backends_zone_table + " VALUES ('" + node['cname'] + "', 259200, '" + node['type'] + "', '" + node['ip'] + "')"
            cur.execute(statement)
            cur.close()
            con.close()
        except (MySQLdb.OperationalError) as mysql_error:
            self.logger.error(mysql_error)

    def run(self):
        while True:
            node = self.queue.get()
            node_ip = node['ip']
            node_port = int(str(node['port']).strip('L'))
            node_timeout = int(str(node['timeout']).strip('L'))
            node_cname = node['cname']
            node_status = node['status']

            if node['health_check'] == "HTTP":
                # HTTP health check
                try:
                    http_conn = httplib.HTTPConnection(node_ip, port=node_port, timeout=node_timeout)
                    http_conn.request("GET", "/")
                    http_response = http_conn.getresponse()

                    if http_response.status >= 500:
                        if node_status != "OFFLINE":                                            # Already marked as failed, no need to do it again
                            self.logger.error("Health check - HTTP - FAIL for node %s for customer %s with error '%s'" % (node_ip, node_cname, http_response.status))
                            self.remove_node(node)                                              # Mark the node as OFFLINE and remove from BIND zone table.
                    else:
                        if node_status == "OFFLINE":
                            self.logger.info("Health check - HTTP - PASS for node %s for customer %s" % (node_ip, node_cname))
                            self.add_node(node)
                except (httplib.HTTPException, socket.error) as http_exception:
                    if node_status != "OFFLINE":
                        self.logger.error("Health check - HTTP - FAIL for node %s for customer %s with '%s'" % (node_ip, node_cname, http_exception))
                        self.remove_node(node)
            elif node['health_check'] == "TCP":
                # TCP health check
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((node_ip, node_port))
                    if node_status == "OFFLINE":
                        self.logger.info("Health check - TCP - PASS for node %s for customer %s" % (node_ip, node_cname))
                        self.add_node(node)
                except (socket.error) as socket_error:
                    if node_status != "OFFLINE":
                        self.logger.error("Health check - TCP - FAIL for node %s for customer %s with '%s'" % (node_ip, node_cname, socket_error))
                        self.remove_node(node)

            self.queue.task_done()


class Healthcheck(object):

    def __init__(self, glb_config, logger):
        self.glb_config = glb_config
        self.logger = logger

    def check_customer_nodes(self):

        queue = Queue.Queue()

        for i in range(self.glb_config.workers_mon):
            t = ThreadHealthCheck(queue, self.logger, self.glb_config)
            t.setDaemon(True)
            t.start()

        while True:
            try:
                con = MySQLdb.connect(self.glb_config.accounts_store_host, self.glb_config.accounts_store_user, self.glb_config.accounts_store_pass, self.glb_config.accounts_store_db)
                cur = con.cursor(MySQLdb.cursors.DictCursor)

                statement = "select domain_id, dns_records.ip, dns_records.port, dns_records.timeout, dns_records.type, domains.cname, domains.health_check, dns_records.status from " + self.glb_config.accounts_store_dns_records_talbe + " join domains on dns_records.domain_id = domains.id"
                cur.execute(statement)
                nodes_info = cur.fetchall()                             # Get all nodes and pass them to the worker threads through the queue

                for node in nodes_info:
                    queue.put(node)

                cur.close()
                con.close()
            except (MySQLdb.OperationalError) as mysql_error:
                self.logger.error(mysql_error)

            time.sleep(5)
