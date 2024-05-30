import time
from network import Server, Client
from typing import List, Set, Dict, TYPE_CHECKING, Any
from blockchain import Blockchain
from constant import *

if TYPE_CHECKING:
    from pbft import PBFTHandler, PBFT


class Node:
    def __init__(self, client_node: 'ClientNode', node_id: int, node_tag: str, blockchain: Blockchain, host: str, port: int, consensus_algorithm):
        self.client_node: 'ClientNode' = client_node
        self.node_id: int = node_id
        self.node_tag: str = node_tag
        self.blockchain: Blockchain = blockchain
        self.host: str = host
        self.port: int = port
        self.consensus_algorithm = consensus_algorithm
        self.server = Server(host, port, self)
        self.server.start()
        self.peers: List[Client] = []
        
        self.processed_messages: List[Dict[str, Any]] = []
        self.pre_prepared_messages: List[Dict[str, Any]] = []
        self.prepared_messages: List[Dict[str, Any]] = []
        self.committed_messages: List[Dict[str, Any]] = []
        
        self.is_primary: bool = False  
        self.last_primary_message_time: int = int(time.time())
        self.current_view_number: int = 0 
        
        self.request_messages_archive: List[Dict[str, Any]] = []
        self.pre_prepare_messages_archive : List[Dict[str, Any]] = []
        self.prepare_messages_archive : List[Dict[str, Any]] = []
        self.commit_messages_archive : List[Dict[str, Any]] = []
        self.reply_messages_archive : List[Dict[str, Any]] = []

        self.pre_prepare_seqnum: int = 0
        self.prepared_seqnum: int = 0
        self.committed_seqnum: int = 0

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
    
        

    def receive_message(self, message) -> None:
        print(f"[Recieve] Node: {self.node_id}, ", end="")
        message_dict = eval(message)
        print(f"stage: {message_dict.get('stage')}, from: Node {message_dict.get('node_id')}")
        
        # else:
        #     self.request_messages_archive.append(message_dict)
        
        # if message_hash in self.processed_messages:
        #     print(f"Node {self.node_id} already processed message: {message}")
        #     return None
        
        self.consensus_algorithm.handle_message(message_dict, self)
    
    def validate_message(self, message, message_archive):
        for message_of_stage in message_archive:
            if (message_of_stage['seq_num'] == message['seq_num'] and
                    message_of_stage['digest'] == message['digest']):
                return True
        return False
    
    def stop(self):
        self.server.stop()
        for peer in self.peers:
            peer.close()
            

class ClientNode:
    def __init__(self, client_id: int, blockchain:'Blockchain', list_of_nodes: List[Node], port: int) -> None:
        self.client_node_id: int = client_id
        self.blockchain: 'Blockchain' = blockchain
        self.port: int = port
        self.request_messages: Dict[str, Any] = {}
        self.list_of_nodes: List[Node] = list_of_nodes
        self.received_replies: List[Dict[str, Any]] = []
        self.count_of_replies: int = 0
        
    
    def send_request(self, pbft_handler:'PBFTHandler', data: str, timestamp: int):
        request= {
            "stage": "REQUEST",
            "data": data,
            "timestamp": timestamp,
            "client_id": self.client_node_id
        }
        self.request_messages = request
        
        print(f"[Send] Client Node: {self.client_node_id} -> Primary Node: {request}")
        pbft_handler.send_request_to_primary(self.request_messages)
        

    def receive_reply(self, reply_message: Dict[str, Any], count_of_faulty_nodes) -> None:
        self.count_of_replies += 1
        self.received_replies.append(reply_message)
        print(f"[Recieve] Client Node: {self.client_node_id} received reply: {reply_message}")
        
        if self.count_of_replies >= count_of_faulty_nodes + 1:
            if self.validate_reply(reply_message, self.received_replies) is True:
                self.blockchain.add_block_to_blockchain(reply_message)
                print(f"Client Node added block: {reply_message}")
        else:
            print(f"Client Node: {self.client_node_id} received {self.count_of_replies} replies.")
    
    def validate_reply(self, reply_message: Dict[str, Any], received_replies) -> None:
        for message_of_stage in received_replies:
            if message_of_stage['digest'] == reply_message['digest']:
                return True
        return False
    
    @property
    def request(self):
        return self.request_messages   

class PrimaryNode:
    def __init__(self, node: Node, pbft: 'PBFT'):
        self.node = node
        self.node_id: int = node.node_id
        self.node_tag: str = PRIMARY
        self.pbft: 'PBFT' = pbft

    def receive_request(self, request):
        print(f"[Recieve] Primary Node: {self.node_id}, content: {request}")
        self.node.pre_prepared_messages.append(request)
        self.pbft.pre_prepare(request, self.node)

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        self._request = value
