from blockchain import Blockchain
from pbft import PBFT, PBFTNetwork
from node import Node, ClientNode
import time
from typing import List, Dict

class Test:
    def __init__(self, algorithm, count_of_nodes:int, count_of_faulty_nodes:int, port:int):
        self.blockchain = Blockchain()
        self.pbft_algorithm = algorithm
        self.count_of_nodes: int = count_of_nodes
        self.list_of_nodes: List[str] = []
        self.count_of_faulty_nodes: int = count_of_faulty_nodes
        self.port: int = port
        

    def setup_nodes(self):
        for i in range(1, self.count_of_nodes + 1):
            node = Node(i, 'localhost', self.port + i, self.blockchain, self.pbft_algorithm)
            self.list_of_nodes.append(node)

    def initialize_network(self):
        self.pbft_network = PBFTNetwork(self.list_of_nodes)

        self.network_client = ClientNode(0, self.pbft_network, self.list_of_nodes)
        self.pbft_network.client_node = self.network_client

        self.pbft_network.initialize_network()
    
    def send_request(self):
        self.network_client.send_request("Transaction Data")
        time.sleep(2)
        
    def print_blockchain(self):
        for block in self.blockchain.chain:
            print(f"Block {block.index} [Hash: {block.current_block_hash}]")
    
    def check_blockchain_validity(self):
        is_valid = self.blockchain.is_chain_valid()
        print(f"Blockchain valid: {is_valid}")

    def check_count_of_nodes(self):
        assert self.count_of_nodes >= self.count_of_faulty_nodes * 3 + 1, "Count of nodes should be greater than 3f + 1"
    
class View:
    def __init__(self):
        self.view_count = 0
        

        
if __name__ == "__main__":
    try:
        test = Test(algorithm=PBFT(), count_of_nodes=4, count_of_faulty_nodes=1, port=5100)
        test.check_count_of_nodes()
        test.setup_nodes()
        test.initialize_network()
        test.send_request()
        test.print_blockchain()
        test.check_blockchain_validity()

    finally:
       test.pbft_network.stop()
