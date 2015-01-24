__author__ = 'wallsr'

import struct
from twisted.internet import defer
from twisted.python import log

from ..BTProtocol import BTProtocol, BTServerProtocol, BTClientProtocol
from ..tools import sleep

#nsl_choke_careful_dos_svr


class FrameBase(BTProtocol):
    """
    Unchoke when we get all of the pieces.
    respond to requests with bad pieces,
    send choke/unchoke if the request is the first chunk of a piece
    """
    exp_args = None

    def __init__(self):
        BTProtocol.__init__(self)
        self.mutex = False
        self.preqs = {}
        self.send_list = []

        if self.exp_args and 'send_list' in self.exp_args:
            self.send_list = self.exp_args['send_list']
            log.msg('Info: using send list: %s' % str(self.send_list))

    @defer.inlineCallbacks
    def send_unchoke(self):
        """
        Wait until we get all of the pieces before we unchoke
        """
        #Make
        if self.mutex:
            return

        self.mutex = True

        while True:
            #Seems that sometimes btm hasn't been assigned when this is called.
            if hasattr(self, 'btm') and self.btm.pieceManager.bitfield.allOne():
                #unchoke them now that we have all of the pieces
                self.mutex = False
                BTProtocol.send_unchoke(self)
                break
            yield sleep(1)

    def send_piece(self, index, begin, piece):
        """
        """
        if begin not in self.send_list:
            self.send_choke()
            self.send_unchoke()
        #only send a piece once
        elif index in self.preqs and begin in self.preqs[index]:
            self.send_choke()
            self.send_unchoke()
        #send a bad piece
        else:
            log.msg('{0}, -bad_piece'.format(self.peer_id_str))

            log.msg('{0} Info: piece index {1},'
                    'begin {2}, length {3}'.format(
                    self.peer_id_str, index, begin, len(piece)))

            if index not in self.preqs:
                self.preqs[index] = []

            self.preqs[index].append(begin)

            #Always send bad data for a piece
            #pieces are of type string.
            bad_piece = 'a' * len(piece)

            data = struct.pack('!II', index, begin) + bad_piece
            self.send_message(self.msg_piece, data)


class Frame(FrameBase, BTClientProtocol):
    """
    """


class FrameSvr(FrameBase, BTServerProtocol):
    """
    """


class FrameBaseV2(FrameBase):
    """
    Same as FrameBase, but don't delay the unchoke.
    """
    def send_unchoke(self):
        BTProtocol.send_unchoke(self)


class FrameV2(FrameBaseV2, BTClientProtocol):
    """
    """


class FrameV2Svr(FrameBaseV2, BTServerProtocol):
    """
    """