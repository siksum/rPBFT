import time
from network import Server, Client
from typing import List, Set, Dict, TYPE_CHECKING, Any
from blockchain import Blockchain
from constant import *
import random
import threading

if TYPE_CHECKING:
    from pbft import PBFTHandler, PBFT


class Node:
    def __init__(self, client_node: 'ClientNode', node_id: int, node_tag: str, blockchain: Blockchain, host: str, port: int, consensus_algorithm):
        self.client_node: 'ClientNode' = client_node
        self.node_id: int = node_id
        
        self.is_primary: bool = False
        self.is_faulty: bool = False  
        
        self.node_tag: str = node_tag
        self.timeout_base: float = 5.0
        self.blockchain: Blockchain = blockchain
        self.host: str = host
        self.port: int = port
        self.consensus_algorithm = consensus_algorithm
        self.server = Server(host, port, self)
        self.server.start()
        self.peers: List[Client] = []
        
        self.processed_messages: List[Dict[str, Any]] = []
        self.received_request_messages: Dict[str, Any] = {}
        
        self.processed_pre_prepare_messages: Dict[str, Any] = {}
        self.processed_prepare_messages: Dict[str, Any] = {}
        self.processed_commit_messages: Dict[str, Any] = {}
        
        self.received_pre_prepare_messages: Dict[str, Any] = {}
        self.received_prepare_messages: Dict[str, Any] = {}
        self.received_commit_messages: Dict[str, Any] = {}
        
        self.last_primary_message_time: int = int(time.time())
        self.current_view_number: int = 0 
        
        # self.request_messages_archive: List[Dict[str, Any]] = []
        # self.pre_prepare_messages_archive : List[Dict[str, Any]] = []
        # self.prepare_messages_archive : List[Dict[str, Any]] = []
        # self.commit_messages_archive : List[Dict[str, Any]] = []
        # self.reply_messages_archive : List[Dict[str, Any]] = []

    def monitor_primary(self, message) -> None:
        if self.is_primary:
            return
        if message == str(None) or int(time.time()) - self.last_primary_message_time  > int(self.timeout_base):
            self.detect_failure_and_request_view_change()
        else:
            return None
        time.sleep(1)
            
    def detect_failure_and_request_view_change(self)-> None:
        print(f"Node {self.node_id} detected failure and is requesting view change.")
        new_view = self.current_view_number + 1
        self.consensus_algorithm.request_view_change(self.node_id, new_view)

    def connect_to_peer(self, host: str, port: int) -> None:
        client = Client(host, port)
        self.peers.append(client)

    def send_message_to_all(self, message) -> None:
        for peer in self.peers:
            peer.send_message(str(message))
            
    def receive_message(self, message) -> None:
        if self.monitor_primary(message) is None:
            print(f"[Recieve] Node: {self.node_id}, ", end="")
            message_dict = eval(message)
            print(f"stage: {message_dict.get('stage')}, from: Node {message_dict.get('node_id')}")
            # threading.Thread(target=self.consensus_algorithm.handle_message, args=(message_dict, self)).start()
            self.consensus_algorithm.handle_message(message_dict, self)
    
    def validate_message(self, message, message_archive):
        for message_of_stage in message_archive:
            if (message_of_stage['seq_num'] == message['seq_num'] and
                    message_of_stage['digest'] == message['digest']):
                return True
        return False
    
    def faulty_behavior(self):
        faulty_actions = [
            self.send_incorrect_message,
            self.send_duplicate_message,
            self.omit_message,
            self.delay_message
        ]
        action = random.choice(faulty_actions)
        action()

    def send_incorrect_message(self):
        incorrect_message = {
            "stage": "PRE-PREPARE",
            "seq_num": self.pre_prepare_seqnum,
            "digest": "incorrect_digest",
            "data": "incorrect_data",
            "node_id": self.node_id,
            "client_id": "incorrect_client_id"
        }
        self.send_message_to_all(str(incorrect_message))

    def send_duplicate_message(self):
        if self.pre_prepared_messages:
            duplicate_message = self.pre_prepared_messages[0]
            self.send_message_to_all(str(duplicate_message))

    def omit_message(self):
        print(f"Node {self.node_id} is omitting a message")

    def delay_message(self):
        time.sleep(self.consensus_algorithm.timeout_base * 2)
        print(f"Node {self.node_id} is delaying a message")

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
                return
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
        self.node_tag: str = node.node_tag
        self.pbft: 'PBFT' = pbft

    def receive_request(self, request):
        print(f"[Recieve] Primary Node: {self.node_id}, content: {request}")
        self.node.received_request_messages['node_id_to'] = self.node_id
        self.node.received_request_messages['node_id_from'] = request['client_id']
        self.node.received_request_messages['message'] = request
        
        self.pbft.pre_prepare(request, self.node)

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        self._request = value
