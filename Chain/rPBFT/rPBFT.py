from typing import List, Dict, Any, TYPE_CHECKING
from node import PrimaryNode, ClientNode
from pbft import PBFT, PBFTHandler
import time
import hashlib

if TYPE_CHECKING:
    from node import Node
    from blockchain import Blockchain

class rPBFT():
    def __init__(self) -> None:
        self.client_node: 'ClientNode' = None
        self.count_of_faulty_nodes: int = 0
        self.nodes: List['Node'] = []
        self.pbft_handler: 'PBFTHandler' = None
        
        self.sequence_number: int = 0
        self.sent_replies: set = set()
        
        self.sharing_faulty_data_count: int = 4
        self.count_of_top_priorities: int = 0
        self.nodes_to_send_fault_data: Dict[str, Any] = {}
    
    def initialize_memory(self, node: 'Node') -> None:
        node.processed_pre_prepare_messages = {}
        node.processed_prepare_messages = {}
        node.processed_commit_messages = {}
        node.processed_reply_messages = {}
        node.processed_view_change_messages = {}
        node.processed_new_view_messages = {}
        
        node.received_pre_prepare_messages = []
        node.received_prepare_messages = []
        node.received_commit_messages = []
        
        node.received_view_change_messages = []
        node.receive_new_view_messages = []   
        node.new_view_counter = False   
         
    def check_fault_data(self) -> bool:
        for node in self.nodes:
            if not node.fault_data:
                return False
            else:
                return True
        
    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
        if message["stage"] == "PRE-PREPARE":
            node.received_pre_prepare_messages.append({'node_id_to' : node.node_id, 'node_id_from': message['node_id'], 'message': message})
            if node.is_faulty is True:
                return
            
            self.prepare(message, node)
            
        elif message["stage"] == "PREPARE":
            node.received_prepare_messages.append({'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message})
            if node.is_faulty is True:
                return
            if len(node.received_prepare_messages) >= 2 * self.count_of_faulty_nodes and node.validate_message(message, node.received_prepare_messages) is True:
                self.commit(message, node)
        
        # COMMIT, VIEW-CHANGE, NEW-VIEW 메시지를 받은 노드는 더이상 타이머가 필요없으므로 종료시킴.
        elif message["stage"] == "COMMIT":
            if node.view_change_timer:
                node.view_change_timer.cancel()
                
            node.received_commit_messages.append({'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message})
            if node.is_faulty is True:
                return
            if len(node.received_commit_messages) >= (2 * self.count_of_faulty_nodes + 1) and node.validate_message(message, node.received_commit_messages) is True:
                self.send_reply_to_client(message, node)
                # self.make_fault_data(node)
        
        elif message["stage"] == "FAULT-DATA":
            node.received_fault_data.append({'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'fault_data': message})
            self.calculate_priority(node)
            print("[PRIORITY AFTER FAULT DATA RECEIVE]",node.node_id, node.sum_of_priorities)
                
        elif message["stage"] == "VIEW-CHANGE":
            if node.view_change_timer:
                node.view_change_timer.cancel()
            
            node.received_view_change_messages.append({'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message})
            node.current_view_number = message.get('new_view')
            if node.current_view_number == node.node_id:
                # 여기서 len > 2 * F + 1이 되면 VIEW-CHANGE 메시지 들어올때마다 new view 메시지를 또 보내는 버그가 있었음.
                # new_view_counter를 넣어서 전에 new_view를 보낸 노드는 또 보내지 않도록 하는 방식으로 해결.
                if len(node.received_view_change_messages) >= 2 * self.count_of_faulty_nodes + 1 and node.new_view_counter is False:
                    node.new_view_counter = True
                    self.select_new_primary(node)
                    self.create_new_view(node)
        
        elif message["stage"] == "NEW-VIEW":     
            if node.view_change_timer:
                node.view_change_timer.cancel()       
            node.receive_new_view_messages.append({'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message})
            if message["node_id"] == message["view"]:
                self.initialize_memory(node)
                self.conduct_previous_view_stage(node)

                
    def pre_prepare(self, request: Dict[str, Any], node: 'Node') -> None:
        if node.is_faulty is True:
            return
        
        self.sequence_number += 1   
        request_digest = hashlib.sha256(str(request).encode()).hexdigest()
        pre_prepare_message: Dict[str, Any] = {
            "stage": "PRE-PREPARE",
            "view": node.current_view_number,
            "seq_num": self.sequence_number,
            "digest": request_digest,
            "data": request,
            "node_id": node.node_id
        }
        
        if node.processed_pre_prepare_messages == {} :
            node.processed_pre_prepare_messages.update({'node_id_from': node.node_id, 
                                                        'message': pre_prepare_message})
        else:
            return
        node.send_message_to_all(pre_prepare_message)
            
    def prepare(self, pre_prepare_message: Dict[str, Any], node: 'Node') -> None:
        pre_prepare_message_digest = hashlib.sha256(str(pre_prepare_message).encode()).hexdigest()
        
        prepare_message: Dict[str, Any] = {
            "stage": "PREPARE",
            "view": node.current_view_number,
            "seq_num": pre_prepare_message["seq_num"],
            "digest": pre_prepare_message_digest,
            "node_id": node.node_id,
        }
        
        if node.processed_prepare_messages == {}:
            node.processed_prepare_messages.update({'node_id_from': node.node_id, 
                                                    'message': prepare_message})
        else:
            return
        node.send_message_to_all(prepare_message)
        
            
    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        prepare_message_digest = hashlib.sha256(str(prepare_message).encode()).hexdigest()
        
        commit_message: Dict[str, Any] = {
            "stage": "COMMIT",
            "view": prepare_message["view"],
            "seq_num": prepare_message["seq_num"],
            "digest": prepare_message_digest,
            "node_id": node.node_id,
        }
        
        if node.processed_commit_messages == {}:
            node.processed_commit_messages.update({'node_id_from': node.node_id, 
                                                'message': commit_message})
        else:
            return
        node.send_message_to_all(commit_message)
        
        
    def send_reply_to_client(self, commit_message: Dict[str, Any], node: 'Node') -> None:
        commit_message_digest = hashlib.sha256(str(commit_message).encode()).hexdigest()
        
        reply_message: Dict[str, Any] = {
            "stage": "REPLY",
            "view": commit_message["view"],
            "timestamp": int(time.time()),
            "client_id": node.client_node.client_node_id,
            "result": "Execution Result",
            "node_id": node.node_id,
            "digest": commit_message_digest
        }
        
        if node.processed_reply_messages == {}:
            node.processed_reply_messages.update({'node_id_from': node.node_id, 
                                                'message': reply_message})
        else:
            return
        node.client_node.receive_reply(reply_message, self.count_of_faulty_nodes)
        self.make_fault_data(node)
    
    def make_fault_data(self, node: 'Node') -> None:
        fault_info = [0 for i in range(0, len(self.nodes))]
        node.sum_of_priorities = [0 for i in range(0, len(self.nodes))]
        
        for prepare_message in node.received_prepare_messages:
            if prepare_message['node_id_from'] in [msg['node_id_from'] for msg in node.received_commit_messages]:
                fault_info[prepare_message['node_id_from']-1] += 1

        fault_data: Dict[str, Any] = {
            "stage": "FAULT-DATA", 
            "block_num": node.blockchain.get_latest_block().index,
            "view_num": node.current_view_number,
            "node_id": node.node_id,
            "fault_info": fault_info
        }
        
        if node.processed_fault_data == {}:
            node.processed_fault_data.update({'node_id_from': node.node_id, 
                                            'message': fault_data})
        else:
            return
        
        self.share_fault_data(node, fault_data)
        
    def share_fault_data(self, node: 'Node', fault_data) -> None:
        node.received_fault_data.append({'node_id_to': node.node_id, 'node_id_from': fault_data['node_id'], 'fault_data': fault_data})
        node.count_of_fault_data += 1
        node.send_message_to_particular_node(fault_data, self.sharing_faulty_data_count, node.node_id)
        
    def calculate_priority(self, node: 'Node') -> None:
        sum_of_priorities = [0 for i in range(0, len(self.nodes))]
        for fault_data in node.received_fault_data:
            sum_of_priorities = [x + y for x, y in zip(sum_of_priorities, fault_data['fault_data']['fault_info'])]
        
        if len(node.received_fault_data) > node.count_of_fault_data :
            node.sum_of_priorities = sum_of_priorities
            node.count_of_fault_data = len(node.received_fault_data)
            # print("TIME:", time.time(), "[UPDATED PRIORITY]", node.node_id, node.sum_of_priorities, "FAULT DATA:", node.received_fault_data, "\n")
        else:
            return 
                
    def view_change(self, node: 'Node') -> None:
        view_change_message: Dict[str, Any] = {
            "stage": "VIEW-CHANGE",
            "new_view": node.current_view_number + 1,
            "seq_num": node.current_sequence_number,
            "node_id": node.node_id
        }
        
        node.current_view_number += 1
        if node.processed_view_change_messages == {}:
            node.processed_view_change_messages.update({'node_id_from': node.node_id, 
                                                        'message': view_change_message})
        else:
            return
        print(f"[VIEWCHANGE] Node: {node.node_id} Message: {view_change_message}")
        node.send_message_to_all(view_change_message)
    
    
    def create_new_view(self, node: 'Node') -> None:
        new_view_message: Dict[str, Any] = {
            "stage": "NEW-VIEW",
            "view": node.current_view_number,
            "node_id": node.node_id
        }
        
        if node.processed_new_view_messages == {}:
            node.processed_new_view_messages.update({'node_id_from': node.node_id, 
                                                    'message': new_view_message})
        node.send_message_to_all(new_view_message)
    
        
    def select_new_primary(self, node: 'Node') -> None:
        print(f"Node {node.node_id} is selected as a new primary node")
        original_primary: 'PrimaryNode' = node.primary_node
        new_primary: 'Node' = self.nodes[original_primary.node_id]
        node.primary_node = PrimaryNode(new_primary, self)
        node.primary_node.node.is_primary = True
        original_primary.node.is_primary = False
        
        
    def conduct_previous_view_stage(self, node: 'Node') -> None:
        self.pre_prepare(node.received_request_messages, node)
        
        
    def cancel_all_view_change_timer(self):
        for node in self.nodes:
            if node.view_change_timer:
                node.view_change_timer.cancel()
                print(node.view_change_timer)

    