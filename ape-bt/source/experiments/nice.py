__author__ = 'wallsr'


from twisted.internet import defer

from ..BTProtocol import BTProtocol, BTServerProtocol, BTClientProtocol
from ..tools import sleep


class DelayedStartBase(BTProtocol):
    """
    wait 30 seconds before unchoking the peer.
    """
    @defer.inlineCallbacks
    def send_unchoke(self):
        print 'Info: waiting to send unchoke'
        yield sleep(30)
        BTProtocol.send_unchoke(self)


class DelayedStartSvr(DelayedStartBase, BTServerProtocol):
    """
    """


class DelayedStart(DelayedStartBase, BTClientProtocol):
    """
    """


class NiceBase(BTProtocol):
    """
    This class does nothing different.
    """


class Nice(NiceBase, BTClientProtocol):
    """
    """


class NiceSvr(NiceBase, BTServerProtocol):
    """
    """