__author__ = 'wallsr'

import argparse

from twisted.python import log
from twisted.internet import reactor
from factory import ProtocolFactory

import sys


class TesterDriver():
    def __init__(self, protocol):
        self.protocol = protocol

        parser = argparse.ArgumentParser()

        parser.add_argument('-m', '--input_model',
                            default=None,
                            help='Model dot file')
        parser.add_argument("ip", nargs="?", default='localhost')
        parser.add_argument("port", nargs="?", type=int, default=1234)

        args = parser.parse_args()
        self.ip = args.ip
        self.port = args.port

        self.arg_dict = {"model": args.input_model}

        # Returns a filelog observer for stdout
        observer = log.FileLogObserver(sys.stdout)

        #Set the timeformat to include fractional seconds.
        #e.g., 2013-09-25 22:33:16.89898
        observer.timeFormat = '%Y-%m-%d %H:%M:%S.%f'
        log.startLoggingWithObserver(observer.emit)

    def run(self):
        reactor.connectTCP(self.ip, self.port, ProtocolFactory(self.protocol, self.arg_dict))
        reactor.run()