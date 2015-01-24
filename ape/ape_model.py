'''
File:        ape_model.py
Author:      rjwalls
Description: Generate the synoptic model!

'''

import fnmatch
import json
import utilities
import os
import sys

from optparse import OptionParser


def main():
    #read the model args from a json file
    usage = 'usage: %prog [options] model_args trace_directory'

    parser = OptionParser(usage=usage)

    parser.add_option('--id', action='store', type='string',
                      dest='id', default='model',
                      help='name for the output model')
    parser.add_option('-p', '--match_pattern', action='store', type='string',
                      dest='match_pattern', default='tester*',
                      help='UNIX style file matching string')
    parser.add_option('--print_dot', action='store_true',
                      dest='print_dot',
                      help='print the models dot file to stdout')


    options, args = parser.parse_args()

    model_args = args[0]
    #We have to remove the trailing slash so the proc arguments aren't
    #messed up.
    trace_dir = args[1].rstrip('/')

    traces = []
    for f in os.listdir(trace_dir):
        if fnmatch.fnmatch(f, options.match_pattern):
            traces.append(os.path.join(trace_dir, f))

    modelerjson = loadjson(model_args)

    replacement = {'{APE:MODELDIR}': trace_dir,
                  '{APE:ITERATION}': options.id}

    modelerjson["args"] = utilities.replace_keywords(modelerjson["args"],
                                                     replacement)
    modelerjson["args"].extend(traces)

    out_modeler = open(os.path.join(trace_dir, options.id + '.log'), 'w')
    modeler = utilities.start_process(None, out_modeler, json=modelerjson)

    modeler.wait()
    out_modeler.close()

    # We are just assuming the model is written with this name
    dotfile = os.path.join(trace_dir, options.id + '.dot')

    if not options.print_dot or not os.path.exists(dotfile):
        exit(0)

    with open(dotfile, 'r') as f:
        print f.readlines()


def loadjson(file):
    try:
        f = open(file, 'r')
        raw = f.read()
        f.close
        return json.loads(raw)
    except:
        sys.stderr.write('Error loading %s' %file)
        exit(1)



if __name__ == '__main__':
    main()
