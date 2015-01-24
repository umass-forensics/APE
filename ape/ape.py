import datetime
import json
import os
import re
import sys
import time
import utilities

from datetime import datetime as dt
from progressbar import ProgressBar, ETA, Timer, Counter, Bar


decoder = json.JSONDecoder()
encoder = json.JSONEncoder(indent=2)


def log(message):
    """
    Simple method for printing a timestamp and log to stdout
    """
    print dt.now().strftime('[%Y-%m-%d %H:%M:%S.%f] ') + message


class Ape(object):
    '''

    '''

    def __init__(self):
        self.model_iteration = ''
        self.model_directory = ''
        self.model_working = ''
        self.trace_directory = ''
        self.num_traces_periter = 2
        self.num_iterations = 1
        self.trace_iter = None

    def generate_traces(self,
                        args_tester,
                        args_target,
                        num_traces=1,
                        output_dir='.',
                        file_prepend='',
                        timeout=5):
        #pbar = ProgressBar(maxval=num_traces).start()

        tester_traces = []


        for x in xrange(0, num_traces):

            tracepath_tester  = os.path.join(output_dir,
                                            '{1}tester_{0}.txt'.format(x,file_prepend))
            out_tester = open(tracepath_tester,'w')

            # We will use this to peek at the log file. Let's us check when
            # the client connects (based on a regex match)
            out_tester_read = open(tracepath_tester, 'r')

            out_target = open(os.path.join(output_dir,
                                        '{1}target_{0}.txt'.format(x, file_prepend)),
                            'w')

            #start the target
            target = utilities.start_process(args_target, out_target, self)

            #give the target a few seconds to start
            time.sleep(15)

            #start the tester
            tester = utilities.start_process(args_tester, out_tester, self)

            #check if the two process have connected.
            # TODO: Make this regex settable
            regex_connected = re.compile(r'connected to client ID')

            start = datetime.datetime.now()

            successful = False

            while not successful:
                out_tester.flush()
                recent_text = out_tester_read.read()

                if regex_connected.search(recent_text):
                    successful = True
                    break

                time.sleep(1)

                span = datetime.datetime.now() - start

                if span.seconds > 30:
                    sys.stderr.write('\n!Failed to connected tester and target\n')
                    time.sleep(10)
                    break

            last_position = 0
            start = datetime.datetime.now()

            #check if the two processes have stopped talking
            #right now that means check if the log file has been written to
            #in the last x seconds
            while successful:
                time.sleep(10)

                current_position = out_tester.tell()

                if current_position == last_position:
                    sys.stderr.write('Breaking: clients stopped communicating')
                    break

                span = datetime.datetime.now() - start

                #Break if the file has grown continuously for 2 minutes
                if span.seconds > 120:
                    sys.stderr.write('Breaking: file reached growth timeout')
                    break

                last_position = current_position
            #clean up
            self.trace_iter += 1

            tester.terminate()
            target.terminate()

            #If the subprocess doesn't stop in 5 seconds let's kill it
            for y in xrange(5):
                if tester.poll() and target.poll():
                    break
                time.sleep(1)
            else:
                try:
                    tester.kill()
                except OSError:
                    pass
                try:
                    target.kill()
                except OSError:
                    pass

            out_tester.close()
            out_target.close()
            tester_traces.append(tracepath_tester)

        return tester_traces


    def explore(self, opt):
        #stage 1: build the model
        args_tester = utilities.parse_argfile(opt.tester_argfile)
        args_target = utilities.parse_argfile(opt.target_argfile)
        args_modeler = utilities.parse_argfile(opt.modeler_argfile)
        self.model_working = opt.initial_model
        self.num_iterations = opt.num_iterations
        self.num_traces_periter = opt.num_traces_periter

        print args_tester

        self.output_directory = os.path.join(os.getcwd(), opt.output_dir)

        #Create the output directory
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
        else:
            raise Exception('Output directory already exists! {0}'.format(self.output_directory))

        print 'Exploration Stage'

        self.trace_directory = os.path.join(self.output_directory, 'traces')
        os.makedirs(self.trace_directory)
        self.model_directory = os.path.join(self.output_directory, 'models')
        os.makedirs(self.model_directory)

        all_traces = []

        print 'Generating traces'

        self.trace_iter = 0

        for x in xrange(0, self.num_iterations):
            #print 'Iteration {0}'.format(x)
            self.model_iteration = str(x)
            traces = self.generate_traces(args_tester,
                                          args_target,
                                          num_traces=self.num_traces_periter,
                                          output_dir=self.trace_directory,
                                          file_prepend='iter_{0}_'.format(x))

            all_traces.extend(traces)

            self.build_model(args_modeler, all_traces)

    def build_model(self, args, traces):
        #Make a copy of the original arguments
        margs = list(args)
        margs.extend(traces)

        modeler_logpath = os.path.join(self.model_directory,
                                    'log_iter_{0}.txt'.format(self.model_iteration))
        modeler_log = open(modeler_logpath, 'w')
        proc = utilities.start_process(margs, modeler_log, self)

        #wait for the modeler to finish
        proc.wait()
        modeler_log.close()

        #Update the working model path
        self.model_working = os.path.join(self.model_directory,
                '{0}.dot'.format(self.model_iteration))

