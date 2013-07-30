import multiprocessing
import socket
import sys
import logging
from daemon import runner
import os

import geo_conf_parser
import geo_dns_worker
import geo_mon

CONFIG_FILE = "/etc/geolb.conf"
PID_FILE = "/var/run/geolb.pid"
LOG_FILE = "/var/log/geolb.log"


class MainApp(object):

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  PID_FILE
        self.pidfile_timeout = 5

    def dns_processor(self, data, addr, sock):
        p = multiprocessing.current_process()

        logger.info("Staring: %s %s " % (p.name, p.pid))

        dns_data = geo_dns_worker.DNSManipulator(data, glb_config, logger)      # Initialize the DNSManipulator object

        domain_name = dns_data.get_domain_name()                                # Extract the requested domain name from the DNS UDP packet
        if domain_name != "":
            dns_type = dns_data.get_domain_record()                                 # Extract the type of record requested for the domain name
            domain_ips = dns_data.query_auth_dns(domain_name, dns_type)             # Get the list of A records from the BIND back-ends for the requested domain name and record type

            # TODO: Get the algorithm for the requested domain name

            if len(domain_ips) > 0:
                ip = dns_data.geo_ip_select(addr[0], domain_ips)            # Select an A record based on the requestor's country of origin
                sock.sendto(dns_data.response(ip), addr)                    # Send a reply back with the selected A record to the requestor
        else:
            logger.info("Invalid Request, discarding!")

        logger.info("Terminating: %s %s " % (p.name, p.pid))
        sys.stdout.flush()

    def run(self):
        logger.info("Global Loadbalancing Proxy serving at %s:%s" % (glb_config.udp_ip, glb_config.udp_port))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)         # Create UDP socket
        sock.bind((glb_config.udp_ip, glb_config.udp_port))

        glb_mon_object = geo_mon.Healthcheck(glb_config, logger)                                        # Initialize the monitoring object
        glb_mon_p = multiprocessing.Process(target=glb_mon_object.check_customer_nodes)                 # Spawn a new child processes for monitoring
        glb_mon_p.daemon = True
        glb_mon_p.start()

        for i in range(glb_config.workers_dns):                         # Prefork child processes to do all the work
            pid = os.fork()

            if pid == 0:                                                # Inside the child process
                childpid = os.getpid()
                logger.info("Child %s listening on %s:%s" % (childpid, glb_config.udp_ip, glb_config.udp_port))
                try:
                    while True:
                        data, addr = sock.recvfrom(1024)                # Received a UDP packet
                        self.dns_processor(data, addr, sock)
                        if os.getppid() == 1:
                            logger.info("Parent died, exiting ...")
                            sys.exit()
                except KeyboardInterrupt:
                    sys.exit()

        try:
            os.waitpid(-1, 0)
        except KeyboardInterrupt:
            print "\nbailing"
            sys.exit()


if __name__ == "__main__":
    glb_config = geo_conf_parser.ParseConfig(CONFIG_FILE)               # Parse the json config file

    main_app = MainApp()

    logger = logging.getLogger("Geo Loadbalancer")                      # Start logging
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    daemon_runner = runner.DaemonRunner(main_app)                       # Daemonize the application
    daemon_runner.daemon_context.files_preserve=[handler.stream]
    daemon_runner.do_action()

