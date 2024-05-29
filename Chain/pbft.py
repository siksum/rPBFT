from abc import ABC, abstractmethod
from typing import List, Dict, Any, TYPE_CHECKING
import hashlib
import time
from view import ViewChange
from node import PrimaryNode

if TYPE_CHECKING:
    from node import Node

class ConsensusAlgorithm(ABC):
    @abstractmethod
    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def request_view_change(self, node_id: int, new_view: int) -> None:
        pass

    @abstractmethod
    def pre_prepare(self, request: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def prepare(self, pre_prepare_message: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def handle_view_change(self, message: Dict[str, Any], node: 'Node') -> None:
        pass

class PBFT(ConsensusAlgorithm):
    def __init__(self):
        self.current_view: int = 0
        self.view_change_requests: List[ViewChange] = []
        self.timeout_base: float = 5.0
        self.current_timeout: float = self.timeout_base
        self.nodes: List['Node'] = []

    def set_nodes(self, nodes: List['Node']) -> None:
        self.nodes = nodes

    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
        if str(message) not in node.processed_messages:
            node.processed_messages.add(str(message))
            if node.is_primary:
                node.last_primary_message_time = int(time.time())

            stage = message["stage"]
            if stage == "PREPARE":
                if any(message["data"] in msg for msg in node.pre_prepared_messages):
                    self.prepare(message, node)

            elif stage == "COMMIT":
                if message["data"] in node.prepared_messages:
                    self.commit(message, node)

            elif stage == "VIEW-CHANGE":
                self.handle_view_change(message, node)

            else:
                self.pre_prepare(message, node)

    def request_view_change(self, node_id: int, new_view: int) -> None:
        view_change = ViewChange(node_id)
        view_change.change_view()
        view_change_message = {
            "stage": "VIEW-CHANGE",
            "new_view": new_view,
            "node_id": node_id
        }
        self.view_change_requests.append(view_change)
        self.broadcast_view_change(view_change_message)

        time.sleep(self.current_timeout)
        if self.check_view_change_agreement(new_view):
            self.start_new_view(new_view)
        else:
            self.current_timeout *= 2

    def pre_prepare(self, request: Dict[str, Any], node: 'Node') -> None:
        print(f"Node {node.node_id} pre-prepare stage")
        request_digest = hashlib.sha256(str(request).encode()).hexdigest()
        pre_prepare_message = {
            "stage": "PRE-PREPARE",
            "view": self.current_view,
            "seq_num": node.current_view_number,
            "digest": request_digest,
            "data": request
        }
        node.pre_prepared_messages.add(str(pre_prepare_message))
        node.send_message_to_all(pre_prepare_message)

    def prepare(self, pre_prepare_message: Dict[str, Any], node: 'Node') -> None:
        print(f"Node {node.node_id} prepare stage")
        prepare_message = {
            "stage": "PREPARE",
            "view": pre_prepare_message["view"],
            "seq_num": pre_prepare_message["seq_num"],
            "digest": pre_prepare_message["digest"],
            "node_id": node.node_id
        }
        node.prepared_messages.add(str(prepare_message))
        node.send_message_to_all(prepare_message)

    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        print(f"Node {node.node_id} commit stage")
        commit_message = {
            "stage": "COMMIT",
            "view": prepare_message["view"],
            "seq_num": prepare_message["seq_num"],
            "digest": prepare_message["digest"],
            "node_id": node.node_id
        }
        node.committed_messages.add(str(commit_message))
        node.blockchain.add_block_to_blockchain(commit_message)
        print(f"Node {node.node_id} added block: {commit_message}")

    def handle_view_change(self, message: Dict[str, Any], node: 'Node') -> None:
        new_view = message["new_view"]
        if new_view > self.current_view:
            self.view_change_requests.append(ViewChange(node.node_id))
            if self.check_view_change_agreement(new_view):
                self.start_new_view(new_view)

    def broadcast_view_change(self, view_change_message: Dict[str, Any]) -> None:
        for node in self.nodes:
            node.receive_message(view_change_message)

    def check_view_change_agreement(self, new_view: int) -> bool:
        count = sum(1 for vc in self.view_change_requests if vc.current_view == new_view)
        return count >= (2 * self.faulty_nodes_count() + 1)

    def start_new_view(self, new_view: int) -> None:
        self.current_view = new_view
        self.current_timeout = self.timeout_base
        print(f"Starting new view: {new_view}")
        self.primary_node = self.select_new_primary(new_view)

    def select_new_primary(self, new_view: int) -> 'Node':
        if len(self.nodes) > 0:
            return self.nodes[new_view % len(self.nodes)]
        else:
            raise ValueError("No nodes available to select a new primary.")

    def faulty_nodes_count(self) -> int:
        return (len(self.nodes) - 1) // 3

class PBFTNetwork:
    def __init__(self, nodes: List['Node']):
        self.nodes = nodes
        self.consensus = PBFT()
        self.consensus.set_nodes(self.nodes)
        self.primary_node = PrimaryNode(nodes[0], self, self.consensus)
        self.client_node = None

    def broadcast_request(self, request: Dict[str, Any]) -> None:
        if self.client_node and request == self.client_node.request:
            self.primary_node.broadcast_pre_prepare_message(request)

    def add_node(self, node: 'Node') -> None:
        for n in self.nodes:
            n.connect_to_peer(node.host, node.port)
            node.connect_to_peer(n.host, n.port)
        self.nodes.append(node)
        self.consensus.set_nodes(self.nodes)  # 새 노드를 추가할 때 PBFT 인스턴스에 갱신

    def initialize_network(self) -> None:
        for node in self.nodes:
            for peer in self.nodes:
                if node.node_id != peer.node_id:
                    node.connect_to_peer(peer.host, peer.port)

    def stop(self) -> None:
        for node in self.nodes:
            node.stop()
