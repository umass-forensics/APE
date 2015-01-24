'''
File:        find_paths.py
Author:      rjwalls
Description: Given a sequence of events, finds a number of shortest paths
including all of those events.

Returns a path, if it exists for every possible mapping of the input event
sequence to states.
'''

from fsm import utilities
import sys
import itertools

dotfile = sys.argv[1]
eventstr = sys.argv[2]

model = utilities.dot_to_fsm(dotfile)

#The event string should be a comma-separated list,
#split on the comma and remove the whitespace.
events = [x.strip() for x in eventstr.split(',')]

#Each event might be associated with many states
event_states = {}
#Find all states for each event label
for event in list(set(events)):
    event_states[event] = utilities.states_by_event(model, event, startswith=True)

#Map the event list to all possible states for each
#of the events, in order
event_states_ordered = [event_states[x] for x in events]

#Cartesian product! Result is a list of all partially ordered state paths.
partial_paths = [x for x in itertools.product(*event_states_ordered)]

paths = []

for partial in partial_paths:
    path = []

    #make sure there is actually a path between every pair in the partial path
    for x in xrange(len(partial) - 1):
        # if this is the first pair then we include the start of the path
        pairpath = utilities.shortest_path(model, partial[x], partial[x + 1],
                                           True, x == 0)

        if pairpath is None or len(pairpath) == 0:
            break

        path.extend(pairpath)
    else:
        # All pairs have a path, i.e., the loop didn't break
        paths.append(path)
        continue

for path in paths:
    print utilities.get_path_eventstr(model, path)
