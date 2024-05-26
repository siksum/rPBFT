from blockchain import Blockchain
from pbft import PBFT, PBFTNetwork
from node import Node, ClientNode
import time

if __name__ == "__main__":
    try:
        # Setup the blockchain, PBFT algorithm, and nodes
        blockchain = Blockchain()
        pbft_algorithm = PBFT()

        count_of_nodes = 5
        list_of_nodes = []

        for i in range(1, count_of_nodes + 1):
            node = Node(i, 'localhost', 5100 + i, blockchain, pbft_algorithm)
            list_of_nodes.append(node)

        # Initialize PBFT network with nodes
        pbft_network = PBFTNetwork(list_of_nodes)

        # Create client node with node_id = 0 and add it to the network
        client = ClientNode(0, pbft_network)
        pbft_network.client_node = client
        
        # Initialize the network
        pbft_network.initialize_network()

        # Send a request to the network
        client.send_request("Transaction Data")

        time.sleep(2)

        # Print the blockchain and check if it is valid
        for block in blockchain.chain:
            print(f"Block {block.index} [Hash: {block.hash}]")

        # Check if the blockchain is valid
        is_valid = blockchain.is_chain_valid()
        print(f"Blockchain valid: {is_valid}")

        # Add a new node to the network
        new_node = Node(6, 'localhost', 5107, blockchain, pbft_algorithm)
        pbft_network.add_node(new_node)
        print(f"New node {new_node.node_id} added and registered.")

    finally:
        pbft_network.stop()
