from typing import List, Dict, Any, TYPE_CHECKING
from Consensus.node import PrimaryNode, ClientNode
from Blockchain.network import Client

if TYPE_CHECKING:
    from Consensus.node import Node
    from Blockchain.blockchain import Blockchain
    
    
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


    # def initialize_network(self) -> None:
    #     for node in self.list_of_total_nodes:
    #         for peer in self.list_of_total_nodes:
    #             if node.node_id != peer.node_id:
    #                 node.peers_list.append({"node_id": peer.node_id, "client": Client(peer.host, peer.port)})
    
    def initialize_network(self) -> None:
        client_map = {peer.node_id: Client(peer.host, peer.port) for peer in self.list_of_total_nodes}

        for node in self.list_of_total_nodes:
            node.peers_list = [{"node_id": peer_id, "client": client} 
                            for peer_id, client in client_map.items() if peer_id != node.node_id]

    
    def stop(self) -> None:
        for node in self.list_of_total_nodes:
            node.stop()