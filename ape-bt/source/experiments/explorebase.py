'''
File:        atkbase.py
Author:      rjwalls
Description: Contains base attack classes that can be extended to create
    specific attack scenarios.

'''
from twisted.python import log
from twisted.internet import defer

from ..bitfield import Bitfield
from ..BTProtocol import BTProtocol
from .fsm import utilities
from .tools import sleep

import random
import struct
import time


class ExperimentBase(BTProtocol):
    '''
    This class overrides all send methods to be simple pass statements. This
    allows us to make sure that autonomo does not send any messages unless we
    want it to.

    '''

    def __init__(self):
        BTProtocol.__init__(self)

    def send_piece(self, index, begin, piece):
        pass

    def _send_piece(self):
        BTProtocol.send_piece(self, index, begin, piece)
        #log.msg('{0}, -bad_piece'.format(self.peer_id_str))

        #Always send bad data for a piece
        #pieces are of type string.
        #bad_piece = 'a' * 16384

        #data = struct.pack('!II', 0, 0) + bad_piece
        #self.send_message(self.msg_piece, data)

    def send_bitfield(self, bitfield):
        pass

    def _send_bitfield(self):
        BTProtocol.send_bitfield(self, self.bitfield)

#    def send_handshake(self):
#        print 'Info: Ignoring handshake method call!'
#        pass

    def _send_handshake(self):
        BTProtocol.send_handshake(self)

    def send_keep_alive(self):
        pass

    def _send_keep_alive(self):
        BTProtocol.send_keep_alive(self)

    def send_choke(self):
        pass

    def _send_choke(self):
        BTProtocol.send_choke(self)

    def send_unchoke(self):
        pass

    def _send_unchoke(self):
        BTProtocol.send_unchoke(self)

    def send_interested(self):
        pass

    def _send_interested(self):
        BTProtocol.send_interested(self)

    def send_not_interested(self):
        pass

    def _send_not_interested(self):
        BTProtocol.send_not_interested(self)

    def send_request(self, index, begin, length):
        pass

    def _send_request(self):
        BTProtocol.send_request(self, 0, 0, 16384)

    def send_cancel(self, idx, begin, length):
        pass

    def _send_cancel(self):
        BTProtocol.send_cancel(self, 0, 0, 16384)

    def send_port(self, port):
        pass

    def _send_port(self):
        BTProtocol.send_port(self, 6881)

    def send_have(self, index):
        pass

    def _send_have(self):
        BTProtocol.send_have(self, 0)


