__author__ = 'wallsr'


class CounterProtocol():
    def __init__(self):
        self.connected_peers = []
        self.new_peers = []

    def send_new_clients(self, IP):
        #send the ping
        socket.send(...)

        #they are no longer new peers,
        #so clear the list
        self.new_peers = []

    def receive_message(self, IP, message):
        if IP not in self.connected_peers:
            self.new_peers.append(IP)

        if message == "ping":
            self.receive_ping(IP)
        elif message == "hello":
            self.connected_peers.append(IP)
        elif message == "goodbye":
            self.connected_peers.remove(IP)


