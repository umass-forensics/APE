'''
File:        find_cycles.py
Author:      rjwalls
Description: Finds all(?) cycles in the given model. Cycles may be listed
multiple times.

'''

from fsm import utilities
import sys

dot_file = sys.argv[1]

model = utilities.dot_to_fsm(dot_file)

paths = []

for state in model._states:
    # Only consider cycles starting at a non-send event
    #event = model._statelabels[state]
    #if event.startswith('-'):
    #    continue

    path = utilities.shortest_path(model, state, state, True, True)

    if path is not None and len(path) > 0:
        print utilities.get_path_eventstr(model, path)
        # A cycle will show up once for each state in the cycle.
        # We need a way to check that two cycles are really the same
        # cycle just one happened to start in a different place.
