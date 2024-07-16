from blockchain import Blockchain
from pbft import PBFT, PBFTHandler
from node import Node, ClientNode, PrimaryNode
from rPBFT.Reliability import Reliability
from rPBFT.rPBFT import rPBFT

import time
from typing import List
import random
import argparse

LOCALHOST = "localhost"


def argument_parser():
    parser = argparse.ArgumentParser(prog='pbftest', description='Testing PBFT algorithm in user\'s local environment', add_help=True, usage='%(prog)s [options]')
    
    subparser = parser.add_subparsers(dest='algorithm', help='Algorithm to test')
    
    pbft_parser = subparser.add_parser('PBFT', help='Test PBFT algorithm')
    pbft_parser.add_argument('--nodes', type=int, default=100, help='Total number of nodes')
    pbft_parser.add_argument('--faulty_nodes', type=int, default=10, help='Number of faulty nodes')
    pbft_parser.add_argument('--port', type=int, default=5300, help='Port number')
    pbft_parser.add_argument('--blocksize', type=int, default=10, help='Block size')

    rpbft_parser = subparser.add_parser('rPBFT', help='Test rPBFT algorithm')
    rpbft_parser.add_argument('--nodes', type=int, default=100, help='Total number of nodes')
    rpbft_parser.add_argument('--model', type=str, choices=['infant', 'random', 'wearout', 'bathtub'], help='Reliability model')
    rpbft_parser.add_argument('--port', type=int, default=5300, help='Port number')
    rpbft_parser.add_argument('--blocksize', type=int, default=10, help='Block size')
    
    args = parser.parse_args()

    # Check if the condition 3f + 1 <= n is satisfied
    if args.algorithm == 'PBFT' and args.nodes < 3 * args.faulty_nodes + 1:
        parser.error("Total number of nodes must be at least 3 times the number of faulty nodes plus one (3f + 1).")

    return args

class Test:
    def __init__(self, algorithm, count_of_total_nodes:int, count_of_faulty_nodes:int, port:int, blocksize:int):
        self.blockchain: Blockchain = Blockchain(algorithm, blocksize)
        self.pbft_algorithm = algorithm
        self.pbft_handler: PBFTHandler = None
        self.client_node: ClientNode = []
        
        self.count_of_total_nodes: int = count_of_total_nodes
        self.count_of_faulty_nodes: int = count_of_faulty_nodes
        self.count_of_normal_nodes: int = count_of_total_nodes - count_of_faulty_nodes
        self.list_of_nodes: List[Node] = []

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
    pbft_test = None
    rpbft_test = None
    
    
    try:
        args = argument_parser()
        if args.algorithm == 'PBFT':
            pbft_test = Test(algorithm=PBFT(), count_of_total_nodes=args.nodes, count_of_faulty_nodes=args.faulty_nodes, port=args.port, blocksize=10)
            pbft_test.setup_client_nodes()
            pbft_test.setup_nodes()
            pbft_test.setup_faulty_nodes()
            pbft_test.initialize_network()
            pbft_test.send_request()
            pbft_test.print_blockchain()
            
        elif args.algorithm == 'rPBFT':
            generate_faulty_nodes = Reliability(1000, args.nodes)
            print(args.nodes)
            if args.model == 'infant':
                generate_faulty_nodes.generate_infant_mortality(400, 0.7)
                generate_faulty_nodes.get_random_failures(generate_faulty_nodes.infant_mortality)
                print(generate_faulty_nodes.count_of_faulty_nodes)
                
            elif args.model == 'random':
                generate_faulty_nodes.generate_random_failures(0.001)
                generate_faulty_nodes.get_random_failures(generate_faulty_nodes.random_failures)
                
            elif args.model == 'wearout':
                generate_faulty_nodes.generate_wear_out(6.8, 0.1)
                generate_faulty_nodes.get_random_failures(generate_faulty_nodes.wear_out)
                
            elif args.model == 'bathtub':
                generate_faulty_nodes.generate_bathtub_curve()
                generate_faulty_nodes.get_random_failures(generate_faulty_nodes.bathtub_curve)
            
            rpbft_test = Test(algorithm=rPBFT(), count_of_total_nodes=args.nodes, count_of_faulty_nodes=generate_faulty_nodes.count_of_faulty_nodes, port=args.port, blocksize=10)
            rpbft_test.setup_client_nodes()

    finally:
        if hasattr(pbft_test, 'pbft_handler'):
            pbft_test.pbft_handler.stop()
        if hasattr(rpbft_test, 'pbft_handler'):
            rpbft_test.pbft_handler.stop()
