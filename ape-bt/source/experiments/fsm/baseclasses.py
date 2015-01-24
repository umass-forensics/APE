"""
A set of classes for creating and processing FSMs...currently only one class
though.

"""


class BaseFSM(object):
    """
    A simple class for finite state machines.

    """

    def __init__(self):
        self.reset()
        self._name = ''

    def __str__(self):
        desc = [object.__str__(self),
                ' ',
                str(len(self._states)),
                ' states,',
                str(len(self._edges)),
                ' edges.']

        return ''.join(desc)

    def reset(self):
        '''
        Puts the FSM object into a default empty configuration.

        '''

        self._initial_state = None

        # A list of states identified by unique integers (or integer strings)
        self._states = []

        # A dictionary, keyed by state int, giving
        # the string label for the state, used for event labels.
        self._statelabels = {}

        # A list of (start, end) tuples
        self._edges = []
        self._edgelabels = {}
        self._edges_by_start = {}
        self._edges_by_end = {}
        self.__temp_state_counter = 0
        self._path_cache = {}

    def remove_edge(self, start=None, end=None):
        if start is None:
            # Remove all edges coming into the end state
            for start in list(self._edges_by_end[end]):
                self.remove_edge(start, end)

        if end is None:
            #delete all edges starting from this node
            for end in list(self._edges_by_start[start]):
                self.remove_edge(start, end)

        if (start, end) in self._edges:
            self._edges.remove((start, end))
            self._edges_by_start[start].remove(end)
            self._edges_by_end[end].remove(start)
            del self._edgelabels[(start, end)]

    def remove_state(self, state):
        # Remove all edges connected to the state
        self.remove_edge(start=state)
        self.remove_edge(end=state)

        self._states.remove(state)
        del self._statelabels[state]

    def add_state(self, state, label=''):
        if not state in self._states:
            self._states.append(state)
            self._edges_by_start[state] = []
            self._edges_by_end[state] = []
            self._statelabels[state] = label

    def add_edge(self, start_state, end_state, label=''):
        self.add_state(start_state)
        self.add_state(end_state)

        #Remove old edge(s). Important to make sure there is
        #only a 1 edge between two states and each message can only
        #transition between the current state and exactly one other
        #state
        self.remove_edge(start_state, end_state)

        #Add edge
        self._edges.append((start_state, end_state))
        self._edges_by_start[start_state].append(end_state)
        self._edges_by_end[end_state].append(start_state)
        self._edgelabels[(start_state, end_state)] = label

    def has_edge(self, start, end):
        return (start, end) in self._edges
