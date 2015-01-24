#
# -*-encoding:gb2312-*-

from twisted.internet import reactor

from bencode import bencode, bdecode, BTError

from twisted.python import log
from twisted.internet import defer
from twisted.web.client import HTTPClientFactory
from twisted.web import http
from urlparse import urlunparse

from tools import sleep

from urllib import urlencode
import hashlib
import socket
import struct


class BTTrackerClient (object):
    def __init__(self, btm):
        self.btm = btm
        self.reciever = btm.connectionManager.clientFactory
        self.timmer = {}
        self.interval = 15 * 60

    @defer.inlineCallbacks
    def start(self):
        self.status = 'started'

        info_hash = self.btm.metainfo.info_hash
        peer_id = self.btm.my_peer_id
        port = self.btm.app.btServer.listen_port
        #RJW: Not sure how to set the request here and what effect
        # it has on the propensity for peers to connect to this client.
        # Though, it seems like changing left from 100 to 0 is a good thing
        request = {
            'info_hash' : info_hash,
            'peer_id' : peer_id,
            'port' : port,
            #'port' : 6889,
            'compact' : 1,
            #'key' : 'abcd', # This is optional anyways
            'uploaded' : 0,
            'downloaded' :0,
            'left' : 0,
            'event' : 'started'
            }
        request_encode = urlencode(request)

        for url in self.btm.metainfo.announce_list :
            self.getPeerList(url, request_encode)
            yield sleep(1)

    def stop(self):
        self.status = 'stopped'

    @defer.inlineCallbacks
    def getPeerList(self, url, data):
        """TODO: This is in serious need of refactoring...
        """
        if self.status == 'stopped':
            return

        try:
            #page = yield getPage(url + '?' + data)
            if self.btm.app.bind_ip:
                bind = (self.btm.app.bind_ip, 0)
            else:
                bind = None

            # Connect to the tracker using our ip binding.
            page = yield getPageWithBind(url + '?' + data, bindAddr=bind)

        except Exception as error:
            log.err('Failed to connect to tracker: {0}'.format(url))

            yield sleep(self.interval)
            self.getPeerList(url, data)

        else:
            try:
                res = bdecode(page)
            except BTError:
                log.err("Received an invalid peer list from the tracker: " +\
                    "{0}".format(url))
            else:
                if len(res) == 1:
                    log.msg('Tracker: {0}'.format(res)) # TODO: What is this?
                    return

                peers = res['peers']
                peers_list = []
                try: # Try parsing in binary format first
                    while peers:
                        addr = socket.inet_ntoa(peers[:4])
                        port = struct.unpack('!H', peers[4:6])[0]
                        #RJW: We don't want to connect to ourselves
                        # This is a big hack that doesn't check to make
                        # sure the IP matches too.
                        if port != self.btm.app.btServer.listen_port:
                            peers_list.append((addr, port))
                        peers = peers[6:]
                except: # Now try parsing in dictionary format
                    try:
                        for p in peers:
                            peers_list.append((p["ip"], p["port"]))
                    except:
                        log.err("Received an invalid peer list from the " +\
                            "tracker: {0}".format(url))

                log.msg('RReceived {0} peers from tracker: {1}'.format(
                    len(peers_list), url))

                if len(peers_list) > 0:
                    log.msg(peers_list)
                    self.btm.add_peers(peers_list)
                    interval = res.get('interval', self.interval)
                    yield sleep(interval)
                    self.getPeerList(url, data)
                else:
                    import time
                    # RJW: Try again until we get peers! Especially since we
                    # know we just started one
                    log.msg("Trying again in 10 seconds")
                    time.sleep(10)
                    self.getPeerList(url, data)


def getPageWithBind(url, bindAddr=None, *args, **kwargs):
    '''
    Download a web page as a string, using the given bind address.

    '''
    scheme, host, port, path = _parse(url)
    factory = HTTPClientFactory(url, *args, **kwargs)

    reactor.connectTCP(host, port, factory, bindAddress=bindAddr)

    return factory.deferred


def _parse(url, defaultPort=None):
    """
    This method was extracted from twisted.web.test.test_webclient.

    Split the given URL into the scheme, host, port, and path.

    @type url: C{str}
    @param url: An URL to parse.

    @type defaultPort: C{int} or C{None}
    @param defaultPort: An alternate value to use as the port if the URL does
    not include one.

    @return: A four-tuple of the scheme, host, port, and path of the URL.  All
    of these are C{str} instances except for port, which is an C{int}.
    """
    url = url.strip()
    parsed = http.urlparse(url)
    scheme = parsed[0]
    path = urlunparse(('', '') + parsed[2:])

    if defaultPort is None:
        if scheme == 'https':
            defaultPort = 443
        else:
            defaultPort = 80

    host, port = parsed[1], defaultPort
    if ':' in host:
        host, port = host.split(':')
        try:
            port = int(port)
        except ValueError:
            port = defaultPort

    if path == '':
        path = '/'

    return scheme, host, port, path
