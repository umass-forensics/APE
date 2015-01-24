__author__ = 'wallsr'

from twisted.python import log
from twisted.internet import defer

from ..BTProtocol import BTProtocol, BTServerProtocol, BTClientProtocol
from ..tools import sleep


class ChokeBase(BTProtocol):
    """
    Responds to all requests with a choke/unchoke
    """
    exp_args = None

    def __init__(self):
        BTProtocol.__init__(self)
        self.choke_interval = 0
        self.__choking__= False

        if self.exp_args and 'choke_interval' in self.exp_args:
            self.choke_interval = self.exp_args['choke_interval']
            log.msg('Info: using choke interval: %d' % self.choke_interval)

    @defer.inlineCallbacks
    def send_piece(self, index, begin, piece):
        """
        Never respond, just send a choke/unchoke. However, only send one choke at a time.
        """

        if self.__choking__:
            return

        self.__choking__ = True

        self.send_choke()

        if self.choke_interval:
            yield sleep(self.choke_interval)

        self.send_unchoke()

        self.__choking__ = False


class Choke(ChokeBase, BTClientProtocol):
    """
    """


class ChokeSvr(ChokeBase, BTServerProtocol):
    """
    """