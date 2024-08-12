import threading
import time
from typing import List, Dict, TYPE_CHECKING, Any
from Blockchain.blockchain import Blockchain
from Blockchain.network import Server, Client
import hashlib
import sys

if TYPE_CHECKING:
    from Consensus.pbft_handler import PBFTHandler
    from Blockchain.network import Server, Client


def check_timeout(timer_start: float, timebase: float) :
    time_diff: float = time.time() - timer_start
    return time_diff <= timebase


class Node:
    def __init__(self, client_node: 'ClientNode', node_id: int, is_faulty: bool, blockchain: Blockchain, host: str, port: int, consensus_algorithm) -> None:
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
        print(f"Node {self.node_id} is running.")
        self.peers: List[Client] = []
        self.peers_list: List[Dict[str, Any]] = []
        self.selected_committee_list: List[Dict[str, Any]] = []
        
        self.processed_fault_data: Dict[str, Any] = {}
        self.processed_view_change_messages: Dict[str, Any] = {}
        self.processed_new_view_messages: Dict[str, Any] = {}
        
        self.received_request_messages: Dict[str, Any] = {}
        self.received_pre_prepare_messages: List[Dict[str, Any]] = []
        self.received_prepare_messages: List[Dict[str, Any]] = []
        self.received_commit_messages: List[Dict[str, Any]] = []
        self.received_fault_data: List[Dict[str, Any]] = []
        self.received_view_change_messages: List[Dict[str, Any]] = []
        self.receive_new_view_messages: List[Dict[str, Any]] = []
        
        self.count_of_fault_data: int = 0
        self.sum_of_priorities: List[int] = []
        self.hasFaultyData: bool = True
        self.is_send_reply: bool = False
        
        self.current_view_number: int = 1
        self.current_sequence_number: int = 0
        self.current_block_round: int = self.blockchain.block_round
        
        # self.view_change_timer: threading.Timer = None
        # self.view_change_timeout_base: float = 2.0
        # self.view_change_timer: threading = threading.Timer(self.view_change_timeout_base, lambda: self.view_change_callback())
        # self.view_change_timer.start()
        # self.new_view_counter: bool = False
    
        
    def detect_failure_and_request_view_change(self)-> None:
        new_view: int = self.current_view_number + 1
        self.consensus_algorithm.request_view_change(self.node_id, new_view)
    
     
    def send_message_to_peers(self, message: Dict[str, Any], peers_list) -> None:
        for peer in peers_list:
            peer["client"].send_message(str(message))
    
                        
    def view_change_callback(self) -> None:
        """_summary_
            view change를 실행하고, 그와 동시에 타이머를 끔.
        """
        self.consensus_algorithm.view_change(self)
        self.view_change_timer.cancel()
            
            
    def receive_message(self, message: str) -> None:
        """_summary_
            1. 노드 입장에서 None 메시지 받았을때는 타이머 꺼질때까지 아무것도 안해도 됨.
            2. request 메시지 받으면 타이머 켬.
            3. 제한시간동안 아무것도 안하면 Timer의 2번째 인자에 들어간 함수가 실행됨.
            4. 타이머를 켠 뒤 handle_message 수행
        """
        
        # self.view_change_timer: threading = threading.Timer(self.view_change_timeout_base, lambda: self.view_change_callback())
        # self.view_change_timer.start()
        
        message_dict: Dict = eval(message)
        self.consensus_algorithm.handle_message(message_dict, self)
    
    
    def validate_message(self, request: Dict[str, Any], received_messages: List[Dict[str, Any]]):
        for received_message in received_messages:
            if (received_message['message']['seq_num'] == request['seq_num'] and
                    received_message['message']['digest'] == request['digest']):
                return True


    def stop(self):
        # print(f"Node {self.node_id} is stopping.")
        self.server.stop()
        for peer in self.peers_list:
            peer['client'].close()
            

