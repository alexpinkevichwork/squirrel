import os
import time
import logging
import datetime
import requests
import subprocess

from mx_crm import settings

logger = logging.getLogger(__name__)


class Connector(object):
    """
    Connect to TMobile and change IP
    """

    ip = "213.61.109.114"
    google_host = "google.de"
    connection_name = 'T-Mobile'

    def ping_google(self):
        """
        Ping google and return ping status
        """
        logger.info("Trying to ping Google (%s)" % self.google_host)
        if os.name == 'nt':
            ret = subprocess.call("ping -n 10 -w 12000 %s" % self.google_host, shell=True, stderr=subprocess.STDOUT)
        else:
            ret = subprocess.call("ping -c 10 -w 12 %s" % self.google_host, shell=True, stderr=subprocess.STDOUT)

        return not ret

    def log_ip(self, agent_string):
        """
        Check the current IP Address
        and log it
        """
        ip = self.get_ip()
        print_string = '%s%s (%s)\n' % (ip, agent_string, datetime.datetime.now().strftime("%H:%M:%S"))
        logger.info(print_string)

    def get_ip(self):
        """
        Check the current IP Address
        """
        ip = requests.get('http://icanhazip.com/').content.strip()
        logger.info("Current IP: %s" % ip)
        return ip

    def _connect(self):
        if os.name == 'nt':
            logger.info("Open new connection")
            r = subprocess.call("rasdial %s" % self.connection_name)
            if r:
                logger.info('TRUBBLE HERE!!!!! CONNECT')
        else:
            logger.info('+'*50)
            logger.info('START NEW CONNECTION')
            logger.info('+' * 50)

    def connect(self, force=True):
        """
        Connect to T-Mobile and force disconnection at the start
        """
        if force:
            self.disconnect()
        try:
            current_ip = self.get_ip()
            if current_ip == self.ip:
                self._connect()
            else:
                self.disconnect()
                self._connect()
                logger.info("IP changed successfully")
        except Exception:
            logger.info("No Internet Connection, trying again")
            self.disconnect()
            self._connect()
        logger.info('Current IP: {}'.format(self.get_ip()))

    def disconnect(self):
        """
        Disconnect from T-Mobile
        """
        if os.name == 'nt':
            logger.info("Close connection")
            r = subprocess.call("rasdial %s /disconnect" % self.connection_name)
            if r:
                logger.info('TRUBBLE HERE!!!!! DISCONNECT')
        else:
            logger.info('+' * 50)
            logger.info('CLOSE CONNECTION')
            logger.info('+' * 50)


def reconnecting():
    if not settings.ENABLE_T_MOBILE:
        return

    connector = Connector()
    connector.connect()
    logger.info('Waiting 5 seconds for stable connection')
    time.sleep(5)


def disconnect():
    if not settings.ENABLE_T_MOBILE:
        return

    connector = Connector()
    connector.disconnect()


if __name__ == '__main__':
    connector = Connector()
