import time
from network import Server, Client
from typing import List, Set

class Node:
    def __init__(self, node_id: int, host: str, port: int, consensus_algorithm: object):
        self.node_id: int = node_id
        self.host: str = host
        self.port: int = port
        self.consensus_algorithm: object = consensus_algorithm
        self.server = Server(host, port, self)
        self.server.start()
        self.peers: List[Client] = []
        
        self.processed_messages: Set[str] = set()
        self.pre_prepared_messages: Set[str] = set()
        self.prepared_messages: Set[str] = set()
        self.committed_messages: Set[str] = set()
        
        self.is_primary: bool = False  
        self.last_primary_message_time: int = int(time.time())
        self.current_view_number: int = 0 


    def monitor_primary(self) -> None:
        while True:
            if self.is_primary:
                continue
            if int(time.time()) - self.last_primary_message_time > self.consensus_algorithm.timeout_base:
                self.detect_failure_and_request_view_change()
            time.sleep(1)
            
    def detect_failure_and_request_view_change(self)-> None:
        print(f"Node {self.node_id} detected failure and is requesting view change.")
        new_view = self.current_view_number + 1
        self.consensus_algorithm.request_view_change(self.node_id, new_view)

    def connect_to_peer(self, host: str, port: int) -> None:
        client = Client(host, port)
        self.peers.append(client)

    def send_message_to_all(self, message: str) -> None:
        for peer in self.peers:
            peer.send_message(message)

    def receive_message(self, message: str) -> None:
        print(f"Node {self.node_id} received message: {message}")
        if message not in self.processed_messages:
            self.processed_messages.add(message)
            if self.is_primary:
                self.last_primary_message_time = int(time.time())

            if message.startswith("PRE-PREPARE:"):
                request = message[len("PRE-PREPARE:"):]
                self.pre_prepared_messages.add(request)
                self.send_message_to_all(f"PREPARE:{request}")
            
            elif message.startswith("PREPARE:"):
                request = message[len("PREPARE:"):]
                if any(request in msg for msg in self.pre_prepared_messages):
                    self.consensus_algorithm.prepare(request, self)
                    self.send_message_to_all(f"COMMIT:{request}")

            elif message.startswith("COMMIT:"):
                request = message[len("COMMIT:"):]
                if request in self.prepared_messages:
                    self.consensus_algorithm.commit(request, self)

            elif message.startswith("VIEW_CHANGE:"):
                self.consensus_algorithm.handle_view_change(message, self)

            else:
                self.consensus_algorithm.pre_prepare(message, self)
                self.send_message_to_all(f"PREPARE:{message}")

    def process_request(self, message):
        if message not in self.processed_messages:
            self.processed_messages.add(message)
            self.consensus_algorithm.pre_prepare(message, self)
            self.send_message_to_all(f"PREPARE:{message}")

    def process_prepare(self, request):
        if request not in self.prepared_messages:
            if request in self.pre_prepared_messages:
                self.prepared_messages.add(request)
                self.consensus_algorithm.prepare(request, self)
                self.send_message_to_all(f"COMMIT:{request}")

    def process_commit(self, request):
        if request not in self.committed_messages:
            if request in self.prepared_messages:
                self.committed_messages.add(request)
                self.consensus_algorithm.commit(request, self)

    def stop(self):
        self.server.stop()
        for peer in self.peers:
            peer.close()



class ClientNode:
    def __init__(self, client_id, pbft_network, list_of_nodes):
        self.client_node_id = client_id
        self.pbft_network = pbft_network
        self._request = None
        self.list_of_nodes = list_of_nodes
        self.primary_node = self.pbft_network.primary_node

    def send_request(self, request):
        self._request = request
        if self.client_node_id == 0 and self.pbft_network.primary_node is not None:
            print(f"Client Node {self.client_node_id} send request to primary node")
            self.pbft_network.broadcast_request(request)

    @property
    def request(self):
        return self._request


class PrimaryNode:
    def __init__(self, primary_node, pbft_network, pbft):
        self.node = primary_node
        self.pbft_network = pbft_network
        self.pbft = pbft
        self._request = None

    def broadcast_pre_prepare_message(self, request):
        print(f"Primary Node {self.node.node_id} broadcasting pre-prepare message")
        self._request = request
        self.pbft.pre_prepare(request, self.node)

    def receive_request(self, request):
        if request not in self.node.processed_messages:
            self.node.process_request(request)
            self.pbft.pre_prepare(request, self.node)
        self.pbft.pre_prepare(request, self.node)

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        self._request = value
