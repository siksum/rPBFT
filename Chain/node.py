import threading
from Chain.blockchain import Blockchain

class Node:
    def __init__(self, node_id, blockchain):
        self.node_id = node_id
        self.blockchain = blockchain
        self.state = "normal"
        self.peers = []

    def receive_request(self, request):
        self.pre_prepare(request)

    def pre_prepare(self, request):
        self.prepare(request)

    def prepare(self, request):
        self.commit(request)

    def commit(self, request):
        self.blockchain.add_block(request)

    def register_peer(self, peer_node):
        self.peers.append(peer_node)

    def validate_chain(self):
        return self.blockchain.is_chain_valid()

class PBFT:
    def __init__(self, nodes):
        self.nodes = nodes
        self.primary_node = nodes[0]

    def broadcast_request(self, request):
        for node in self.nodes:
            threading.Thread(target=node.receive_request, args=(request,)).start()

    def add_node(self, node):
        for n in self.nodes:
            n.register_peer(node)
        self.nodes.append(node)
    
    def initialize_network(self):
        for node in self.nodes:
            for peer in self.nodes:
                if node.node_id != peer.node_id:
                    node.register_peer(peer)
