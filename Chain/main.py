from blockchain import Blockchain
from pbft import PBFT, PBFTNetwork
from node import Node, ClientNode
import time

if __name__ == "__main__":
    try:
        #Setup the blockchain, PBFT algorithm, and nodes
        blockchain = Blockchain()
        pbft_algorithm = PBFT()
        
        count_of_nodes = 3
        list_of_nodes = []
        
        for i in range(count_of_nodes):
            node = Node(i, 'localhost', 5000 + i, blockchain, pbft_algorithm)
            list_of_nodes.append(node)

        pbft_network = PBFTNetwork(list_of_nodes)
        client = ClientNode(0, pbft_network)
        
        #Initialize the network
        pbft_network.initialize_network()

        #Send a request to the network
        client.send_request("Transaction Data")
        
        time.sleep(2)

        #Print the blockchain and check if it is valid
        for block in blockchain.chain:
            print(f"Block {block.index} [Hash: {block.hash}]")

        #Check if the blockchain is valid
        is_valid = blockchain.is_chain_valid()
        print(f"Blockchain valid: {is_valid}")

        #Add a new node to the network
        new_node = Node(4, 'localhost', 5003, blockchain, pbft_algorithm)
        pbft_network.add_node(new_node)
        print(f"New node {new_node.node_id} added and registered.")

    finally:
        pbft_network.stop()
