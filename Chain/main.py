from blockchain import Blockchain
from pbft import PBFT, PBFTHandler
from node import Node, ClientNode, PrimaryNode
from constant import *
import time
from typing import List

class Test:
    def __init__(self, algorithm, count_of_client_nodes: int, count_of_nodes:int, count_of_faulty_nodes:int, port:int, blocksize:int):
        self.blockchain: Blockchain = Blockchain(blocksize)
        self.pbft_algorithm = algorithm
        
        self.count_of_client_nodes: int = count_of_client_nodes
        self.list_of_client_nodes: List[ClientNode] = []
        
        self.count_of_nodes: int = count_of_nodes
        self.list_of_nodes: List[Node] = []
        
        self.count_of_faulty_nodes: int = count_of_faulty_nodes
        self.port: int = port
    
    def setup_client_nodes(self) -> None:
        for i in range(1, self.count_of_client_nodes + 1):
            client_node = ClientNode(i, self.blockchain, self.list_of_nodes, port=self.port+i)
            self.list_of_client_nodes.append(client_node)
            print(f"Client Node : {client_node.client_node_id}, port: {client_node.port}")

    def setup_nodes(self)-> None:
        for i in range(1, self.count_of_nodes + 1):
            node:Node = Node(self.list_of_client_nodes, 
                             i+self.count_of_client_nodes, 
                             RIGHT, 
                             self.blockchain, 
                             LOCALHOST, 
                             self.port + self.count_of_client_nodes+ i, 
                             self.pbft_algorithm)
            self.list_of_nodes.append(node)
        
        self.primary_node = PrimaryNode(self.list_of_nodes[0], self.pbft_algorithm)
        self.list_of_nodes[0] = self.primary_node
           
        for i in range(1, self.count_of_faulty_nodes + 1):
            faulty_nodes = Node(self.list_of_client_nodes, 
                i+self.count_of_client_nodes+self.count_of_nodes, 
                FAULT, 
                self.blockchain, 
                LOCALHOST, 
                self.port + self.count_of_client_nodes + self.count_of_nodes +i, 
                self.pbft_algorithm)
            self.list_of_nodes.append(faulty_nodes)
        
        print(f"Primary Node: {self.list_of_nodes[0].node_id} is {self.list_of_nodes[0].node_tag}, port: {self.list_of_nodes[0].node.port}")
        for node in self.list_of_nodes[1:]:
            print(f"Node {node.node_id} is {node.node_tag}, port: {node.port}")

    def initialize_network(self) -> None:
        self.pbft_handler = PBFTHandler(self.blockchain, self.pbft_algorithm, self.list_of_nodes)
        print(self.pbft_handler.client_node.client_node_id)
        self.client_id = self.pbft_handler.client_node.client_node_id

        for node in self.list_of_nodes:
            node.client_node = self.list_of_client_nodes
        
        self.pbft_handler.initialize_network()
    
    def send_request(self) -> None:
        self.list_of_client_nodes.send_request("Transaction Data", int(time.time()))
        time.sleep(2)
        
    def print_blockchain(self) -> None:
        for block in self.blockchain.chain:
            print(f"Block {block.index} [Hash: {block.current_block_hash}]")
    
    def check_blockchain_validity(self) -> None:
        is_valid: bool = self.blockchain.is_valid_block(self.blockchain.get_latest_block())
        print(f"Blockchain valid: {is_valid}")

   
    def test_view_change(self) -> None:
        if self.list_of_nodes:
            self.list_of_nodes[0].detect_failure_and_request_view_change()
        # self.pbft_algorithm.request_view_change(1)
        # assert self.pbft_algorithm.current_view == 1, "View Change Failed"
        
if __name__ == "__main__":
    try:
        test = Test(algorithm=PBFT, count_of_client_nodes=2, count_of_nodes=4, count_of_faulty_nodes=1, port=5300, blocksize=10)
        test.setup_client_nodes()
        test.setup_nodes()
        # test.initialize_network()
        # test.send_request()
        # test.print_blockchain()
        # test.check_blockchain_validity()
        
        # test.test_view_change()
    finally:
        if hasattr(test, 'pbft_handler'):
            test.pbft_handler.stop()
