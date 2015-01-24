'''
File:        ape.py
Author:      rjwalls
Description:

'''
import datetime
import os
import re
import signal
import subprocess
import sys
import threading
import time

import utilities

from ape import Ape
from optparse import OptionParser
from progressbar import ProgressBar, ETA, Timer, Counter, Bar

gsubproc = []
shutdown_event = threading.Event()

def signal_handler(signal, frame):
    print 'Received singal. Stopping subprocesses.'

    global gsubproc

    # Iterate over any of the running processes.
    for proc in [ x for x in gsubproc if not x.poll()]:
        print "Terminating process {0}".format(proc.pid)
        proc.terminate()

    for proc in [ x for x in gsubproc if not x. poll()]:
        print "Waiting for {0} to finish".format(proc.pid)
        proc.wait()

    sys.exit(0)

class AdaptiveETA(Timer):
    """Widget which attempts to estimate the time of arrival.

    Uses a weighted average of two estimates:
    1) ETA based on the total progress and time elapsed so far
    2) ETA based on the progress as per tha last 10 update reports

    The weight depends on the current progress so that to begin with the
    total progress is used and at the end only the most recent progress is
    used.

    Pull from progressbar google code site
    """

    TIME_SENSITIVE = True
    NUM_SAMPLES = 10

    def _update_samples(self, currval, elapsed):
        sample = (currval, elapsed)
        if not hasattr(self, 'samples'):
            self.samples = [sample] * (self.NUM_SAMPLES + 1)
        else:
            self.samples.append(sample)
        return self.samples.pop(0)

    def _eta(self, maxval, currval, elapsed):
        return elapsed * maxval / float(currval) - elapsed

    def update(self, pbar):
        """Updates the widget to show the ETA or total time when finished."""
        if pbar.currval == 0:
            self.prevval = 0
            self.statstr = 'ETA:  --:--:--'
        elif pbar.currval == self.prevval:
            # No need to update the estimate if we didn't increase the currval
            pass
        elif pbar.finished:
            self.statstr = 'Time: %s' % self.format_time(pbar.seconds_elapsed)
        else:
            elapsed = pbar.seconds_elapsed
            currval1, elapsed1 = self._update_samples(pbar.currval, elapsed)
            eta = self._eta(pbar.maxval, pbar.currval, elapsed)
            if pbar.currval > currval1:
                etasamp = self._eta(pbar.maxval - currval1,
                                    pbar.currval - currval1,
                                    elapsed - elapsed1)
                weight = (pbar.currval / float(pbar.maxval)) ** 0.5
                eta = (1 - weight) * eta + weight * etasamp
            self.statstr = 'ETA:  %s' % self.format_time(eta)

        self.prevval = pbar.currval

        return self.statstr

def thread_pbar(ape):
    pbar = None

    while not shutdown_event.is_set():
        pbar = update_pbar(pbar, ape)

        #waiting for the trace generator to start
        time.sleep(1)

    if pbar is not None:
        pbar.finish()


def update_pbar(pbar, ape):
    if ape.trace_iter is None:
        return pbar
    elif pbar is None:
        pbar_widgets = ['Trace: ', Counter(), ' (', Timer(), ') ',
                        Bar(), AdaptiveETA()]
        pbar = ProgressBar(maxval=ape.num_iterations*ape.num_traces_periter,
                           widgets=pbar_widgets).start()

    pbar.update(ape.trace_iter)

    return pbar


def console():
    print("Ape!")

    usage = 'usage: %prog [options]'
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--modeler_argfile', action='store', type='string',
                      dest='modeler_argfile', default=None,
                      help='file containing the model builder arguments')
    parser.add_option('-t', '--tester_argfile', action='store', type='string',
                      dest='tester_argfile', default=None,
                      help='file containing the tester arguments')
    parser.add_option('-u', '--target_argfile', action='store', type='string',
                      dest='target_argfile', default=None,
                      help='file containing the tester arguments')
    parser.add_option('-o', '--output_dir', action='store', type='string',
                      dest='output_dir', default='.',
                      help='directory for the output')
    parser.add_option('-i', '--initial_model', action='store', type='string',
                      dest='initial_model', default='',
                      help='the initial model to use in the exploration stage')
    parser.add_option('--num_traces_periter', action='store', type='int',
                      dest='num_traces_periter', default=2,
                      help='the number of traces per iteration')
    parser.add_option('--num_iteration', action='store', type='int',
                      dest='num_iterations', default=2,
                      help='the number of iterations for the model builder')
    parser.add_option('--input_files', action='append', type='string',
                      dest='input_files',
                      help='The input files to use as seeds for the process')
    parser.add_option('--input_files_names', action='append', type='string',
                      dest='input_files_names',
                      help='the names to use for the input file.')

    options, args = parser.parse_args()

    # Looks like I don't need this call since python will, by default, send
    # SIGINT to all of my spawned subprocesses
    #signal.signal(signal.SIGINT, signal_handler)

    try:
        ape = Ape()

        pbthread = threading.Thread(target=thread_pbar, args=[ape])
        #Setting this allows the thread to terminate when Ctrl-c is pressed.
        #pbthread.daemon = True
        pbthread.start()

        ape.explore(options)
    except:
        raise
    finally:
        shutdown_event.set()



if __name__ == '__main__':
    console()
