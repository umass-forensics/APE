__author__ = 'wallsr'

import struct

from datetime import datetime

from twisted.python import log
from twisted.internet import defer, reactor

from ..BTProtocol import BTProtocol, BTServerProtocol, BTClientProtocol
from ..tools import sleep


class NoResponseBase(BTProtocol):
    """
    Does not respond to any piece requests.
    """

    def send_piece(self, index, begin, piece):
        """
        Never respond, and be silent about it
        """

        log.msg('Info: Ignoring request.')
        return


class NoResponse(NoResponseBase, BTClientProtocol):
    """
    """


class NoResponseSvr(NoResponseBase, BTServerProtocol):
    """
    """


class BadPiecesBase(BTProtocol):
    """
    Respond to every request with bad data
    """

    def send_piece(self, index, begin, piece):
        log.msg('{0}, -bad_piece'.format(self.peer_id_str))

        bad_piece = 'a' * len(piece)

        data = struct.pack('!II', index, begin) + bad_piece
        self.send_message(self.msg_piece, data)


class BadPieces(BadPiecesBase, BTClientProtocol):
    """
    """


class BadPiecesSvr(BadPiecesBase, BTServerProtocol):
    """
    """


class TimeoutBase(BTProtocol):
    """
    Class will close the application if we have communicated with
    the remote peer in a while. This is useful for exploration
    """

    timeout = 5
    #Static across all connections
    Last_Message = None

    def __init__(self):
        BTProtocol.__init__(self)
        self.check_time()

    def dataReceived(self, data):
        Timeout.Last_Message = datetime.now()
        BTProtocol.dataReceived(self, data)

    @defer.inlineCallbacks
    def check_time(self):
        while True:
            #break out of the loop when the timeout expires
            if Timeout.Last_Message is not None and \
               (datetime.now() - Timeout.Last_Message).seconds > self.timeout:
                break

            yield sleep(1)

        log.msg('{0}, Info: Timeout reached. Disconnecting.'.format(self.peer_id_str))

        self.exit()

    def exit(self):
        reactor.callFromThread(reactor.stop)


class Timeout(TimeoutBase, BTClientProtocol):
    """
    """


class TimeoutSvr(TimeoutBase, BTServerProtocol):
    """
    """