from typing import List, Dict, Any, TYPE_CHECKING
import hashlib
import time
from view import ViewChange
from node import PrimaryNode, ClientNode
from abstract import ConsensusAlgorithm
from network import Client

if TYPE_CHECKING:
    from node import Node


def receive_pre_prepare_message(hash_data, message) -> bool:
    if hash_data == hashlib.sha256(str(message).encode()).hexdigest():
        return True
    return False

def receive_prepare_message(count: int, faulty_nodes) -> bool:
    if count >= (2 * faulty_nodes):
        return True
    return False

def receive_commit_message(count: int, faulty_nodes) -> bool:
    if count >= (2 * faulty_nodes + 1):
        return True
    return False

class PBFT(ConsensusAlgorithm):
    def __init__(self):
        self.current_view: int = 0
        self.view_change_requests: List[ViewChange] = []
        self.client_node: 'ClientNode' = None
        self.count_of_faulty_nodes: int = 0
        self.nodes: List['Node'] = []
        
        self.count_of_prepared = 0
        self.count_of_prepared = 0
        self.count_of_committed = 0
        
        self.sequence_number = 0
        self.sent_replies: set = set() 
        
    def set_nodes(self, nodes: List['Node']) -> None:
        self.nodes = nodes

    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
        # if node.is_primary:
        #     node.last_primary_message_time = int(time.time())

        if message["stage"] == "PRE-PREPARE":  #prepare stage 시작 직전
            node.received_pre_prepare_messages.append({'node_id_to' : node.node_id, 'node_id_from': message['node_id'], 'message': message})
            if node.is_faulty is True:
                return
            self.prepare(message, node)
            
        elif message["stage"] == "PREPARE":
            node.received_prepare_messages.append({'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message})
            if node.is_faulty is True:
                return
            self.commit(message, node)

            # if len(node.received_prepare_messages) >= 2 * self.count_of_faulty_nodes and node.validate_message(message, node.received_prepare_messages) is True:
            #     self.commit(message, node)
                
        elif message["stage"] == "COMMIT":
            node.received_commit_messages.append({'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message})
            if node.is_faulty is True:
                return
            self.send_reply_to_client(message, node)
            # if len(node.received_commit_messages) >= (2 * self.count_of_faulty_nodes + 1) and node.validate_message(message, node.received_commit_messages) is True:
            #     print(f"Node {node.node_id}, {len(node.received_commit_messages)}")
            #     self.send_reply_to_client(message, node)
                
        # elif stage == "VIEW-CHANGE":
        #     self.handle_view_change(message, node)

    # def request_view_change(self, node_id: int, new_view: int) -> None:
    #     view_change = ViewChange(node_id)
    #     view_change.change_view()
    #     view_change_message = {
    #         "stage": "VIEW-CHANGE",
    #         "new_view": new_view,
    #         "node_id": node_id
    #     }
    #     self.view_change_requests.append(view_change)
    #     self.broadcast_view_change(view_change_message)

    #     time.sleep(self.current_timeout)
    #     if self.check_view_change_agreement(new_view):
    #         self.start_new_view(new_view)
    #     else:
    #         self.current_timeout *= 2

    def pre_prepare(self, request: Dict[str, Any], node: 'Node') -> None:
        self.sequence_number += 1   
        request_digest = hashlib.sha256(str(request).encode()).hexdigest()
        pre_prepare_message = {
            "stage": "PRE-PREPARE",
            # "view": self.current_view,
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
        
        prepare_message= {
            "stage": "PREPARE",
            # "view": self.current_view,
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
        
        commit_message = {
            "stage": "COMMIT",
            # "view": prepare_message["view"],
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
        reply_message = {
            "stage": "REPLY",
            # "view": commit_message["view"],
            "timestamp": int(time.time()),
            "client_id": node.client_node.client_node_id,
            "result": "Execution Result",
            "node_id": node.node_id
        }
        if node.processed_reply_messages == {}:
            node.processed_reply_messages.update({'node_id_from': node.node_id, 
                                                'message': reply_message})
        else:
            return
        node.client_node.receive_reply(reply_message, self.count_of_faulty_nodes)
        
    # def handle_view_change(self, message: Dict[str, Any], node: 'Node') -> None:
    #     new_view = message["new_view"]
    #     if new_view > self.current_view:
    #         self.view_change_requests.append(ViewChange(node.node_id))
    #         if self.check_view_change_agreement(new_view):
    #             self.start_new_view(new_view)

    # def broadcast_view_change(self, view_change_message: Dict[str, Any]) -> None:
    #     for node in self.nodes:
    #         node.receive_message(view_change_message)

    # def check_view_change_agreement(self, new_view: int) -> bool:
    #     count = sum(1 for vc in self.view_change_requests if vc.current_view == new_view)
    #     return count >= (2 * self.faulty_nodes_count() + 1)

    # def start_new_view(self, new_view: int) -> None:
    #     self.current_view = new_view
    #     self.current_timeout = self.timeout_base
    #     print(f"Starting new view: {new_view}")
    #     if self.nodes:
    #         self.primary_node = self.select_new_primary(new_view)
    #         print(f"New primary selected: Node {self.primary_node.node_id}")
    #     else:
    #         print("Error: No nodes available to select a new primary.")

    # def select_new_primary(self, new_view: int) -> 'Node':
    #     if len(self.nodes) > 0:
    #         return self.nodes[new_view % len(self.nodes)]
    #     else:
    #         raise ValueError("No nodes available to select a new primary.")



class PBFTHandler:
    def __init__(self, blockchain, consensus, client_node: List['ClientNode'], nodes: List['Node']):
        self.blockchain = blockchain
        self.consensus = consensus
        
        self.nodes: List['Node'] = nodes
        self.right_nodes = [node for node in nodes if node.is_faulty is False]
        self.faulty_nodes = [node for node in nodes if node.is_faulty is True]
        
        self.check_count_of_nodes()
    
        self.client_node: List['ClientNode'] = client_node
        self.primary_node = PrimaryNode(nodes[0], self.consensus)
        
    def check_count_of_nodes(self) -> None:
        if self.faulty_nodes is None:
            assert len(self.nodes) >= 3, "Count of nodes should be greater than 3"
        else:
            assert len(self.nodes) >= len(self.faulty_nodes) * 3 + 1, "Count of nodes should be greater than 3f + 1"

    def send_request_to_primary(self, request: Dict[str, Any]) -> None:
        self.primary_node.receive_request(request)

    def add_node(self, node: 'Node') -> None:
        for n in self.nodes:
            n.connect_to_peer(node.host, node.port)
            node.connect_to_peer(n.host, n.port)
        self.nodes.append(node)

    def initialize_network(self) -> None:
        for node in self.nodes:
            for peer in self.nodes:
                if node.node_id != peer.node_id:
                    node.peers_list.append({"node_id": peer.node_id, "client": Client(peer.host, peer.port)})

    def select_random_primary(self) -> None:
        original_primary = self.primary_node.node
        self.primary_node = PrimaryNode(self.nodes[0], self.consensus)
        self.primary_node.node.is_primary = True
        original_primary.is_primary = False
        self.nodes.append(original_primary)
        self.nodes.remove(self.primary_node.node)
    
    def stop(self) -> None:
        for node in self.nodes:
            node.stop()