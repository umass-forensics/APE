'''
This module contains functions for working with finite state machines.



'''

from .baseclasses import BaseFSM
import copy
import itertools
import re
import sys
import random


def get_random_event(fsm, include_initial=False):
    '''
    Returns a random event from the model. Each event is equally likely.
    Excludes TERMINAL and send events.

    '''

    send_events = [x for x in fsm._statelabels.values() if x.startswith('-')]

    if include_initial:
        exclude_events = set(['TERMINAL'] + send_events)
    else:
        exclude_events = set(['TERMINAL', 'INITIAL'] + send_events)

    unique_events = list(set(fsm._statelabels.values()) - exclude_events)

    if len(unique_events) == 0:
        return None

    rand_idx = random.randint(0, len(unique_events) - 1)

    return unique_events[rand_idx]


def calculate_successrate_fsm(fsm, dest_event):
    '''
    Attempts to calculate the rate at which every node successfully reaches
    the destination event.

    '''

    # Get all possible goal states
    all_dest_states = states_by_event(fsm, dest_event)

    fsm._successrates = {}

    # You cannot succeed from the terminal state
    fsm._successrates[get_terminal(fsm)] = 0.0

    # Initialize the success rate for all goal states to be one
    for state in all_dest_states:
        fsm._successrates[state] = 1.0

    # Let's calculate the successrate for all states.
    # We want to keep track of which ones we have done so
    # we only call the calculate method (from the current method)
    # once for each state
    states_todo = []
    states_done = []

    states_todo.extend(fsm._edges_by_end[get_terminal(fsm)])

    while len(states_todo) > 0:
        state = states_todo.pop(0)
        __calculate_successrate_state(fsm, state)
        states_done.append(state)

        # Append all states that we havent done
        new_states = [x for x in fsm._edges_by_end[state] if
                      x not in states_done]

        states_todo.extend(new_states)


def __calculate_successrate_state(fsm, state):
    '''
    docstring for calculate_sucess_rate_state

    '''

    if fsm._successrates is None:
        raise Exception('Call calculate_success_rate_fsm first!')

    if state in fsm._successrates:
        return fsm._successrates[state]

    rate = 0.0

    for end in fsm._edges_by_start[state]:
        # Skip self-loops
        if end == state:
            continue

        # Assume the edge labels are the transition probabilities
        transition_prob = float(fsm._edgelabels[(state, end)])
        end_rate = __calculate_successrate_state(fsm, end)
        rate = rate + transition_prob * end_rate

    fsm._successrates[state] = rate

    return rate


def normalize_transition_probabilities(fsm):
    '''
    Normalize the transition probabilities to discount self loops

    '''
    for state in fsm._states:
        # check for self-loop
        if state in fsm._edges_by_start[state]:
            loop_prob = float(fsm._edgelabels[(state, state)])
            mass = loop_prob / (len(fsm._edges_by_start[state]) - 1)

            for end in fsm._edges_by_start[state]:
                # Self-loops should have a zero transition probability
                if end == state:
                    fsm._edgelabels[(state, state)] = str('0.0')
                else:
                    old_prob = float(fsm._edgelabels[(state, end)])
                    fsm._edgelabels[(state, end)] = str(old_prob + mass)


def fsm_to_dot(fsm, filepath="out.dot"):
    '''
    Converts an FSM object into a state transition diagram dot file.

    '''

    f = open(filepath, 'w')

    f.write('digraph {\n')

    # Add all of the states. Use custom shapes for the
    # TERMINAL and INITIAL states.
    for state in fsm._states:
        label = fsm._statelabels[state]
        shape = ''

        if label == "TERMINAL":
            shape = ',shape=diamond'
        elif label == "INITIAL":
            shape = ',shape=box'

        if hasattr(fsm, '_successrates'):
            # Make the label multiline
            # Only show three decimall places
            label = '{0}\\n{1:.3}'.format(label, fsm._successrates[state])

        f.write(' {0} [label="{1}"{2}];\n'.format(state, label, shape))

    # Add all of the edges
    for start, end in fsm._edges:
        label = fsm._edgelabels[(start, end)]
        f.write('{0}->{1} '
                '[label="{2}", weight="{2}",];\n'.format(start, end, label))

    f.write('}\n')

    f.close()