class EventExecute(ExperimentBase):
    '''
    This is a base class designed for attack scenarios where
    the user wants the tester to try and reach multiple different
    events.

    '''

    def __init__(self):
        ExperimentBase.__init__(self)

        # a dictionary, keyed by the event, pointing to the associated
        # model. allows us to use different models for different events.
        self._dest_event_models = {}
        self._requests = []

    def handle_data(self):
        '''
        Handle data received from the target.
        '''
        protocol = yield ord((yield 1))
        reserved = yield 8
        info_hash = yield 20
        peer_id = yield 20

        self.handle_handshake(protocol, reserved, info_hash, peer_id)

        self.postHandshake()

        self.finishHandshake()

        current_event = '+handshake'
        response = self._get_response(current_event)
        self._send_response(response)

        self._recv_events = []

        #This is an inlinecallback method /non-blocking
        self.handle_observed()

        while True:
            #Queue up receive events
            size, = struct.unpack('!I', (yield 4))
            if size == 0:
                self.handle_keep_alive()
            else:
                _type = yield 1
                self.cur_msg_type = _type

                data = yield (size - 1)

                event_string = self.msg_type[_type]

                self._recv_events.append({'type': event_string,
                                          'data': data,
                                          'time': time.time()})

                method_name = 'handle_' + self.msg_type[_type]
                method = getattr(self, method_name, None)
                if method:

                    if self.msg_type[_type] != 'bitfield':
                        log.msg('{0}, +{1}'.format(self.peer_id_str,
                                                   self.msg_type[_type]))
                    method(data)
                else:
                    raise NotImplementedError(method_name)

    @defer.inlineCallbacks
    def handle_observed(self):
        '''
        This method waits before allowing the tester to send any response
        messages. The idea is to allow all messages to be received before
        responding.

        '''

        while self.connected:
            if len(self._recv_events) == 0:
                yield sleep(0.1)
                continue

            tdiff = time.time() - self._recv_events[-1]['time']

            if tdiff < 0.1:
                yield sleep(0.1)
                continue

            current_events = []

            # TODO: Possible Race condition with the recv_events list
            for event in self._recv_events:
                if event["type"] == "bitfield":
                    bf = Bitfield(self.download.pieceManager.pieces_size, event["data"])

                    if bf.allOne():
                        event["type"] = "bitfield_all"
                    elif bf.allZero():
                        event["type"] = "bitfield_none"
                    else:
                        event["type"] = "bitfield_partial"

                current_events.append('+' + event["type"])

            #For now lets removed the unique requirement. This is needed to
            #make sure we respond to all piece requests.
            #current_events_uniq = list(set(current_events))
            #response = self._get_response(current_events_uniq)
            response = self._get_response(current_events)
            self._send_response(response)

            self._recv_events = []

    def _mix_response(self, responses):
        response_set = set()
        response_set_add = response_set.add
        return [x for x in responses if x not in response_set
                and not response_set_add(x)]

    def _get_response(self, obs_event):
        '''
        Figures out how to respond to the most recently observed events.

        Input can be a single event or a list of events.

        '''

        # if the input is a list of events then call this method for each
        # event individually.
        if isinstance(obs_event, list):
            responses = []
            for event in obs_event:
                responses += self._get_response(event)

            return responses
            #return self._mix_response(responses)

        # Our responses
        responses = []

        # Figure out the responses needed to reach each event
        for devent in self._dest_event_models:
            dmodel = self._dest_event_models[devent]

            #The True argument tell the algorithm to pick randomly among
            #all possible starting states, i.e. states with the same label
            #as the current_event
            devent_state, path = utilities.shortest_path_to_event(dmodel,
                                                                  devent,
                                                                  obs_event,
                                                                  True)
            responses_new = self._find_next_send(path, dmodel)

            if responses_new is None:
                log.msg('Info: Could not find a path from'\
                    '{0} to {1}'.format(obs_event, devent))
            else:
                responses = responses + responses_new

        # RJW: I commented this out because it will only allow us to
        # respond to a single request at a time.
        # Remove duplicated responses but preserve order
        #responses_uniq = self._mix_response(responses)

        log.msg('Info: Response to {0} should be {1}'.format(obs_event,
                                                           responses))

        return responses
        #return responses_uniq

    def _send_response(self, responses):
        '''
        Sends a message corresponding to each response event type.

        Expects responses as a list of send events.

        '''

        for response in responses:
            method_name = '_send_' + response.replace('-', '')
            method = getattr(self, method_name, None)

            if method:
                method()
            else:
                raise NotImplementedError(method_name)

    def _find_next_send(self, path, model):
        '''
        Returns the next sequence of contiguous send events. If not send events
        are found, it will return an empty list.

        '''
        send_events = []

        if path is None:
            return None

        for state in path:
            event = model._statelabels[state]

            if not event.startswith("+"):
                send_events.append(event)
            elif len(send_events) > 0:
                break

        return send_events


class EventExecuteExplore(EventExecute):
    '''
    Tries to find a path to the specified events, randomly forgetting to send
    some of the messages.

    '''

    def __init__(self):
        EventExecute.__init__(self)
        # If set to true, the explorer will occasionally send a random
        # response in addition to ignoring some responses.
        self.USE_RAND_RESPONSES = False
        self.EXPLORE_AFTER_GOAL = False
        self.SKIP_RESPONSES = False

        self._possible_send = ['handshake',
                               'cancel',
                               'port',
                               'request',
                               'piece',
                               #'piece_expected',
                               'piece_expected_bad',
                               #'piece_expected_half',
                               #'piece_unexpected',
                               #'piece_unexpected_bad',
                               'bitfield_partial',
                               'bitfield_none',
                               'bitfield_all',
                               #'bitfield',
                               'have',
                               'not_interested',
                               'interested',
                               'unchoke',
                               'choke',
                               'keep_alive']

        log.msg('Possible send events:')
        log.msg(self._possible_send)

        self._remaining_goals = self._dest_event_models.keys()
        self._requests=[]