class ClientNode:
    def __init__(self, client_id: int, blockchain:'Blockchain', nodes: 'Node', port: int) -> None:
        self.client_node_id: int = client_id
        self.blockchain: 'Blockchain' = blockchain
        self.port: int = port
        self.request_messages: List[Dict[str, Any]] = []
        self.digests_of_requests: List[Dict[Any, int]] = []
        self.count_of_replies: List[Dict[int, int]] = []
        self.nodes: List['Node'] = nodes
        self.primary_node: 'PrimaryNode' = None
        self.received_reply_messages: List[Dict[str, Any]] = []
        
        
    def send_request(self, pbft_handler:'PBFTHandler', data: str, timestamp: int):
        request: Dict[str, Any] = {
            "stage": "REQUEST",
            "data": data,
            "timestamp": timestamp,
            "client_id": self.client_node_id
        }
        request_digest = hashlib.sha256(str(request).encode()).hexdigest()
        self.request_messages.append({'request': request, 'digest': request_digest, 'reply_count': 0})
        print(f"[Send] Client Node: {self.client_node_id} -> Primary Node: {request}")
        
        # for node in self.nodes[1:]:
        #     node.send_message_to_all(self.request_messages)
        pbft_handler.send_request_to_primary(request)


    def receive_reply(self, reply_message: Dict[str, Any], count_of_faulty_nodes: int) -> None:
        """_summary_
            1. reply를 받은 노드는 타이머를 종료.
            2. reply가 f + 1개 모이면 모든 노드의 타이머를 끔. 끄지 않을 시 reply 전송 이후에 타이머가 트리거되는 흐름 발생.
            3. 이후 reply를 검증하고 블록 추가.
        """
        # if self.nodes[self.client_node_id].view_change_timer:
        #     self.nodes[self.client_node_id].view_change_timer.cancel()
        
        sys.stdout.flush() #print문에 바이너리 데이터가 포함된 경우가 있어서 추가
        
        current_digest = reply_message['digest']
        current_reqeust = None
        count_of_current_replies = 0
        
        if self.validate_reply(current_digest) is True:
            if len(self.received_reply_messages) == 0:
                print(f"[Recieve] Node: {self.client_node_id}, content: {reply_message}")
                self.received_reply_messages.append(reply_message)
            else:
                is_duplicate = any(reply_message['digest'] == message['digest'] 
                                   and reply_message['node_id'] == message['node_id'] 
                                   for message in self.received_reply_messages)
                
                if not is_duplicate:
                    print(f"[Recieve] Node: {self.client_node_id}, content: {reply_message}")
                    self.received_reply_messages.append(reply_message)
        
        else:
            return
        
        count_of_current_replies = sum(1 for message in self.received_reply_messages if message['digest'] == current_digest)
        for message in self.request_messages:
            if current_digest in message['digest']:
                message['reply_count'] = count_of_current_replies
                current_reqeust = message['request']
                break
        
        
        if count_of_current_replies >= count_of_faulty_nodes + 1:
            # for node in self.nodes:
            #     if node.view_change_timer:
            #         node.view_change_timer.cancel()    
            for block in self.blockchain.chain:
                if block.data == current_reqeust:
                    return
            else:
                print(f"[ADD BLOCK] Client Node added block: {current_reqeust}")
                self.blockchain.add_block_to_blockchain(current_reqeust)
                return True
        return False    
            
        # else:
        #     print(f"Client Node: {self.client_node_id} received {self.count_of_replies} replies.")
            
            
    def validate_reply(self, reply_digest) -> None:
        #reply 메시지와 request 메시지의 digest 같은지 비교 -> reply digest는 request digest이기 때문
        all_keys = []
        for message in self.request_messages:
            all_keys.append(message['digest'])
        
        if reply_digest in all_keys:
            return True
        else:
            return False
    
    
    @property
    def request(self):
        return self.request_messages   
    
    
class PrimaryNode:
    def __init__(self, node: 'Node', pbft_algorithm):
        self.node: 'Node' = node
        self.node_id: int = node.node_id
        self.pbft_algorithm = pbft_algorithm
        self.sequence_number: int = 0


    def receive_request(self, request: Dict[str, Any]):
        print(f"[Recieve] Primary Node: {self.node_id}, content: {request}")
        
        self.node.received_request_messages['node_id_to'] = self.node_id
        self.node.received_request_messages['node_id_from'] = request['client_id']
        self.node.received_request_messages['message'] = request
        
        self.node.current_sequence_number += 1
        
        self.pbft_algorithm.pre_prepare(request, self.node)
        
        
    @property
    def request(self):
        return self._request


    @request.setter
    def request(self, value):
        self._request = value