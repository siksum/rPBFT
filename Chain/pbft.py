from abc import ABC, abstractmethod
from typing import List, Dict, Any, TYPE_CHECKING
import hashlib
import time
from view import ViewChange
from node import PrimaryNode, ClientNode
import random

if TYPE_CHECKING:
    from node import Node

class ConsensusAlgorithm(ABC):
    @abstractmethod
    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
        pass

    # @abstractmethod
    # def request_view_change(self, node_id: int, new_view: int) -> None:
    #     pass

    @abstractmethod
    def pre_prepare(self, request: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def prepare(self, pre_prepare_message: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        pass

    # @abstractmethod
    # def handle_view_change(self, message: Dict[str, Any], node: 'Node') -> None:
    #     pass
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
        
        self.pre_prepare_archive: List[Dict[str, Any]] = []
        self.count_of_prepared = 0
        
        self.prepare_archive: List[Dict[str, Any]] = []
        self.count_of_prepared = 0
        
        self.commit_archive: List[Dict[str, Any]] = []
        self.count_of_committed = 0
        
    def set_nodes(self, nodes: List['Node']) -> None:
        self.nodes = nodes

    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
            if node.is_primary:
                node.last_primary_message_time = int(time.time())

            stage = message["stage"]
            if stage == "PRE-PREPARE" and node.is_primary == False: #prepare stage 시작 직전
                node.pre_prepare_messages_archive.append(message)
                if node.node_tag == "fault":
                    return
                self.prepare(message, node)
                    
            elif stage == "PREPARE":
                node.prepare_messages_archive.append(message)
                self.pre_prepare_archive.append(message)

                if node.node_tag == "fault":
                    return
                
                if node.validate_message(message, self.pre_prepare_archive) is True:
                    self.count_of_prepared += 1
                    correct_prepare = receive_prepare_message(self.count_of_prepared, self.count_of_faulty_nodes)
                    if correct_prepare is True:
                        self.commit(message, node)
                else:
                    print(f"Node {node.node_id} failed to validate prepare message.")
                    return
                    
            elif stage == "COMMIT":
                node.commit_messages_archive.append(message)
                self.prepare_archive.append(message)
                
                if node.node_tag == "fault":
                    return
                
                if node.validate_message(message, self.prepare_archive) is True:
                    self.count_of_committed += 1
                    correct_commit = receive_commit_message(self.count_of_committed, self.count_of_faulty_nodes)
                    if correct_commit is True:
                        self.send_reply_to_client(message, node)
                else:
                    print(f"Node {node.node_id} failed to validate commit message.")
                    return
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
        print(f"Node {node.node_id} pre-prepare stage")
        pre_prepare_message= None
        if node.node_tag == "fault":
            if random.choice([True, False]):
                node.send_message_to_all(pre_prepare_message)
            else:
                time.sleep(node.timeout_base + 1)
                ("randome")
        else:
            request_digest = hashlib.sha256(str(request).encode()).hexdigest()
            pre_prepare_message = {
                "stage": "PRE-PREPARE",
                # "view": self.current_view,
                "seq_num": node.pre_prepare_seqnum,
                "digest": request_digest,
                "data": request,
                "node_id": node.node_id,
                "client_id": request["client_id"]
            }
            if pre_prepare_message not in node.pre_prepared_messages:
                node.pre_prepared_messages.append(pre_prepare_message)
                node.send_message_to_all(pre_prepare_message)
                

    def prepare(self, pre_prepare_message: Dict[str, Any], node: 'Node') -> None:
        print(f"Node {node.node_id} prepare stage")
        pre_prepare_message_digest = hashlib.sha256(str(pre_prepare_message).encode()).hexdigest()
        prepare_message= {
            "stage": "PREPARE",
            # "view": self.current_view,
            "seq_num": node.prepared_seqnum,
            "digest": pre_prepare_message_digest,
            "node_id": node.node_id,
            "client_id": pre_prepare_message["client_id"]
        }
        if prepare_message not in node.prepared_messages:
            node.prepared_messages.append(prepare_message)
            node.send_message_to_all(prepare_message)
            

    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        print(f"Node {node.node_id} commit stage")
        prepare_message_digest = hashlib.sha256(str(prepare_message).encode()).hexdigest()
        
        commit_message = {
            "stage": "COMMIT",
            # "view": prepare_message["view"],
            "seq_num": node.committed_seqnum,
            "digest": prepare_message_digest,
            "node_id": node.node_id,
            "client_id": prepare_message["client_id"]
        }
    
        if prepare_message not in node.committed_messages:
            node.committed_messages.append(prepare_message)
            node.send_message_to_all(commit_message)
          
    def send_reply_to_client(self, commit_message: Dict[str, Any], node: 'Node') -> None:
        print(f"Node {node.node_id} sending reply to client")
        commit_message_digest = hashlib.sha256(str(commit_message).encode()).hexdigest()
        
        reply_message = {
            "stage": "REPLY",
            # "view": commit_message["view"],
            "timestamp": int(time.time()),
            "client_id": commit_message["client_id"],
            "result": "Execution Result",
            "node_id": node.node_id
        }
        
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
        self.right_nodes = [node for node in nodes if node.node_tag == "right"]
        self.faulty_nodes = [node for node in nodes if node.node_tag == "fault"]
        
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
                    node.connect_to_peer(peer.host, peer.port)

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