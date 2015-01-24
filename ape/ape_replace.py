__author__ = 'wallsr'
import sys
import utilities
from ape import decoder, encoder
from optparse import OptionParser


BIND_IP_BASE = '10.0.2.'
BIND_IP_END = 50


def run_replace(run):
    """
    Takes a JSON dictionary containing a list of processes.
    For each of these processes, we replace predefined string
    literals. We also will replicate a process's arguments, allowing us
    to define the process once and then create many copies with slightly
    different starting arguments, e.g., bind_ip.

    Returns a dictionary of process arguments.
    """
    new_run = run.copy()
    new_procs = []

    for proc in run['procs']:
        new_procs.extend(process_replace(proc))

    new_run['procs'] = new_procs
    return new_run


def process_replace(proc):
    """
    Replace process arguments. The input is a dictionary.
    This method could be greatly improved. Right now it is limited in
    the depth it can handle and the type values it can replace. (hint: strings)
    """

    new_procs = []
    rep = 1

    # check if we want to replicate these arguments (for creating many identical peers)
    if 'replicate' in proc:
        rep = proc['replicate']
        # We don't want this arg to show up in the results
        del proc['replicate']

    nprocs = []

    for x in xrange(rep):
        nproc = proc.copy()
        rdict = {'{APE:BIND_IP}': get_bind_ip(), '{APE:REPL_ID}': x}

        for key in nproc:
            ktype = type(nproc[key])

            if ktype is list:
                nproc[key] = utilities.replace_keywords(nproc[key], rdict)
            elif ktype is str or ktype is unicode:
                nproc[key] = utilities.replace_keywords([nproc[key]], rdict)[0]

        nprocs.append(nproc)

    return nprocs


def get_bind_ip():
    """
    Returns the next bind ip in order. Will only
    return each IP once.
    """
    global BIND_IP_BASE
    global BIND_IP_END

    ip = BIND_IP_BASE + str(BIND_IP_END)
    BIND_IP_END += 1

    return ip



def main():
    usage = 'usage: %prog [options]'

    parser = OptionParser(usage=usage)

    options, args = parser.parse_args()

    runs = sys.stdin.read()

    #test_json = '[{"id":"teststring!","procs":[{"replicate":2, "id":"bar_{APE:REPL_ID}",' \
    #            '"args":["--bind_ip {APE:BIND_IP}"]}]}]'

    if len(runs.strip()) == 0:
        exit(1)

    try:
        runs = decoder.decode(runs)
    except ValueError as e:
        print 'Unable to read the input JSON.'
        sys.stderr.write(e.message + '\n')
        exit(1)

    new_runs = []

    for run in runs:
        new_runs.append(run_replace(run))

    print encoder.encode(new_runs)


if __name__ == '__main__':
    main()