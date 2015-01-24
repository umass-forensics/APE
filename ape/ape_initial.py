'''
File:        ape_initial.py
Author:      rjwalls
Description: Generates the JSON output for the ape_generate function to create
initial seed traces for a target.
'''

# Call our tester and the target with different starting file values.
# We want the tester to be the seed sometimes and the leech other times.

# Input should be an JSON dictionary describing the torrent.

import json
import os
import utilities

from optparse import OptionParser

encoder = json.JSONEncoder()


def main():
    usage = 'usage: %prog [options] tester_args target_args tracker_args torrent_info'

    parser = OptionParser(usage=usage)

    parser.add_option('-o', '--output_dir', action='store', type='string',
                      dest='output_dir', default='.',
                      help='directory for the output')
    parser.add_option('-p', '--tester_port', action='store', type='int',
                      dest='tester_port', default=6880,
                      help='port for the tester')

    options, args = parser.parse_args()

    tester_args = args[0]
    target_args = args[1]
    tracker_args = args[2]
    torrent_info = args[3]

    testerjson = loadjson(tester_args)
    targetjson = loadjson(target_args)
    trackerjson = loadjson(tracker_args)
    torrentjson = loadjson(torrent_info)

    torrent_dir = os.path.dirname(torrent_info)
    torrent_path = os.path.join(torrent_dir, torrentjson['torrent'])

    replacement = {'{APE:PORT}': options.tester_port,
                  '{APE:OUTDIR}': options.output_dir,
                  '{APE:TORRENT}': torrent_path,
                  '{APE:STARTFILE}': '.',
                  '{APE:STARTFILENAME}': torrentjson['data']}

    full = os.path.join(torrent_dir, torrentjson['data'])
    partial = os.path.join(torrent_dir, torrentjson['partial'])
    partialb = os.path.join(torrent_dir, torrentjson['partialb'])
    none = os.path.join(torrent_dir, torrentjson['none'])

    filelist = [('full_none', full, none),
                ('full_partial', full, partial),
                ('partial_none', partial, none),
                ('partial_partial', partial, partialb),
                ('none_full', none, full),
                ('none_partial', none, partial)]

    runs = list()

    for (id, test_file, targ_file) in filelist:
        replacement['{APE:STARTFILE}'] = test_file

        tester = testerjson.copy()
        tester["args"] = utilities.replace_keywords(tester["args"], replacement)

        replacement['{APE:STARTFILE}'] = targ_file

        target = targetjson.copy()
        target["args"] = utilities.replace_keywords(target["args"], replacement)

        run = {}
        run['outdir'] = options.output_dir
        #run['conn_regex'] = r'connected to client ID'
        run['count'] = 1
        run['id'] = id
        run['procs'] = []
        run['procs'].append(trackerjson)
        run['procs'].append(target)
        run['procs'].append(tester)

        runs.append(run)

    print json.dumps(runs, indent = 2)

def loadjson(file):
    try:
        f = open(file, 'r')
        raw = f.read()
        f.close
        return json.loads(raw)
    except Exception as e:
        print 'Error loading %s' %file
        print e.message
        exit(1)

if __name__ == '__main__':
    main()