#    def handle_bitfield(self, data):
#        self.download._bitfield(data)

    def handle_request(self, data):
        index, begin, length = struct.unpack('!III', data)
        log.msg( '{3}, Info: Request Index {0}, Begin {1}, Length {2}'.format(
            index, begin, length, self.peer_id_str))
        self._requests.append((index, (begin, length)))

    def _get_response(self, current_event):
        # Check if the current_event is one of our destination events.
        if current_event in self._remaining_goals:
            self._remaining_goals.remove(current_event)
            log.msg('Info: goal {0} reached.'.format(current_event))

        #Check if we are in exploration mode,i.e., all goals have been reached
        #at least once.
        if len(self._remaining_goals) == 0 and self.EXPLORE_AFTER_GOAL:
            responses = []
            #Send up to 3 random events
            for x in xrange(random.randint(1, 3)):
                responses.append(self._get_rand_sendevent())

            log.msg('Info: Random mode, sending {0} random messages.'.format(
                len(responses)))


            return responses
        else:
            return EventExecute._get_response(self, current_event)

    def _send_response(self, responses):

        for response in responses:
            # Skip the message with some probability
            if self.SKIP_RESPONSES and random.randint(0, 10) == 0:
                log.msg('Info: Skipping response event {0}'.format(response))
                continue

            # Replace the response with a random message with some probability
            if self.USE_RAND_RESPONSES and random.randint(0, 10) == 0:
                log.msg('Info: Replacing response event {0}'.format(response))
                response = self._get_rand_sendevent()

            method_name = '_send_' + response.replace('-', '')
            method = getattr(self, method_name, None)

            if method:
                method()
            else:
                raise NotImplementedError(method_name)

    def _get_rand_sendevent(self):
        '''
        Sends a random message...for fun!

        '''

        idx = random.randint(0, len(self._possible_send) - 1)

        return self._possible_send[idx]

    def _send_bitfield(self):
        '''
        I have to override this method to make sure the bitfield log message
        doesn't show up.

        '''

        BTProtocol.send_bitfield(self, self.bitfield)

    def _send_bitfield_all(self):
        #log.msg('{0}, -bitfield_all'.format(self.peer_id_str))

        for x in xrange(self.download.pieceManager.pieces_size):
            self.bitfield.set1(x)

        self._send_bitfield()

    def _send_bitfield_none(self):
        #log.msg('{0}, -bitfield_none'.format(self.peer_id_str))

        for x in xrange(self.download.pieceManager.pieces_size):
            self.bitfield.set0(x)

        self._send_bitfield()

    def _send_bitfield_partial(self):
        #Assuming that we are using the rand64k torrent
        # that only has two pieces. We want the bitfield to be
        # zero for the second piece
        #log.msg('{0}, -bitfield_partial'.format(self.peer_id_str))

        for x in xrange(self.download.pieceManager.pieces_size):

            if x < self.download.pieceManager.pieces_size / 2:
                self.bitfield.set1(x)
            else:
                self.bitfield.set0(x)

        self._send_bitfield()

    def _send_piece(self):
        '''
        Send one of the pieces that the client requested
        '''

        if len(self._requests) == 0:
            log.msg('{0}, info: no current piece requests, skipping send_piece'.format(
                self.peer_id_str))
            return

        #get the oldest requested piece
        idx, (begin, length) = self._requests[0]
        data = self.upload.pieceManager.getPieceData(idx, begin, length)
        del self._requests[0]
        log.msg('{0}, -piece'.format(self.peer_id_str))
        BTProtocol.send_piece(self, idx, begin, data)

    def _send_piece_expected_half(self):
        '''
        Send one of the pieces that the client requested
        '''

        if len(self._requests) == 0:
            log.msg('{0}, info: no current piece requests, skipping send_piece_expected_half'.format(
                self.peer_id_str))
            return

        #get the oldest requested piece
        idx, (begin, length) = self._requests[0]
        #only send the first half of the request
        data = self.upload.pieceManager.getPieceData(idx, begin, length/2)
        del self._requests[0]
        log.msg('{0}, -piece_expected_half'.format(self.peer_id_str))
        BTProtocol.send_piece(self, idx, begin, data)

    def _send_piece_expected_bad(self):
        '''
        Send the expected piece (by index and offset), but replace the data with
        all 'a's
        '''

        if len(self._requests) == 0:
            log.msg('{0}, info: no current piece requests, skipping send_piece_expected_bad'.format(
                self.peer_id_str))
            return

        #get the oldest requested piece
        idx, (begin, length) = self._requests[0]
        data = 'a' * length
        del self._requests[0]
        log.msg('{0}, -piece_expected_bad'.format(self.peer_id_str))
        BTProtocol.send_piece(self, idx, begin, data)

    def _send_piece_unexpected(self):
        '''
        Send one of the pieces that the client did not request
        '''

        possible = [(0, (0, 16384)),
                    (1, (0, 16384))]

        not_expected = [i for i in possible if i not in self._requests]

        if len(not_expected) == 0:
            log.msg('{0}, info: unable to find an unexpected piece, skipping send_piece_unexpected'.format(
                self.peer_id_str))
            return

        idx, (begin, length) = not_expected[0]
        data = self.upload.pieceManager.getPieceData(idx, begin, length)
        log.msg('{0}, -piece_unexpected'.format(self.peer_id_str))
        self._send_piece(idx, begin, data)

    def _send_piece_unexpected_bad(self):
        '''
        Send one of the pieces that the client did not request, with bad data
        '''

        possible = [(0, (0, 16384)),
                    (1, (0, 16384))]

        not_expected = [i for i in possible if i not in self._requests]

        if len(not_expected) == 0:
            log.msg('{0}, info: unable to find an unexpected piece, skipping send_piece_unexpected'.format(
                self.peer_id_str))
            return

        idx, (begin, length) = not_expected[0]
        data = 'a'*length
        log.msg('{0}, -piece_unexpected_bad'.format(self.peer_id_str))
        self._send_piece(idx, begin, data)


