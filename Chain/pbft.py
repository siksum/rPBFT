from abc import ABC, abstractmethod
from node import PrimaryNode, ClientNode
from typing import List
from view import ViewChange
import time

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
    def __init__(self):
        self.current_view: int = 0
        self.view_change_requests: List[ViewChange] = []
        self.timeout_base: float = 5.0
        self.current_timeout: float = self.timeout_base

    def request_view_change(self, node_id: int):
        while True:
            new_view = self.current_view + 1
            view_change = ViewChange(node_id)
            self.view_change_requests.append(view_change)
            self.broadcast_view_change(view_change)
            
            time.sleep(self.current_timeout)

            if self.check_view_change_agreement(new_view):
                self.start_new_view(new_view)
                break 
            else:
                self.current_timeout *= 2
                
    def check_view_change_agreement(self, new_view: int) -> bool:
        count = sum(1 for vc in self.view_change_requests if vc.new_view == new_view)
        return count >= (2 * self.faulty_nodes_count() + 1)

    def start_new_view(self, new_view: int):
        self.current_view = new_view
        self.current_timeout = self.timeout_base
        print(f"Starting new view: {new_view}")

    def broadcast_view_change(self, view: ViewChange):
        print(f"Broadcasting view change request: {view.current_view}")

    def pre_prepare(self, request, node):
        print(f"Node {node.node_id} pre-prepare stage")
        node.pre_prepared_messages.add(request)
        node.send_message_to_all(f"PREPARE:{request}")

    def prepare(self, request, node):
        print(f"Node {node.node_id} prepare stage")
        node.prepared_messages.add(request)
        node.send_message_to_all(f"COMMIT:{request}")

    def commit(self, request, node):
        print(f"Node {node.node_id} commit stage")
        node.committed_messages.add(request)
        node.blockchain.add_block(request)
        print(f"Node {node.node_id} added block: {request}")

class PBFTNetwork:
    def __init__(self, nodes):
        self.nodes = nodes
        self.consensus = PBFT()
        self.primary_node = PrimaryNode(nodes[0], self, self.consensus)
        self.client_node = None

    def broadcast_request(self, request):
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

    def stop(self):
        for node in self.nodes:
            node.stop()