def dot_to_fsm(dotfile):
    '''
    This function imports an FSM from a dotfile. Specifically, a dot file
    generated by synoptic.

    '''

    fsm = BaseFSM()
    regex_state = re.compile(r'^\s*(?P<state>\d+) \[label="(?P<label>.+)"'
                             '.*\];')
    regex_edge = re.compile(r'^\s*(?P<start>\d+)->(?P<end>\d+).*'
                            'label="(?P<label>\d.\d{2})".*')

    f = open(dotfile, 'r')

    for line in f:
        res = regex_state.search(line)
        res_edge = regex_edge.search(line)

        if res is not None and res.groups() is not None:
            state = res.group('state')
            label = res.group('label')

            #print 'Adding state {0}:{1}'.format(state, label)
            fsm.add_state(state, label)

        elif res_edge is not None and res_edge.groups() is not None:
            start = res_edge.group('start')
            end = res_edge.group('end')
            label = res_edge.group('label')

            #print 'Adding edge {0}->{1}'.format(start, end, label)
            fsm.add_edge(start, end, label)

    # Let's normalize all of those self-loop transition probabilities.
    normalize_transition_probabilities(fsm)

    f.close()

    return fsm


def states_by_event(fsm, event):
    '''
    Returns all states corresponding to a given event. Recall that
    states are labeled with events and multiple states may have the same
    event label.

    '''
    states = []

    for state in fsm._statelabels:
        if fsm._statelabels[state] == event:
            states.append(state)

    return states


def reduce(fsm, dest_event):
    '''
    Attempts to remove states from the FSM while retaining the
    shortest path.
    '''

    # TODO: Re-evaluate this method. A simpler approach is to
    # remove all states that aren't on the returned path.

    # Remove each state, if the shortest path to the event
    # increases then that state must be on a shortest path and
    # we need to keep it.

    estate, path = shortest_path_to_event(fsm, dest_event)
    minlen = len(path)

    # We need a copy of the state list since we will
    # be modifying the original list in the loop.
    states_copy = list(fsm._states)

    for state in states_copy:
        # copy the fsm
        fsm_copy = copy.deepcopy(fsm)

        # If we try to call fsm_copy.remove_state()
        # if will call the remove_state method in fsm
        BaseFSM.remove_state(fsm_copy, state)

        estate, path = shortest_path_to_event(fsm_copy, dest_event)

        if path is None or len(path) > minlen:
            # This state must be on a shortest path
            continue
        elif len(path) == minlen:
            # This state is not on the shortest path
            fsm.remove_state(state)
        else:
            # This should never happen
            raise Exception('How did the path length decrease???')

    # I got some bug in my remove_edge method that is causing some
    # edges to stick around even after the corresponding state has
    # been deleted.
    remove_old_edges(fsm)

    return


def remove_old_edges(fsm):
    '''
    TODO: Fix the bug that allows this to happen!
    Sometimes removing a state from the FSM does remove all edges to/from
    that state. This method will make sure they are removed.

    '''
    for start, end in list(fsm._edges):
        if start not in fsm._states or end not in fsm._states:
            fsm._edges.remove((start, end))


def remove_unreachable_states(fsm, start=None):
    '''
    Finds and removes all states that are unreachable from
    the start state. NOTE: I don't think I ever used or properly
    tested this method.

    '''

    fsm_copy = copy.deepcopy(fsm)

    if start is None:
        start = get_initial(fsm_copy)

    state_copy = list(fsm_copy._states)

    for state in state_copy:
        path = shortest_path(fsm_copy, start, state)

        if path is None:
            BaseFSM.remove_state(fsm_copy, state)

    return fsm_copy


