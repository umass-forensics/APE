__author__ = 'wallsr'

import os
import datetime
from optparse import OptionParser
from traceutils.utilities import get_unique_events, get_time, parse_path


def get_cutoff(piece_times, total_num_pieces=16384):
    #This should be all of the pieces sorted by time
    #across all peers in the trial
    sorted_time = sorted(piece_times)

    print 'Received %d pieces' % len(sorted_time)

    #Check if the target didn't download the
    #whole file
    if len(sorted_time) < 16384:
        print 'Download not finished.'
        return

    print 'Took %f seconds to download' % \
          (sorted_time[-1] - sorted_time[0]).total_seconds()

    return sorted_time[-1]


def main():
    usage = 'usage: %prog [options] trace0 trace1 ...'
    parser = OptionParser(usage=usage)

    options, args = parser.parse_args()

    piece_times_dict = {}
    cutoff_dict = {}

    trials_idx = 0
    trials_map = {}

    for tracepath in args:
        key = ''.join(tracepath.split('_')[:-1])
        if key not in trials_map:
            trials_map[key] = str(trials_idx)
            trials_idx += 1
            piece_times_dict[key] = []

        trial = trials_map[key]

        with open(tracepath, 'r') as f:
            lines = f.readlines()

        events = get_unique_events(lines)

        if '-piece' not in events:
            continue

        piece_times = get_time(events['-piece'])
        piece_times_dict[key].extend(piece_times)

    for trial_key in piece_times_dict:
        cutoff = get_cutoff(piece_times_dict[trial_key])
        print 'Cutoff: %s' % str(cutoff)
        cutoff_dict[trial_key] = cutoff

    for tracepath in args:
        trace_name = os.path.basename(tracepath)
        tracedir = os.path.dirname(tracepath)



        trial_key = ''.join(tracepath.split('_')[:-1])
        if cutoff_dict[trial_key] is None:
            'Trial has no cutoff time: %s' % trial_key
            cutoff_dict[trial_key] = datetime.datetime(2100, 1, 1, 0, 0, 0, 1)


        with open(tracepath, 'r') as f:
            lines = f.readlines()

        times = get_time(lines, null_failures=True)

        cutoff_idx = None



        for x in xrange(len(times)):
            #line didn't have a timestamp
            if times[x] is None:
                continue
            #check if this event occurred after the
            #cutoff
            if times[x] > cutoff_dict[trial_key]:
                cutoff_idx = x
                break

        with open(os.path.join(tracedir,
                               'truncated'+trace_name), 'w+') as f_out:

            if cutoff_idx:
                print 'Truncating %s at line %d' \
                % (trace_name, cutoff_idx)

                last_line = str(cutoff_dict[trial_key]) + ' TRUNCATED!!!'

                f_out.writelines(lines[:cutoff_idx]+[last_line])
            else:
                print 'Not truncating %s' % trace_name
                f_out.writelines(lines)






if __name__ == '__main__':
    main()
