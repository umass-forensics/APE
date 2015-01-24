__author__ = 'wallsr'

import datetime
import os
import re
import sys

from optparse import OptionParser
from traceutils.utilities import calculate_throughput, get_unique_events


def main():
    usage = 'usage: %prog [options] trace0 trace1 ...'
    parser = OptionParser(usage=usage)

    options, args = parser.parse_args()

    distinct_events = set()

    tracedict = {}
    raw_tracedict = {}

    for tracepath in args:
        with open(tracepath, 'r') as f:
            lines = f.readlines()

        events = get_unique_events(lines)
        tracedict[tracepath] = events
        raw_tracedict[tracepath] = lines


        distinct_events = distinct_events | set(events.keys())

    # Add an empty list for any events not seen in the trace.
    # that way we dont have any empty/missing columns.
    for key in tracedict:
        for e in distinct_events:
             if e not in tracedict[key]:
                tracedict[key][e] = []

    #Print the header
    #Note: This header might be different for different sets of input traces.
    ordered_events = sorted(distinct_events)
    print 'filename,throughput,' + ','.join(ordered_events)


    for key in tracedict:
        values = []
        values.append(key)

        tput = 0.0
        if len(tracedict[key]['+piece']) > 0:
            tput = calculate_throughput(tracedict[key]['+handshake'],
                                        tracedict[key]['-request'],
                                        tracedict[key]['+piece'],
                                        raw_tracedict[key])

        values.append(str(tput))

        for e in ordered_events:
            values.append(str(len(tracedict[key][e])))

        print ','.join(values)

    pass





if __name__ == '__main__':
    main()
