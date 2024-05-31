from blockchain import Blockchain
from pbft import PBFT, PBFTHandler
from node import Node, ClientNode, PrimaryNode
from constant import *
import time
from typing import List

class Test:
    def __init__(self, algorithm, count_of_nodes:int, count_of_faulty_nodes:int, port:int, blocksize:int):
        self.blockchain: Blockchain = Blockchain(blocksize)
        self.pbft_algorithm = algorithm
        self.pbft_handler: PBFTHandler = None
        
        self.client_node: ClientNode = []
        
        self.count_of_nodes: int = count_of_nodes
        self.list_of_nodes: List[Node] = []
        
        self.count_of_faulty_nodes: int = count_of_faulty_nodes
        self.port: int = port
    
    def setup_client_nodes(self) -> None:
        """_summary_
            클라이언트 노드를 설정 -> 0번 노드가 클라이언트 노드
        """
        client_node = ClientNode(0, self.blockchain, self.list_of_nodes, port=self.port)
        self.client_node = client_node

    def setup_nodes(self)-> None:
        """_summary_
            리스트에 노드를 추가하고, primary node를 설정 -> 1번 노드가 primary node
            view change때는 랜덤으로 primary node를 설정
        """
        for i in range(1, self.count_of_nodes + 1):
            # if i == 1:
            #     node:Node = Node(self.client_node, 
            #                      i, 
            #                      FAULT, 
            #                      self.blockchain, 
            #                      LOCALHOST, 
            #                      self.port + i, 
            #                      self.pbft_algorithm)
            # else:
            node:Node = Node(self.client_node, 
                            i, 
                            RIGHT, 
                            self.blockchain, 
                            LOCALHOST, 
                            self.port + i, 
                            self.pbft_algorithm)
            self.list_of_nodes.append(node)
        
        self.primary_node = PrimaryNode(self.list_of_nodes[0], self.pbft_algorithm)
        self.primary_node.node.is_primary = True
           
        for i in range(1, self.count_of_faulty_nodes + 1):
            faulty_nodes = Node(self.client_node, 
                i+self.count_of_nodes, 
                FAULT, 
                self.blockchain, 
                LOCALHOST, 
                self.port + self.count_of_nodes + i, 
                self.pbft_algorithm)
            self.list_of_nodes.append(faulty_nodes)
    

    def initialize_network(self) -> None:
        self.pbft_handler = PBFTHandler(self.blockchain, self.pbft_algorithm, self.client_node, self.list_of_nodes) 
        
        for node in self.list_of_nodes:
            node.client_node = self.client_node
        
        self.pbft_algorithm.count_of_faulty_nodes = len(self.pbft_handler.faulty_nodes)
        
        self.pbft_handler.initialize_network()
    
    def send_request(self) -> None:
        self.client_node.send_request(self.pbft_handler, "Transaction Data", int(time.time()))
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
        test = Test(algorithm=PBFT(), count_of_nodes=6, count_of_faulty_nodes=1, port=5300, blocksize=10)
        test.setup_client_nodes()
        test.setup_nodes()
        test.initialize_network()
        test.send_request()
        test.print_blockchain()
        # test.check_blockchain_validity()
        
        # test.test_view_change()
    finally:
        if hasattr(test, 'pbft_handler'):
            test.pbft_handler.stop()
