__author__ = 'wallsr'

from twisted.python import log

from ..BTProtocol import BTProtocol, BTClientProtocol, BTServerProtocol
from ..ClientIdentifier import identify_client


class IgnoreClientBase(BTProtocol):
    """
    Given a list of client strings, e.g., utorrent, this class will check the client of the
    current peer and if that peer's client is in the ignore list.

    If ignoring, this peer will not send an unchoke, nor will it send or respond to piece
    requests.
    """

    def __init__(self):
        BTProtocol.__init__(self)

        self.ignore_list = []
        # When this is set, we won't send or respond to requests
        self.ignoring = False

        if self.exp_args and 'ignore_clients_list' in self.exp_args:
            self.ignore_list = self.exp_args['ignore_clients_list']
            log.msg('Ignoring Clients: %s' % str(self.ignore_list))


    def handle_handshake(self, protocol, reserved, info_hash, peer_id):
        client, version = identify_client(peer_id)

        if client in self.ignore_list:
            log.msg('Info: Client %s is in ignore list.' % client)
            self.ignoring = True

        BTProtocol.handle_handshake(self, protocol, reserved, info_hash, peer_id)


    def send_unchoke(self):
        if self.ignoring:
            return

        BTProtocol.send_unchoke(self)

    def handle_request(self, data):
        if self.ignoring:
            log.msg('Info: ignoring request.')
            return

        BTProtocol.handle_request(self, data)

    def send_request(self, index, begin, length):
        if self.ignoring:
            return

        BTProtocol.send_request(self, index, begin, length)


class IgnoreClient(IgnoreClientBase, BTClientProtocol):
    """

    """


class IgnoreClientSvr(IgnoreClientBase, BTServerProtocol):
    """

    """