def shortest_path_to_event(fsm, destination_event, current_event="INITIAL",
                           random_start=False, current_state=None):
    '''
    Returns the shortest path from the current event to some state labeled with
    the destination event. The path is a sequence of event labels.

    Given that multiple different states maybe labeled the same we have to
    guess which one is current (optionally, we can specify the current event).
    If random_start is not set then this function
    will return the shortest path of all possible guesses; otherwise, the
    function will return one of the paths.


    '''

    # Find all states that might correspond to the current event
    if not current_state:
        all_current_states = states_by_event(fsm, current_event)
    else:
        all_current_states = [current_state]

    # Find all states that might correspond to the destination event
    all_destination_event_states = states_by_event(fsm, destination_event)

    destination_event_state = None
    event_path = None

    all_paths = []

    for current in all_current_states:
        for state in all_destination_event_states:
            path = shortest_path(fsm, current, state)

            if path is None:
                continue

            all_paths.append((state, path))

            if event_path is None or len(path) < len(event_path):
                event_path = path
                destination_event_state = state

    if random_start and len(all_paths) > 0:
        rand_idx = random.randint(0, len(all_paths) - 1)
        return all_paths[rand_idx]

    return destination_event_state, event_path


def get_initial(fsm, label='INITIAL'):
    '''
    Find the state that corresponds to the INITIAL event. By default,
    the initial state is identified by the 'INITIAL' label.
    Note that synoptic always starts with  the INITIAL event.

    Returns 'None' if it fails to find state with the right label.

    '''

    for state in fsm._statelabels:
        if fsm._statelabels[state] == label:
            return state

    return None


def get_terminal(fsm, label='TERMINAL'):
    '''
    Gets the TERMINAL state.

    '''

    for state in fsm._statelabels:
        if fsm._statelabels[state] == label:
            return state

    return None


def all_simple_paths(fsm, start, end, encountered=None, include_start=True):
    """
    Recursive Breadth first search
    """

    if encountered is None:
        encountered = [start]
        if (start, end, include_start) in fsm._path_cache:
            return fsm._path_cache[(start, end, include_start)]

    next_states = fsm._edges_by_start[start]

    paths = []

    for state in next_states:
        if state == end:
            paths.append([start, state])
            continue

        if state in encountered:
            continue

        # check if any path exists from here to the end
        if not shortest_path(fsm, state, end):
            continue

        new_paths = all_simple_paths(fsm, state, end,
                                     encountered + [state],
                                     True)

        if include_start:
            for path in new_paths:
                path.insert(0, start)

        paths.extend(new_paths)

    fsm._path_cache[(start, end, include_start)] = paths

    return paths



def shortest_path(fsm, start, end, allow_loops=False, include_start=False):
    '''
    Finds the shortest path from the start state to the end state.

    Returns the found path as a sequence of states. Returns 'None' if no path
    is found.

    '''

    if start == end and not allow_loops:
        return []

    dist, prev = calculate_distances(fsm, start)

    path = []

    state = end

    self_start = (start == end)

    while state != start or self_start:
        self_start = False

        if state is None:
            return None

        path.insert(0, state)
        state = prev[state]

    if len(path) == 0:
        return None

    if include_start:
        path.insert(0, start)

    return path


def get_path_eventlist(fsm, path):
    return [fsm._statelabels[x] for x in path]

def get_path_eventstr(fsm, path):
    '''
    Returns a comma-separated string of all events along the
    given path.

    '''
    # Return a comma-separated string
    return ', '.join(get_path_eventlist(fsm, path))


def get_nexthop_eventset(fsm, start):
    events = []

    for state in fsm._edges_by_start[start]:
        events.append(fsm._statelabels[state])

    return set(events)


