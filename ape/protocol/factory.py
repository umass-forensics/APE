__author__ = 'wallsr'

from twisted.internet import protocol


class ProtocolFactory(protocol.ClientFactory):
    def __init__(self, protocol_arg, args):
        self.args = args
        self.protocol_arg = protocol_arg

    def buildProtocol(self, addr):
        return self.protocol_arg(self, self.args)