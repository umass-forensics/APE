"""
"""
import sys
import os
import importlib

import os
from twisted.python import log
from twisted.internet import reactor
from twisted.internet import task

#from autonomotorrent.BTManager import BTManager
#from autonomotorrent.factory import BTServerFactories
#from autonomotorrent.MetaInfo import BTMetaInfo
#from autonomotorrent.DHTProtocol import DHTProtocol

from BTManager import BTManager
from factory import BTServerFactories, BTClientFactory, BTServerFactory
from MetaInfo import BTMetaInfo
from DHTProtocol import DHTProtocol
from BTProtocol import BTServerProtocol

import experiments.testing
import importlib


class BTConfig(object):
    def __init__(self, torrent_path=None, meta_info=None):
        if torrent_path:
            self.metainfo = BTMetaInfo(path=torrent_path)
        elif meta_info:
            self.metainfo = BTMetaInfo(meta_info=meta_info)
        else:
            raise Exception("Must provide either a torrent path or meta_info.")

        self.info_hash = self.metainfo.info_hash
        self.downloadList = None

    def check(self) :
        if self.downloadList is None:
            self.downloadList = range(len(self.metainfo.files))
        for i in self.downloadList :
            f = self.metainfo.files[i]
            size = f['length']
            name = f['path']
            log.msg("File: {0} Size: {1}".format(name, size)) # TODO: Do we really need this?

class BTApp:
    def __init__(self, save_dir=".",
                       listen_port=6881,
                       enable_DHT=False,
                       remote_debugging=False,
                       exp_str=None,
                       exp_args=None,
                       model=None,
                       loopstr=None,
                       bind_ip=''):
        """
        @param remote_degugging enables telnet login via port 9999 with a
            username and password of 'admin'
        """

        # Returns a filelog observer for stdout
        self.observer = log.FileLogObserver(sys.stdout)

        #Set the timeformat to include fractional seconds.
        #e.g., 2013-09-25 22:33:16.89898
        self.observer.timeFormat = '%Y-%m-%d %H:%M:%S.%f'

        log.startLoggingWithObserver(self.observer.emit)
        self.save_dir = save_dir
        self.listen_port = listen_port
        self.enable_DHT = enable_DHT
        self.exp_str = exp_str
        self.exp_args = exp_args
        self.model = model
        self.loopstr = loopstr
        self.tasks = {}
        self.bind_ip = bind_ip

        self.btServer = None

        #RJW: Let's set the experimental scenario
        if self.exp_str:
            if '.' in self.exp_str:
                modulename, classname = self.exp_str.rsplit('.', 1)
                module = importlib.import_module(modulename)
            else:
                module = experiments.testing
                classname = self.exp_str

            client_protocol = getattr(module, classname)

            BTClientFactory.protocol = client_protocol
            client_protocol.exp_args = self.exp_args

            #RJW: not all experiments have a defined server class
            server_protocol = getattr(module, classname+'Svr', None)

            if server_protocol:
                BTServerFactories.protocol = server_protocol
                BTServerFactory.protocol = server_protocol
                server_protocol.exp_args = self.exp_args

                print 'Start the server factory!'
                self.btServer = BTServerFactories(self.listen_port)
                reactor.listenTCP(self.listen_port, self.btServer, interface=bind_ip)
            else:
                print 'No server defined. Not starting the server factory.'
        else:
            #Normal operation
            self.btServer = BTServerFactories(self.listen_port)
            reactor.listenTCP(self.listen_port, self.btServer, interface=bind_ip)

        if enable_DHT:
            log.msg("Turning DHT on.")
            self.dht = DHTProtocol()
            reactor.listenUDP(self.listen_port, self.dht, interface=bind_ip)

        if remote_debugging:
            log.msg("Turning remote debugging on. You may login via telnet "
                    "on port 9999 username & password are 'admin'")
            import twisted.manhole.telnet
            dbg = twisted.manhole.telnet.ShellFactory()
            dbg.username = "admin"
            dbg.password = "admin"
            dbg.namespace['app'] = self
            reactor.listenTCP(9999, dbg)

    def add_torrent(self, config):
        config.check()
        info_hash = config.info_hash
        if info_hash in self.tasks:
            log.msg('Torrent {0} already in download list'.format(config.metainfo.pretty_info_hash))
        else:
            btm = BTManager(self, config)
            # RJW: Adding Ape info to the manager so the protocol class can
            # access it later.
            btm.model_path = self.model
            if self.loopstr:
                btm.loop = [x.strip() for x in self.loopstr.split(',')]

            btm.bind_ip = self.bind_ip
            btm.exp_args = self.exp_args

            self.tasks[info_hash] = btm
            btm.startDownload()
            return info_hash

    def stop_torrent(self, key):
        info_hash = key
        if info_hash in self.tasks:
            btm = self.tasks[info_hash]
            btm.stopDownload()

    def remove_torrent(self, key):
        info_hash = key
        if info_hash in self.tasks:
            btm = self.tasks[info_hash]
            btm.exit()

    def stop_all_torrents(self):
        for task in self.tasks.itervalues() :
            task.stopDownload()

    def get_status(self):
        """Returns a dictionary of stats on every torrent and total speed.
        """
        status = {}
        for torrent_hash, bt_manager in self.tasks.iteritems():
            pretty_hash = bt_manager.metainfo.pretty_info_hash
            speed = bt_manager.get_speed()
            num_connections = bt_manager.get_num_connections()

            status[pretty_hash] = {
                "state": bt_manager.status,
                "speed_up": speed["up"],
                "speed_down": speed["down"],
                "num_seeds": num_connections["server"],
                "num_peers": num_connections["client"],
                }
            try:
                status["all"]["speed_up"] += status[pretty_hash]["speed_up"]
                status["all"]["speed_down"] += status[pretty_hash]["speed_down"]
            except KeyError:
                status["all"] = {
                    "speed_up": status[pretty_hash]["speed_up"],
                    "speed_down": status[pretty_hash]["speed_down"]
                    }


        return status

    def start_reactor(self):
        reactor.run()
