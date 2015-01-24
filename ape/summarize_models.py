import os
import random

import utilities

class Subs(object):
    def __init__(self):
        self.model_iteration = ''
        self.model_directory = ''
        self.model_working = ''
        self.trace_directory = ''


def sample_traces(tracedir, samplesize=1):
    tester_traces = []
    for files in os.listdir(tracedir):
        if files.count('tester') > 0:
            tester_traces.append(os.path.join(tracedir,files))

    sample = random.sample(tester_traces, samplesize)

    return sample


def build_model(args, traces, model_iteration='0', model_directory='.'):
    #Make a copy of the original arguments
    margs = list(args)
    margs.extend(traces)

    modeler_logpath = os.path.join(model_directory,
                                   'log_iter_{0}.txt'.format(model_iteration))
    modeler_log = open(modeler_logpath, 'w')

    subs = Subs()
    subs.model_iteration = model_iteration
    subs.model_directory = model_directory

    proc = utilities.start_process(margs, modeler_log, subs)

    #wait for the modeler to finish
    proc.wait()
    modeler_log.close()

    dotfile = os.path.join(model_directory, '{0}.dot'.format(model_iteration))

    import fsm.utilities

    model = fsm.utilities.dot_to_fsm(dotfile)

    return model

def summarize_model(model, numtraces):
    '''
    returns the following string:
        numtraces,num_states,num_edges,num_unique_events,
        num_receive_events,num_send_events

    '''

    s = []
    s.append(str(numtraces))
    s.append(str(len(model._states)))
    s.append(str(len(model._edges)))

    uniqevents = set(model._statelabels.values())
    s.append(str(len(uniqevents)))

    revents = set([e for e in uniqevents if e.startswith('+')])
    sevents = set([e for e in uniqevents if e.startswith('-')])

    s.append(str(len(revents)))
    s.append(str(len(sevents)))

    return ','.join(s)

def main(tracedir, outdir, synoptic_argsfile):
    #Build a bunch of models

    synoptic_args = utilities.parse_argfile(synoptic_argsfile)

    sample_sizes = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100]
    trial_size = 30
    print 'traces,states,edges,events,recv_events,send_events'

    for size in sample_sizes:
        for x in xrange(trial_size):
            traces = sample_traces(tracedir, size)
            model = build_model(synoptic_args,
                                traces,
                                '{0}_{1}'.format(size, x),
                                outdir)
            print summarize_model(model, size)

    sample_sizes = [200, 300, 400, 500]
    trial_size = 3

    for size in sample_sizes:
        for x in xrange(trial_size):
            traces = sample_traces(tracedir, size)
            model = build_model(synoptic_args,
                                traces,
                                '{0}_{1}'.format(size, x),
                                outdir)
            print summarize_model(model, size)



def test():
    synoptic_argsfile='/Users/wallsr/Documents/Research/ProtocolRevEng/git/args/args_synoptic.txt'
    tracedir = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/experiments/utorrent/explore_nsbasicstart_300_1/traces'
    tmpdir = '/Users/wallsr/Documents/Research/ProtocolRevEng/git/ape/tmp'

    main(tracedir, tmpdir, synoptic_argsfile)

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 4:
        print 'Usage: tracedir outdir synoptic_argsfile'
        exit(1)

    tracedir = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    syn_args = os.path.abspath(sys.argv[3])

    main(tracedir, outdir, syn_args)
