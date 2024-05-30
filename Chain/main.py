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
        count_of_faulty_nodes = 0
        
        if count_of_faulty_nodes != 0:
            f = count_of_faulty_nodes
            m = (f - 1) // 3
            count_of_nodes = 3 * m + 2 * f
            print(f"Total nodes: {count_of_nodes}")
            
            
        for i in range(1, count_of_nodes + 1):
            node = Node(i, 'localhost', 5100 + i, blockchain, pbft_algorithm)
            list_of_nodes.append(node)

        # Initialize PBFT network with nodes
        pbft_network = PBFTNetwork(list_of_nodes)

        # Create client node with node_id = 0 and add it to the network
        network_client = ClientNode(0, pbft_network, list_of_nodes)
        pbft_network.client_node = network_client
        
        # Initialize the network
        pbft_network.initialize_network()
        
        request = {
            "message_type": "Request",
            "client_id": 1,
            "timestamp": time.time(),
            "operation": "Request",
            "seq_num": 0
        }

        # Send a request to the network
        network_client.send_request(request)

        time.sleep(2)

        # Print the blockchain and check if it is valid
        
        print("result after 2 seconds!")
        
        
        for block in blockchain.chain:
            print(f"Block {block.index} [Hash: {block.current_block_hash}]")

        # Check if the blockchain is valid
        is_valid = blockchain.is_chain_valid()
        print(f"Blockchain valid: {is_valid}")

        # # Add a new node to the network
        # new_node = Node(6, 'localhost', 5107, blockchain, pbft_algorithm)
        # pbft_network.add_node(new_node)
        # print(f"New node {new_node.node_id} added and registered.")

    finally:
        pbft_network.stop()