def print_event_path(fsm, path):
    '''
    Print the event labels for all states in the given path. The path should
    be a list/sequence of states.

    '''

    for state in path:
        print fsm._statelabels[state]


def calculate_distances(fsm, start):
    '''
    Calculate distances from the start state to all other states
    using Dijkstra's algorithm. Assume add edge weights are one.

    '''
    dist = {}
    prev = {}

    for state in fsm._states:
        dist[state] = sys.maxint
        prev[state] = None

    # We have to comment out this line to get cycles.
    # dist[start] = 0

    # Since we are assuming that all edge weights are one,
    # initialize all of the state's immediate neighbors to
    # a distance of 1.
    for neighbor in fsm._edges_by_start[start]:
        dist[neighbor] = 1
        prev[neighbor] = start

    states = list(fsm._states)

    while len(states) > 0:
        min_dist = sys.maxint
        min_dist_state = None

        # Get the state with the shortest distance
        for state in states:
            if dist[state] < min_dist:
                min_dist = dist[state]
                min_dist_state = state

        if min_dist_state is None:
            break

        states.remove(min_dist_state)

        for neighbor in fsm._edges_by_start[min_dist_state]:
            alt = dist[min_dist_state] + 1

            if alt < dist[neighbor]:
                dist[neighbor] = alt
                prev[neighbor] = min_dist_state
            elif alt == dist[neighbor] and random.randint(0, 1) == 1:
                #Sometimes there are multiple paths to the same event with
                #the same cost, let's randomly pick between them.
                dist[neighbor] = alt
                prev[neighbor] = min_dist_state

    # Replace all distances of maxint with None
    for key in dist:
        if dist[key] == sys.maxint:
            dist[key] = None

    return dist, prev


def guess_current_state(fsm, event_list):
    if len(event_list) == 1 and event_list[0] == "INITIAL":
        paths = [get_initial(fsm)]
    else:
        paths = get_paths(fsm, event_list)

    return set([path[-1] for path in paths if len(path) > 0])


def get_event_paths(fsm, event_list):
    paths = get_paths(fsm, event_list)

    path_strings = []

    for path in paths:
        path_strings.append(get_path_eventstr(fsm, path))

    return path_strings


def get_paths(fsm, event_list):
    """
    Given a sequence of events, all simple paths
    including all of those events.

    Returns a path, if it exists for every possible mapping of the input event
    sequence to states.
    """

    #Each event might be associated with many states
    event_states = {}
    #Find all states for each event label
    for event in event_list:
        event_states[event] = states_by_event(fsm, event)

    #Map the event list to all possible states for each
    #of the events, in order
    event_states_ordered = [event_states[x] for x in event_list]

    #Cartesian product! Result is a list of all partially ordered state paths.
    partial_paths = [x for x in itertools.product(*event_states_ordered)]

    paths = []

    for partial in partial_paths:
        path = []
        sub_paths = []

        #make sure there is actually a path between every pair in the partial path
        for x in xrange(len(partial) - 1):
            # if this is the first pair then we include the start of the path
            #pairpath = shortest_path(fsm,
            #                         partial[x],
            #                         partial[x + 1],
            #                         True,
            #                         x == 0)

            #if pairpath is None or len(pairpath) == 0:
            #    break

            #path.extend(pairpath)

            pairpaths = all_simple_paths(fsm,
                                         partial[x],
                                         partial[x+1],
                                         include_start=(x == 0))
            if len(pairpaths) == 0:
                break

            if len(sub_paths) == 0:
                for pp in pairpaths:
                    sub_paths.append(pp)

                continue

            for sub in list(sub_paths):
                sub_paths.remove(sub)
                for pp in pairpaths:
                    sub_paths.append(sub+pp)


        else:
            # All pairs have a path, i.e., the loop didn't break
            #paths.append(path)
            paths.extend(sub_paths)
            continue

    return paths