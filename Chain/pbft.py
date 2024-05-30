from abc import ABC, abstractmethod
import json
from node import PrimaryNode, ClientNode

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
        node.pre_prepared.append(request)
        processed_request = node.process_request(request)
        serialized_request = json.dumps(processed_request).encode()
        node.send_message_to_all(serialized_request)

    def prepare(self, request, node):
        pass

    def commit(self, commit, node):
        pass



class PBFTNetwork:
    def __init__(self, nodes):
        self.nodes = nodes
        self.consensus = PBFT()
        self.primary_node = PrimaryNode(nodes[0], self, self.consensus)
        self.client_node = None  # ClientNode 초기화는 main 함수에서 처리

    def broadcast_request(self, request):  # 1. request = "Transaction Data"
        if self.client_node and request == self.client_node.request:
            self.primary_node.broadcast_pre_prepare_message(request)

    def add_node(self, node):
        for n in self.nodes:
            n.connect_to_peer(node.host, node.port)
            node.connect_to_peer(n.host, n.port)
        self.nodes.append(node)

    def initialize_network(self):
        for node in self.nodes:
            for peer in self.nodes:
                if node.node_id != peer.node_id:
                    node.connect_to_peer(peer.host, peer.port)
                    node.pbft_network = self


    def stop(self):
        for node in self.nodes:
            node.stop()
