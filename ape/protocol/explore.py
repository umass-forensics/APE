__author__ = 'wallsr'

import inspect
import random
import struct
import time

from ..fsm import utilities as utils
from threading import Lock
from tools import sleep
from twisted.internet import protocol
from twisted.python import log
from twisted.internet import defer


class ExploreProtocol(protocol.Protocol):
    '''
    Base class for performing exploration of a target implementation.
    This class is designed to be inherited, where the child class provides
    specific methods for the target implementation.

    '''
    def __init__(self, factory, args):
        #args should be a json dictionary.

        #pull in the model
        log.msg('Info: Using model %s' % args["model"])
        self.model = utils.dot_to_fsm(args["model"])

        #We want a small chance to ignore the destination and go
        #exploring instead.
        self.destination = utils.get_random_event(self.model, include_initial=True)

        if self.destination == "INITIAL":
            self.destination = None

        self.observed = ["INITIAL"]

        if self.destination is not None:
            log.msg('Info: Destination %s' % self.destination)

        #Get all possible send events, as defined by the methods named 'send_*'
        self.possible_send_events = [name.replace('send_', '-') for (name, method)
                                     in inspect.getmembers(self,
                                                           predicate=inspect.ismethod)
                                     if name.startswith('send_')]

        self.data = ''
        self.explore_cache = {}
        self.last_message_time = None

        self.SKIP_RESPONSES = True
        self.USE_RANDOM_RESPONSE = True

        self._mutex_data_incoming = Lock()
        self._mutex_event = Lock()

    def get_message_type(self, message):
        """
        This method should be overridden by the child class
        """
        raise Exception('Child class did override this method.')

    def connectionMade(self):
        print 'Connection made!'

        self.start()

        self._handle_data = self.handle_data()
        self._next_length = self._handle_data.next()

    def start(self):
        """
        Start the exploration.
        We may want to start by sending some messages.
        """
        send_events = []

        if self.destination is None:
            send_events = self.get_explore_event()
        else:
            #The model might tell us we
            #need to start by sending messages to the target
            send_events_model = self.get_response()


            if send_events_model:
                send_events = send_events_model
            else:
                send_events = self.get_random_send_events()

        self.transmit_events(send_events)

    #@defer.inlineCallbacks
    def transmit_events(self, send_events):
        log.msg('Info: Sending %d response events' % len(send_events))
        for event in send_events:
            # Skip the message with some probability
            if self.SKIP_RESPONSES and random.randint(0, 10) == 0:
                log.msg('Info: Skipping response event {0}'.format(event))
                continue

            # Replace the response with a random message with some probability
            if self.USE_RANDOM_RESPONSE and random.randint(0, 10) == 0:
                log.msg('Info: Replacing response event {0}'.format(event))
                event = self.get_random_send_events()[0]

            #yield sleep(0.5)
            #now = time.time()
            ##We sleep half a second, make sure we didn't receive a message in that
            ##time frame. if so, we skip our response
            #if self.last_message_time is not None and now - self.last_message_time < 0.5:
            #    return

            #Assume that all send events have an associated method of the name
            #'send_EVENTNAME'.
            method_name = 'send_' + event.replace('-', '')
            method = getattr(self, method_name, None)

            if method:
                log.msg('%s' % event)
                method()
            else:
                raise NotImplementedError(method_name)

    def dataReceived(self, data):
        """
        This method is called whenever we receive data
        from the remote client.
        """
        self._mutex_data_incoming.acquire()

        #Let's record the last time we received any data
        self.last_message_time = time.time()

        #Add the data we just received to the data
        #we received previously, but have yet to
        #process.
        data = self.data + data

        # This loop works in concert with the handle_data
        # method. We ask the method what amount of data
        # it is expecting, and then send that amount as
        # soon as we have it.
        # For example, handle_data first asks for 4 bytes, which
        # it then interprets as an int representing
        # the size of the payload. handle_data will then ask
        # for data equal to the payload size.
        next_length = self._next_length
        while len(data) >= next_length:
            data_send, data = data[:next_length], data[next_length:]
            next_length = self._handle_data.send(data_send)

        self.data = data
        self._next_length = next_length

        self._mutex_data_incoming.release()

    def handle_data(self):
        while True:
            size, = struct.unpack('!I', (yield 4))
            received_event = self.get_message_type((yield size))
            self.handle_received_event(received_event)

    @defer.inlineCallbacks
    def handle_received_event(self, received_event):
        log.msg('+%s' % received_event)

        #We have to remove that extra data we may have appended.
        received_event = received_event.split('__')[0]

        self.observed.append('+'+received_event)
        #Only keep track of the last 100 events
        self.observed = self.observed[-100:]

        # Check if we already have a handle_received_event
        # method running. If so, let it handle the rest.
        if not self._mutex_event.acquire(False):
            return

        #Wait for us to get all of the data
        while not self._mutex_data_incoming.acquire(False):
            yield sleep(0.01)

        if self.observed[-1] == self.destination:
            log.msg('Info: Destination %s reached' % self.destination)
            self.destination = None

        if self.destination:
            send_events = self.get_response()
            if not send_events:
                send_events = self.get_random_send_events()
        else:
            send_events = self.get_explore_event()

        self.transmit_events(send_events)

        self._mutex_data_incoming.release()
        self._mutex_event.release()


    def get_response(self):
        """
        Figures out what messages the tester should send based on the
        sequence of events observed since the last sent message.

        If we can't find a path in the model from any of the observed observed
        events to the destination, then this method returns None. Note, this is
        different then returning an empty list which may occur if we have a path
        to the destination, but it doesn't contain any send events.
        """
        if self.destination is None:
            log.msg('Info: No current destination.')
            return None

        # Our responses
        send_events = []

        #Guess our current state based on the past 5 events:
        #if that doesn't work use past 4, and so on
        x = 5
        while x > 0:
            current_state_guesses = utils.guess_current_state(self.model, self.observed[-x:])

            if len(current_state_guesses) > 0:
                break
            x -= 1

        #This would only happen if we have never seen the last event before
        if len(current_state_guesses) == 0:
            #we couldn't figure out where we are, switch to random mode.
            log.msg('Info: Unable to figure out current state.')
            return None

        csg_withpath = []

        #check if any of these guesses have a path to the destination
        for guess in current_state_guesses:
            guess_destination, guess_path = utils.shortest_path_to_event(
                self.model,
                self.destination,
                current_state=guess)

            if self.model:
                csg_withpath.append((guess, guess_destination))

        if len(csg_withpath) == 0:
            #We couldn't find a path from any of our guesses to the destination.
            log.msg('Info: None of our current state guesses has a path to the destination.')
            return None

        #Pick a random state from the current guesses.
        current_idx = random.randint(0, len(csg_withpath) - 1)

        current, destination = csg_withpath[current_idx]

        all_paths_raw = utils.all_simple_paths(self.model,
                                               current,
                                               destination,
                                               include_start=False
                                               )



            #The 'True' argument tells the algorithm to pick randomly among
            #all possible starting states, i.e. states with the same label
            #as the current_event
            #dest_state, path = utils.shortest_path_to_event(self.model,
            #                                                self.destination,
            #                                                observed,
            #                                                random_start=True)



        if not all_paths_raw:
            log.msg('Info: Could not find a path'
                    ' from %s to %s' % (current, self.destination))

            return None
        else:
            path_idx = random.randint(0, len(all_paths_raw) - 1)
            path = all_paths_raw[path_idx]

            #Extract the first sequence of contiguous send events,
            #if the path doesn't contain a send event, then we
            #return an empty list
            for state in path:
                event = self.model._statelabels[state]

                #Stop when we hit an expected receive event.
                if not event.startswith("+"):
                    #Anything after the double underscore is related to
                    #the fuzzing properties and should not be considered here
                    send_events.append(event.split('__')[0])
                #Check if this receive event occurs after a send
                #in our path
                elif len(send_events) > 0:
                    break

            log.msg('Info: Response to %s should be %s' % (self.observed[-1],
                                                           str(send_events)))
            #send_events_all.extend(send_events)

            return send_events

    def get_explore_event(self, depth=1):

        #Guess our current state based on the past 5 events:
        #current_state_guesses = utils.guess_current_state(self.model, self.observed[-5:])

        #Guess our current state based on the past 5 events:
        #if that doesn't work use past 4, and so on
        #TODO: test if this works
        x = 5
        while x > 0:
            current_state_guesses = utils.guess_current_state(self.model, self.observed[-x:])

            if len(current_state_guesses) > 0:
                break
            x -= 1

        #We can't figure out where we are, so just go random.
        if len(current_state_guesses) == 0:
            return self.get_random_send_events(num=depth)

        send_set = set(self.possible_send_events)

        #We have an idea where we are, so we need to explore smartly
        for state in current_state_guesses:
            if state not in self.explore_cache:
                nexthop = utils.get_nexthop_eventset(self.model, state)
                #We only want send events
                nexthop = [event for event in nexthop if event.startswith('-')]
                self.explore_cache[state] = set(nexthop)

        #pick the state with the fewest events
        picked_key = sorted(self.explore_cache,
                            key=lambda x: len(self.explore_cache[x]))[0]

        #pick an event we haven't send from this state
        possible_sends = send_set - self.explore_cache[picked_key]

        #Check if we've already tried every send event.
        if len(possible_sends) == 0:
            return self.get_random_send_events(num=depth)

        first_send = self.get_random_send_events(possible_sends=list(possible_sends))

        #Add it to our set so in the next go around we pick a different  value
        self.explore_cache[picked_key].update(first_send)

        #Just send one value and see what happens.
        return first_send

    def get_random_send_events(self, num=1, possible_sends=None):
        """
        Grab one or more random send events.
        """
        if not possible_sends:
            possible_sends = self.possible_send_events

        events = []

        for x in xrange(num):
            idx = random.randint(0, len(possible_sends)-1)
            events.append(possible_sends[idx])

        return events




