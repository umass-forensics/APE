import os
import shlex
import subprocess


def replace_keywords(args, replacement_dict):
        '''
        Substitutes runtime values into the process arguments.
        Keywords are of the form {APE:KEYWORD}.

        Assumes input is a list of strings
        '''
        new_args = list(args)

        for x in xrange(len(new_args)):
            for i, j in replacement_dict.iteritems():
                new_args[x] = str(new_args[x]).replace(i, str(j))

        return new_args


def parse_argfile(filepath):
    f = open(filepath, 'r')
    args_raw = f.readlines()
    f.close()

    #combine all of the lines together
    args_raw = (''.join(args_raw)).replace('\n', ' ')
    args = shlex.split(args_raw)

    return args

def start_process(args, out, ape=None, json=None):
    margs = None

    if json:
        #for now lets just make a list out of the json values
        #margs = [str(x) for x in json.values()]
        margs = list()
        margs.append(json['exe'])
        margs.extend([str(x) for x in json['args']])
    elif not ape:
        margs = list(args)
    else:
        margs = replace_keywords(args,
                                 {'{APE:ITERATION}': ape.model_iteration,
                                 '{APE:MODELDIR}': ape.model_directory,
                                 '{APE:MODELWORKING}': ape.model_working,
                                 '{APE:TRACEDIR}': ape.trace_directory})

    #Assume the arguments are already parsed and the first entry is the
    #executable
    exe = os.path.basename(margs[0])
    exe_dir = os.path.dirname(margs[0])

    if not exe_dir:
        exe_dir = '.'

    proc = None

    #If the user provides a path to the executable, then we want to start
    #the new process in that directory. This is import for processes that
    #will not work unless started in the correct directory,e.g., synoptic.


    if exe_dir is not '':
        #Need to use the preexec_fn arg so that we can use os.killpg later.
        proc = subprocess.Popen(margs, stdout=out, stderr=subprocess.STDOUT, cwd=exe_dir, preexec_fn=os.setsid)
    else:
        proc = subprocess.Popen(margs, stdout=out, stderr=subprocess.STDOUT, preexec_fn=os.setsid)

    return proc


