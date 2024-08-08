from typing import List, Dict, Any, TYPE_CHECKING
import hashlib
import time
from node import PrimaryNode, ClientNode
from abstract import ConsensusAlgorithm
from network import Client

if TYPE_CHECKING:
    from node import Node
    from blockchain import Blockchain
    

class PBFT(ConsensusAlgorithm):
    def __init__(self):
        self.client_node: 'ClientNode' = None
        self.count_of_faulty_nodes: int = 0
        self.nodes: List['Node'] = []
        
        self.sequence_number: int = 0
        self.sent_replies: set = set() 
    
    def set_nodes(self, nodes: List['Node']) -> None:
        self.nodes: List['Node'] = nodes
    
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
        
        prepare_message: Dict[str, Any] = {
            "stage": "PREPARE",
            "view": node.current_view_number,
            "seq_num": pre_prepare_message["seq_num"],
            "digest": pre_prepare_message["digest"],
            "node_id": node.node_id,
        }
        
        if node.processed_prepare_messages == {}:
            node.processed_prepare_messages.update({'node_id_from': node.node_id, 
                                                    'message': prepare_message})
        else:
            return
        node.send_message_to_all(prepare_message)
           
            
    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        
        commit_message: Dict[str, Any] = {
            "stage": "COMMIT",
            "view": prepare_message["view"],
            "seq_num": prepare_message["seq_num"],
            "digest": prepare_message["digest"],
            "node_id": node.node_id,
        }
        
        if node.processed_commit_messages == {}:
            node.processed_commit_messages.update({'node_id_from': node.node_id, 
                                                'message': commit_message})
        else:
            return
        node.send_message_to_all(commit_message)
          
          
    def send_reply_to_client(self, commit_message: Dict[str, Any], node: 'Node') -> None:
        
        reply_message: Dict[str, Any] = {
            "stage": "REPLY",
            "view": commit_message["view"],
            "timestamp": int(time.time()),
            "client_id": node.client_node.client_node_id,
            "result": "Execution Result",
            "digest": commit_message["digest"]
        }
        
        if node.processed_reply_messages == {}:
            node.processed_reply_messages.update({'node_id_from': node.node_id, 
                                                'message': reply_message})
        else:
            return
        node.client_node.receive_reply(reply_message, self.count_of_faulty_nodes)
    
    
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


class PBFTHandler:
    def __init__(self, blockchain: 'Blockchain', pbft_algorithm, client_node: List['ClientNode'], nodes: List['Node']):
        self.blockchain: 'Blockchain' = blockchain
        self.pbft_algorithm = pbft_algorithm
        self.list_of_total_nodes: List['Node'] = nodes
        self.list_of_normal_nodes: List['Node'] = [node for node in nodes if node.is_faulty is False]
        self.list_of_faulty_nodes: List['Node'] = [node for node in nodes if node.is_faulty is True]
        self.client_node: List['ClientNode'] = client_node
        self.primary_node = PrimaryNode(nodes[0], self.pbft_algorithm)

    def send_request_to_primary(self, request: Dict[str, Any]) -> None:
        self.primary_node.receive_request(request)

    def initialize_network(self) -> None:
        for node in self.list_of_total_nodes:
            for peer in self.list_of_total_nodes:
                if node.node_id != peer.node_id:
                    node.peers_list.append({"node_id": peer.node_id, "client": Client(peer.host, peer.port)})
    
    def stop(self) -> None:
        for node in self.list_of_total_nodes:
            node.stop()