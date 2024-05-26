from Chain.network import Server, Client


class Node:
    def __init__(self, node_id, host, port, blockchain):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.server = Server(host, port, self)
        self.server.start()
        self.peers = []

    def connect_to_peer(self, host, port):
        client = Client(host, port)
        self.peers.append(client)

    def send_message_to_all(self, message):
        for peer in self.peers:
            peer.send_message(message)

    def receive_message(self, message):
        print(f"Node {self.node_id} received message: {message}")
        self.pre_prepare(message)

    def pre_prepare(self, request):
        self.prepare(request)

    def prepare(self, request):
        self.commit(request)

    def commit(self, request):
        self.blockchain.add_block(request)

class ClientNode:
    def __init__(self, client_id, pbft):
        self.client_id = client_id
        self.pbft = pbft

    def send_request(self, request):
        self.pbft.broadcast_request(request)
