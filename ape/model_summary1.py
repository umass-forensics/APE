import sys
import fsm.utilities as utils

print 'states,edges,events'

# skip the first argument
for dotfile in sys.argv[1:]:
    print dotfile
    model = utils.dot_to_fsm(dotfile)

    s = []

    s.append(str(len(model._states)))
    s.append(str(len(model._edges)))
    uniqevents = set(model._statelabels.values())
    s.append(str(len(uniqevents)))

    print ','.join(s)
