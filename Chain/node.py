from Chain.network import Server, Client


class Node:
    def __init__(self, node_id, host, port, blockchain, consensus_algorithm):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.consensus_algorithm = consensus_algorithm
        self.server = Server(host, port, self)
        self.server.start()
        self.peers = []
        self.processed_messages = set()
        self.pre_prepared_messages = set()
        self.prepared_messages = set()
        self.committed_messages = set()

    def connect_to_peer(self, host, port):
        client = Client(host, port)
        self.peers.append(client)

    def send_message_to_all(self, message):
        for peer in self.peers:
            peer.send_message(message)

    def receive_message(self, message):
        print(f"Node {self.node_id} received message: {message}")

        if message.startswith("PREPARE:"):
            self.consensus_algorithm.prepare(message[len("PREPARE:"):], self)
        elif message.startswith("COMMIT:"):
            self.consensus_algorithm.commit(message[len("COMMIT:"):], self)
        else:
            self.consensus_algorithm.pre_prepare(message, self)

    def stop(self):
        self.server.stop()
        for peer in self.peers:
            peer.close()



class ClientNode:
    def __init__(self, client_id, pbft_network):
        self.client_id = client_id
        self.pbft_network = pbft_network

    def send_request(self, request):
        self.pbft_network.broadcast_request(request)

