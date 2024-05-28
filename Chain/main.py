from blockchain import Blockchain
from pbft import PBFT, PBFTNetwork
from node import Node, ClientNode
import time


class Test:
    def __init__(self):
        self.blockchain = Blockchain()
        self.pbft_algorithm = PBFT()

        self.count_of_nodes = 5
        self.list_of_nodes = []
        self.count_of_faulty_nodes = 0

    def setup(self):
        for i in range(1, self.count_of_nodes + 1):
            node = Node(i, 'localhost', 5100 + i, self.blockchain, self.pbft_algorithm)
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

class View:
    def __init__(self):
        self.view_count = 0
        
if __name__ == "__main__":
    try:
        test = Test()
        test.setup()
        test.initialize_network()
        test.send_request()
        test.print_blockchain()
        test.check_blockchain_validity()

    finally:
       test.pbft_network.stop()
