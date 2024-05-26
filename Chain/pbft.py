from abc import ABC, abstractmethod

class ConsensusAlgorithm(ABC):
    @abstractmethod
    def pre_prepare(self, request, node):
        pass

    @abstractmethod
    def prepare(self, request, node):
        pass

    @abstractmethod
    def commit(self, request, node):
        pass

class PBFT(ConsensusAlgorithm):
    def pre_prepare(self, request, node):
        print(f"Node {node.node_id} pre-prepare stage")
        node.pre_prepared_messages.add(request)
        node.send_message_to_all(f"PREPARE:{request}")
        # self.prepare(request, node)

    def prepare(self, request, node):
        print(f"Node {node.node_id} prepare stage")
        node.prepared_messages.add(request)
        node.send_message_to_all(f"COMMIT:{request}")
        # self.commit(request, node)

    def commit(self, request, node):
        print(f"Node {node.node_id} commit stage")
        node.committed_messages.add(request)
        node.blockchain.add_block(request)
        print(f"Node {node.node_id} added block: {request}")



class PBFTNetwork:
    def __init__(self, nodes):
        self.nodes = nodes
        self.client_node = nodes[0]

    def broadcast_request(self, request):
        self.client_node.receive_message(request)

    def add_node(self, node):
        for n in self.nodes:
            n.connect_to_peer(node.host, node.port)
            node.connect_to_peer(n.host, n.port)
        self.nodes.append(node)

    def initialize_network(self):
        for node in self.nodes:
            print(f"node {node}")
            for peer in self.nodes:
                print(f"peer {peer}")
                if node.node_id != peer.node_id:
                    node.connect_to_peer(peer.host, peer.port)

    def stop(self):
        for node in self.nodes:
            node.stop()

