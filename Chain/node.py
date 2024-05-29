import time
from network import Server, Client
from typing import List, Set, Dict, TYPE_CHECKING, Any
from blockchain import Blockchain

if TYPE_CHECKING:
    from pbft import PBFTNetwork, PBFT


class Node:
    def __init__(self, node_id: int, node_tag: str, blockchain: Blockchain, host: str, port: int, consensus_algorithm: object):
        self.node_id: int = node_id
        self.node_tag: str = node_tag
        self.blockchain: Blockchain = blockchain
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
            peer.send_message(str(message))

    def receive_message(self, message: str) -> None:
        print(f"Node {self.node_id} received message: {message}")
        message_dict = eval(message)
        self.consensus_algorithm.handle_message(message_dict, self)
    
    def stop(self):
        self.server.stop()
        for peer in self.peers:
            peer.close()
            



class ClientNode:
    def __init__(self, client_id: int, pbft_network: 'PBFTNetwork', list_of_nodes: List[Node]):
        self.client_node_id: int = client_id
        self.pbft_network: 'PBFTNetwork' = pbft_network
        self.request_messages: Dict[str, Any] = {}
        self.list_of_nodes: List[Node] = list_of_nodes
        self.primary_node: PrimaryNode = self.pbft_network.primary_node

    
    def send_request(self, data: str, timestamp: int):
        request= {
            "stage": "REQUEST",
            "data": data,
            "timestamp": timestamp,
            "client_id": self.client_node_id
        }
        self.request_messages = request
        if self.client_node_id == 0 and self.pbft_network.primary_node is not None:
            print(f"Client Node {self.client_node_id} send request to primary node")
            self.pbft_network.broadcast_request(self.request_messages)

    @property
    def request(self):
        return self.request_messages   

class PrimaryNode:
    def __init__(self, primary_node: Node, pbft_network: 'PBFTNetwork', pbft: 'PBFT'):
        self.primary_node: Node = primary_node
        self.pbft_network: 'PBFTNetwork' = pbft_network
        self.pbft: 'PBFT' = pbft
        self._request: Dict = {}

    def broadcast_pre_prepare_message(self, request):
        print(f"Primary Node {self.primary_node.node_id} broadcasting PRE-PREPARE message")
        self._request = request
        self.pbft.pre_prepare(request, self.primary_node)

    def receive_request(self, request):
        if request not in self.primary_node.processed_messages:
            self.pbft.pre_prepare(request, self.primary_node)
        else:
            print(f"Primary Node {self.primary_node.node_id} already processed request: {request}")
            #client에 문제가 있을때는 어떻게 처리할지 고민해보기 -> view change 해야 하는지?

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        self._request = value
