'''
File:        ape_explore.py
Author:      rjwalls
Description: Try building up the model!

'''

import sys


def main():
    usage = 'usage: %prog [options] tester_args target_args torrent_info'

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
    torrent_info = args[2]

    testerjson = loadjson(tester_args)
    targetjson = loadjson(target_args)
    torrentjson = loadjson(torrent_info)

    torrent_dir = os.path.dirname(torrent_info)
    torrent_path = os.path.join(torrent_dir, torrentjson['torrent'])

    replacement = {'{APE:PORT}': options.tester_port,
                  '{APE:OUTDIR}': options.output_dir,
                  '{APE:TORRENT}': torrent_path,
                  '{APE:STARTFILE}': torrentjson['partial'],
                  '{APE:STARTFILENAME}': torrentjson['data']}

    for (id, test_file, targ_file) in filelist:
        replacement['{APE:STARTFILE}'] = test_file
        test_args = utilities.replace_keywords(testerjson['args'], replacement)

        replacement['{APE:STARTFILE}'] = targ_file
        targ_args = utilities.replace_keywords(targetjson['args'], replacement)

        run = {}
        run['outdir'] = options.output_dir
        run['conn_regex'] = r'connected to client ID'
        run['count'] = 1
        run['id'] = id
        run['tester'] = { 'proc':testerjson['proc'], 'args':test_args }
        run['target'] = { 'proc':targetjson['proc'], 'args':targ_args }

        runs.append(run)

    print json.dumps(runs, indent = 2)




def loadjson(file):
    try:
        f = open(file, 'r')
        raw = f.read()
        f.close
        return json.loads(raw)
    except:
        print 'Error loading %s' %file
        exit(1)


if __name__ == '__main__':
    main()
