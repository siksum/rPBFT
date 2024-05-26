from blockchain import Blockchain
from pbft import PBFT, PBFTNetwork
from node import Node, ClientNode
import time

if __name__ == "__main__":
    try:
        blockchain = Blockchain()
        pbft_algorithm = PBFT()

        node1 = Node(1, 'localhost', 5000, blockchain, pbft_algorithm)
        node2 = Node(2, 'localhost', 5001, blockchain, pbft_algorithm)
        node3 = Node(3, 'localhost', 5002, blockchain, pbft_algorithm)

        pbft_network = PBFTNetwork([node1, node2, node3])
        pbft_network.initialize_network()

        client = ClientNode(0, pbft_network)

        client.send_request("Transaction Data")
        
        time.sleep(2)

        for block in blockchain.chain:
            print(f"Block {block.index} [Hash: {block.hash}]")

        is_valid = blockchain.is_chain_valid()
        print(f"Blockchain valid: {is_valid}")

        new_node = Node(4, 'localhost', 5003, blockchain, pbft_algorithm)
        pbft_network.add_node(new_node)
        print(f"New node {new_node.node_id} added and registered.")

    finally:
        pbft_network.stop()
