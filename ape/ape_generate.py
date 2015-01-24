'''
File:        apegen.py
Author:      rjwalls
Description: Attempts to the tester and target processes using the given
             arguments.

'''
#!/usr/bin/env Python
import os
import signal
import sys
import time
import utilities as utils

from ape import decoder, log
from optparse import OptionParser


def generate_traces(run_info):
    for x in xrange(run_info['count']):
        traceid=''

        if 'sub_id' in run_info:
            log('Iteration %s_%d' %(run_info['sub_id'], x))
            traceid = '%s_%d' % (run_info['sub_id'], x)
        else:
            log('Iteration %d' % x)
            traceid = str(x)

        # Write all of the traces into a subdirectory named after
        # the id of the experimental run.
        outdir = os.path.join(run_info['outdir'], run_info['id'])

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if 'timeout' in run_info:
            generate_trace(run_info['procs'], outdir, traceid, run_info['timeout'])
        else:
            generate_trace(run_info['procs'], outdir, traceid)


def generate_trace(process_info, outdir='.', traceid='x', timeout=60):
    #the spawned peer processes keyed by the peerinfo id.
    procs = {}

    # Start each process
    for pinfo in process_info:
        tracefilepath = os.path.join(outdir, 'proc_%s_%s.txt'
                                     % (traceid, pinfo['id']))
        # Use 0 to make this unbuffered.
        tracefile = open(tracefilepath, 'w', 0)

        #if not tracefile:
        #    log('WARNING! Unable to open trace file: %s' % tracefilepath)

        log(tracefilepath)

        proc = utils.start_process(None, tracefile, json=pinfo)
        log('Started process %s: %d' % (pinfo['id'], proc.pid))

        #if not proc.stdout:
        #    log('WARNING! Process stdout is type none.')

        if 'startup_delay' in pinfo:
            log('Waiting %d seconds...' % pinfo['startup_delay'])
            # Wait the specified number of seconds before starting the next process
            time.sleep(pinfo['startup_delay'])

        procs[pinfo['id']] = (proc, tracefile)

    #Terminate the trace when these procs finish
    #The process info should contain the wait for 'wait_for_term'
    #key set to true.
    terms = [peer['id'] for peer in process_info
                  if 'wait_for_term' in peer and
                  peer['wait_for_term']]

    term_procs = [p for p, tfile in [procs[x] for x in terms]]

    #Let's sit and wait until either all of the processes
    #in term_procs have finished or the timeout is reached.
    wait_for_termination(term_procs, timeout)

    terminate([pid for pid, tfile in [procs[x] for x in procs]],
              timeout=60)

    # Close the trace files
    for p in procs:
        proc, tfile = procs[p]
        tfile.flush()
        tfile.close()


def wait_for_termination(procs, timeout=1):
    """
    Expects Popen process objections
    'timeout' is the max time, in seconds, before returning.
    """

    alldead = False

    for x in xrange(timeout):
        for proc in procs:
            if proc.poll() is None:
                #Still a process running.
                break
        else:
            #All of the processes have terminated
            alldead = True
            break

        time.sleep(1)

    return alldead


def terminate(procs, timeout=60):
    '''
    Expects a list of Popen process objects.
    '''

    for proc in procs:
        # check if the process is still runing
        if proc.poll() is None:
            #Let's send the sigterm signal to the process and
            #child processes it may have spawned.
            os.killpg(proc.pid, signal.SIGTERM)

            #if we don't wait for the process to terminate, then we won't get
            #the full log file.
            log('Waiting for process %s to finish.' % str(proc.pid))
            proc.wait()

            log('Process %s killed with return code: %s.' % (str(proc.pid), str(proc.wait())))
        else:
            log('Process %s is already dead with return code: %s.' % (str(proc.pid), str(proc.wait())))

    #if not wait_for_termination(procs, timeout=timeout):
    #    for proc in procs:
    #        #Kill the process if it hasn't finished by now.
    #        if proc.poll() is None:
    #            try:
    #                proc.kill()
    #            except OSError:
    #                pass


def main():
    usage = 'usage: %prog [options] tester_argfile target_argfile'

    parser = OptionParser(usage=usage)

    #These options override the values in the json input
    parser.add_option('-c', '--count', action='store', type='int',
                      dest='count', default=None,
                      help='the number of traces to generate')
    parser.add_option('-o', '--output_dir', action='store', type='string',
                      dest='output_dir', default=None,
                      help='directory for the output')
    parser.add_option('-t', '--timeout', action='store', type='int',
                      dest='timeout', default=None,
                      help='the amount of time, in seconds to wait before'
                      'killing all spawned processes')
    parser.add_option('--sub_id', action='store', type='string',
                      dest='sub_id', default=None)

    options, args = parser.parse_args()
    runs = sys.stdin.read()

    if len(runs.strip()) == 0:
        exit(1)

    try:
        runs = decoder.decode(runs)
    except ValueError as e:
        log('Unable to read the input JSON.')
        sys.stderr.write(e.message + '\n')
        exit(1)

    for run in runs:
        if options.count:
            run['count'] = options.count

        if options.timeout:
            run['timeout'] = options.timeout

        if options.output_dir:
            run['outdir'] = options.output_dir

        if options.sub_id:
            run['sub_id'] = options.sub_id

        log('Using output directory %s' % run['outdir'])
        log('Timeout: %d seconds' % run['timeout'])

        log('Run: %s' % run['id'])
        generate_traces(run)


if __name__ == '__main__':
    main()
