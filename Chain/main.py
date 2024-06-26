from blockchain import Blockchain
from pbft import PBFT, PBFTHandler
from node import Node, ClientNode, PrimaryNode
import time
from typing import List
import random

LOCALHOST = "localhost"

class Test:
    def __init__(self, algorithm, count_of_total_nodes:int, count_of_faulty_nodes:int, port:int, blocksize:int):
        self.blockchain: Blockchain = Blockchain(algorithm, blocksize)
        self.pbft_algorithm = algorithm
        self.pbft_handler: PBFTHandler = None
        self.client_node: ClientNode = []
        self.count_of_total_nodes: int = count_of_total_nodes
        self.list_of_nodes: List[Node] = []
        self.count_of_faulty_nodes: int = count_of_faulty_nodes
        self.pbft_algorithm.count_of_faulty_nodes = count_of_faulty_nodes
        self.port: int = port
    
    def setup_client_nodes(self) -> None:
        """_summary_
            클라이언트 노드를 설정 -> 0번 노드가 클라이언트 노드
        """
        client_node = ClientNode(0, self.blockchain, nodes=self.list_of_nodes, port=self.port)
        self.client_node: ClientNode = client_node

    def setup_nodes(self)-> None:
        """_summary_
            리스트에 노드를 추가하고, primary node를 설정 -> 1번 노드가 primary node
            view change때는 랜덤으로 primary node를 설정
        """
        for i in range(0, self.count_of_total_nodes):
            node:Node = Node(self.client_node, 
                            i+1, 
                            False, 
                            self.blockchain, 
                            LOCALHOST, 
                            self.port + i, 
                            self.pbft_algorithm)
            self.list_of_nodes.append(node)
        
        self.primary_node = PrimaryNode(self.list_of_nodes[0], self.pbft_algorithm)
        self.primary_node.node.is_primary = True
        
        self.pbft_algorithm.nodes = self.list_of_nodes
    
    def setup_faulty_nodes(self) -> None:
        for node in self.list_of_nodes:
            node.primary_node = self.primary_node
        
        random.choice(self.list_of_nodes).is_faulty = True
        
    def initialize_network(self) -> None:
        self.pbft_handler = PBFTHandler(self.blockchain, self.pbft_algorithm, self.client_node, self.list_of_nodes) 
        
        for node in self.list_of_nodes:
            node.client_node = self.client_node
        
        self.pbft_algorithm.count_of_faulty_nodes = len(self.pbft_handler.faulty_nodes)
        self.pbft_handler.initialize_network()
    
    def send_request(self) -> None:
        self.client_node.send_request(self.pbft_handler, "Transaction Data", int(time.time()))        
        # 최종 생성된 체인 확인하는 시간
        time.sleep(3)
        
    def print_blockchain(self) -> None:
        for block in self.blockchain.chain:
            print(f"Block {block.index} [Hash: {block.current_block_hash}]")
    
    def check_blockchain_validity(self) -> None:
        is_valid: bool = self.blockchain.is_valid_block(self.blockchain.get_latest_block())
        print(f"Blockchain valid: {is_valid}")
        
        
if __name__ == "__main__":
    try:
        test = Test(algorithm=PBFT(), count_of_total_nodes=5, count_of_faulty_nodes=1, port=5300, blocksize=10)
        test.setup_client_nodes()
        test.setup_nodes()
        test.setup_faulty_nodes()
        test.initialize_network()
        test.send_request()
        test.print_blockchain()
        
    finally:
        if hasattr(test, 'pbft_handler'):
            test.pbft_handler.stop()
