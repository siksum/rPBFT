import threading
import time
from typing import List, Dict, TYPE_CHECKING, Any
from blockchain import Blockchain
from constant import *
from network import Server

if TYPE_CHECKING:
    from pbft import PBFTHandler, PBFT
    from network import Server, Client

def check_timeout(timer_start, timebase) :
    time_diff = time.time() - timer_start
    if time_diff > timebase:
        return False
    else:
        return True

class Node:
    def __init__(self, client_node: 'ClientNode', node_id: int, is_faulty: bool, blockchain: Blockchain, host: str, port: int, consensus_algorithm):
        self.client_node: 'ClientNode' = client_node
        self.primary_node: 'PrimaryNode' = None
        self.node_id: int = node_id
        self.is_primary: bool = False
        self.is_faulty: bool = is_faulty  
        self.blockchain: Blockchain = blockchain
        self.host: str = host
        self.port: int = port
        self.consensus_algorithm = consensus_algorithm
        
        self.server = Server(host, port, self)
        self.server.start()
        self.peers: List[Client] = []
        self.peers_list: List[Dict[str, Any]] = []
        
        self.processed_pre_prepare_messages: Dict[str, Any] = {}
        self.processed_prepare_messages: Dict[str, Any] = {}
        self.processed_commit_messages: Dict[str, Any] = {}
        self.processed_reply_messages: Dict[str, Any] = {}
        
        self.received_request_messages: Dict[str, Any] = {}
        self.received_pre_prepare_messages: List[Dict[str, Any]] = []
        self.received_prepare_messages: List[Dict[str, Any]] = []
        self.received_commit_messages: List[Dict[str, Any]] = []
        
        self.current_view_number: int = 1
        self.current_sequence_number: int = 0

        self.processed_view_change_messages: Dict[str, Any] = {}
        self.processed_new_view_messages: Dict[str, Any] = {}
        
        self.received_view_change_messages: List[Dict[str, Any]] = []
        self.receive_new_view_messages: List[Dict[str, Any]] = []
        
        self.view_change_timer: threading.Timer = None
        self.view_change_timeout_base: float = 2.0
        
    def detect_failure_and_request_view_change(self)-> None:
        new_view = self.current_view_number + 1
        self.consensus_algorithm.request_view_change(self.node_id, new_view)


    
    def send_message_to_all(self, message) -> None:
        for peer in self.peers_list:
            peer["client"].send_message(str(message))
    
    def view_change_callback(self) -> None:
        self.consensus_algorithm.view_change(self)
        self.view_change_timer.cancel()
            
    def receive_message(self, message) -> None:
        # 노드 입장에서 None 메시지 받았을때는 타이머 꺼질때까지 아무것도 안해도 됨.
        if message == "None":
            return
        
        print(f"[Recieve] Node: {self.node_id}, ", end="")
        message_dict = eval(message)
        if message_dict.get('stage') == "REQUEST":
            # request 메시지 받으면 타이머 켬. 시간제한 2초.
            # threading.Timer -> 제한시간동안 아무것도 안하면 2번째 인자에 들어간 함수가 실행됨.
            self.view_change_timer = threading.Timer(self.view_change_timeout_base, lambda: self.view_change_callback())
            self.view_change_timer.start()
            if self.received_request_messages == {}:
                self.received_request_messages = message_dict
                print(f"stage: {message_dict.get('stage')}, from: Client {message_dict.get('client_id')}")
            else:
                return
        print(f"stage: {message_dict.get('stage')}, from: Node {message_dict.get('node_id')}")
        self.consensus_algorithm.handle_message(message_dict, self)
    
    def validate_message(self, request, received_prepare_messages):
        for received_prepare_message in received_prepare_messages:
            if (received_prepare_message['message']['seq_num'] == request['seq_num'] and
                    received_prepare_message['message']['digest'] == request['digest']):
                return True

    def stop(self):
        self.server.stop()
        for peer in self.peers:
            peer.close()
            

class ClientNode:
    def __init__(self, client_id: int, blockchain:'Blockchain', nodes: 'Node', port: int) -> None:
        self.client_node_id: int = client_id
        self.blockchain: 'Blockchain' = blockchain
        self.port: int = port
        self.request_messages: Dict[str, Any] = {}
        self.received_replies: List[Dict[str, Any]] = []
        self.count_of_replies: int = 0
        self.nodes: List['Node'] = nodes
        self.primary_node: 'PrimaryNode' = None
        
    def send_request(self, pbft_handler:'PBFTHandler', data: str, timestamp: int):
        request= {
            "stage": "REQUEST",
            "data": data,
            "timestamp": timestamp,
            "client_id": self.client_node_id
        }
        self.request_messages = request
        print(f"[Send] Client Node: {self.client_node_id} -> Primary Node: {self.request_messages}")
        
        for node in self.nodes[1:]:
            node.send_message_to_all(self.request_messages)
        pbft_handler.send_request_to_primary(self.request_messages)


    def receive_reply(self, reply_message: Dict[str, Any], count_of_faulty_nodes) -> None:
        if self.nodes[self.client_node_id].view_change_timer:
            self.nodes[self.client_node_id].view_change_timer.cancel()
        self.count_of_replies += 1
        self.received_replies.append(reply_message)
        print(f"[Recieve] Client Node: {self.client_node_id} received reply: {reply_message}")
        
        if self.count_of_replies >= count_of_faulty_nodes + 1:
            for node in self.nodes:
                if node.view_change_timer:
                    node.view_change_timer.cancel()            
            
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
        self.pbft: 'PBFT' = pbft

    def receive_request(self, request):
        print(f"[Recieve] Primary Node: {self.node_id}, content: {request}")
        
        if self.node.is_faulty is True:
            self.node.send_message_to_all(None)
        else:
            self.node.received_request_messages['node_id_to'] = self.node_id
            self.node.received_request_messages['node_id_from'] = request['client_id']
            self.node.received_request_messages['message'] = request
            
            self.pbft.pre_prepare(request, self.node)
        
        
    # def call_pre_prepare(self, request):
    #     self.pbft.pre_prepare(request, self.node)

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        self._request = value