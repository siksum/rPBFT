from blockchain import Blockchain
from pbft import PBFT, PBFTNetwork
from node import Node, ClientNode
import time
from typing import List

class Test:
    def __init__(self, algorithm, count_of_nodes:int, count_of_faulty_nodes:int, port:int, blocksize:int):
        self.blockchain: Blockchain = Blockchain(blocksize)
        self.pbft_algorithm = algorithm
        self.count_of_nodes: int = count_of_nodes
        self.list_of_nodes: List[Node] = []
        self.count_of_faulty_nodes: int = count_of_faulty_nodes
        self.port: int = port
        

    def setup_nodes(self)-> None:
        for i in range(1, self.count_of_nodes + 1):
            node:Node = Node(i, "right", self.blockchain, 'localhost', self.port + i, self.pbft_algorithm)
            self.list_of_nodes.append(node)
            
        for i in range(1, self.count_of_faulty_nodes + 1):
            faulty_nodes = Node(i, "fault", self.blockchain, 'localhost', self.port + i, self.pbft_algorithm)
            self.list_of_nodes.append(faulty_nodes)
            

    def initialize_network(self) -> None:
        self.pbft_network = PBFTNetwork(self.list_of_nodes)
        self.network_client = ClientNode(0, self.pbft_network, self.list_of_nodes)
        self.pbft_network.client_node = self.network_client

        self.pbft_network.initialize_network()
    
    def send_request(self) -> None:
        self.network_client.send_request("Transaction Data", int(time.time()))
        time.sleep(2)
        
    def print_blockchain(self) -> None:
        for block in self.blockchain.chain:
            print(f"Block {block.index} [Hash: {block.current_block_hash}]")
    
    def check_blockchain_validity(self) -> None:
        is_valid: bool = self.blockchain.is_valid_block(self.blockchain.get_latest_block())
        print(f"Blockchain valid: {is_valid}")

    def check_count_of_nodes(self) -> None:
        assert self.count_of_nodes >= self.count_of_faulty_nodes * 3 + 1, "Count of nodes should be greater than 3f + 1"

    def test_view_change(self) -> None:
        if self.list_of_nodes:
            self.list_of_nodes[0].detect_failure_and_request_view_change()
        # self.pbft_algorithm.request_view_change(1)
        # assert self.pbft_algorithm.current_view == 1, "View Change Failed"
        
if __name__ == "__main__":
    try:
        test = Test(algorithm=PBFT(), count_of_nodes=4, count_of_faulty_nodes=0, port=5100, blocksize=10)
        test.check_count_of_nodes()
        test.setup_nodes()
        test.initialize_network()
        test.send_request()
        test.print_blockchain()
        # test.check_blockchain_validity()
        
        test.test_view_change()
    finally:
        if hasattr(test, 'pbft_network'):
            test.pbft_network.stop()
