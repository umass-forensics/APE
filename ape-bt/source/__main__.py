"""
"""
import json
import os
import tempfile
import shutil
from twisted.python import log
from BTApp import BTApp, BTConfig
from . import __version__ as VERSION

def main(opt, btfiles):
    tmpdir = None

    if opt.start_clean:
        tmpdir = tempfile.mkdtemp()
        print 'Create temp directory: {0}'.format(tmpdir)
        opt.save_dir = tmpdir

        if opt.start_file:
            newname = None

            if opt.start_file_name:
                newname=opt.start_file_name
            else:
                newname=os.path.basename(opt.start_file)

            print 'Using input file: {1} from {0}'.format(opt.start_file,
                                                        newname)
            shutil.copyfile(opt.start_file, os.path.join(tmpdir, newname))

    exp_args = None
    if opt.experiment_args:
        decoder = json.JSONDecoder()
        exp_args = decoder.decode(opt.experiment_args)

    app = BTApp(save_dir=opt.save_dir,
                listen_port=opt.listen_port,
                enable_DHT=opt.enable_dht,
                remote_debugging=opt.remote_debugging,
                exp_str=opt.exp_str,
                exp_args=exp_args,
                model=opt.model,
                loopstr=opt.loopstr,
                bind_ip=opt.bind_ip,)

    if opt.exp_str:
        log.msg('Starting experiment scenario {0}'.format(opt.exp_str))

    for torrent_file in btfiles:
        try:
            log.msg('Adding: {0}'.format(torrent_file))
            config = BTConfig(torrent_file)
            config.downloadList = None
            app.add_torrent(config)

        except:
            log.err()
            log.err("Failed to add {0}".format(torrent_file))

    app.start_reactor()

    print 'Clean-up time.'

    #we need to delete it, but lets make sure it isnt our working dir
    if tmpdir and os.path.exists(tmpdir) and os.getcwd() != tmpdir:
        print 'Removing tmp directory.'
        shutil.rmtree(tmpdir)

def console():
    print("AutonomoTorrent v{0}".format(VERSION))
    print("Let's do this!")
    from optparse import OptionParser

    usage = 'usage: %prog [options] torrent1 torrent2 ...'
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--output_dir', action='store', type='string',
                      dest='save_dir', default='.',
                      help='save download file to which directory')
    parser.add_option('-l', '--listen-port', action='store', type='int',
                     dest='listen_port', default=6881,
                     help='Bittorrent listen port')
    parser.add_option("-d", "--enable_dht", action="store_true",
                    dest="enable_dht", help="enable the DHT extension")
    parser.add_option("--remote_debug", action="store_true",
                    dest="remote_debugging",
                    help="enable remote debugging through twisted's manhole" + \
                    " telnet service on port 9999 (username & password: admin)")

    parser.add_option("-e", "--experiment", help="specify the experiment."
                      " Default is normal operation.",
                    action='store', type='string', dest='exp_str', default='')
    parser.add_option("--experiment_args", help="A json dictionary of experiment"
                      "specific arguments", type='string', dest='experiment_args',
                      default=None)
    parser.add_option("-m", "--model", help="specify the initial model",
                    action='store', type='string', dest='model', default='')

    parser.add_option("-s", "--loop_sequence", help="specify the loop sequence",
                    action='store', type='string', dest='loopstr', default=None)

    parser.add_option("--start_clean", help="creates a temp directory to work in",
                    action='store_true', dest='start_clean')
    parser.add_option("--start_file", help="Start with this input file in" +\
                      "the output directory.",
                    action='store', type='string',  dest='start_file',
                      default='')
    parser.add_option("--start_file_name", help="Rename the start file to this.",
                    action='store', type='string',  dest='start_file_name',
                      default='')
    parser.add_option('--bind_ip', help='Use the specified network interface,'
                      'identified by IP', type='string', dest='bind_ip',
                      default='')

    options, args = parser.parse_args()
    if(len(args) > 0):
        main(options, args)
    else:
        print "Error: No torrent files given."
        print usage

if __name__ == '__main__':
    console()
