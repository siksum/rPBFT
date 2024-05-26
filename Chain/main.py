from blockchain import Blockchain, PBFT
from node import Node, ClientNode
import time


if __name__ == "__main__":
    blockchain = Blockchain()
    node1 = Node(1, 'localhost', 8000, blockchain)
    node2 = Node(2, 'localhost', 8001, blockchain)
    node3 = Node(3, 'localhost', 8002, blockchain)

    pbft = PBFT([node1, node2, node3])
    pbft.initialize_network()

    client = ClientNode(0, pbft)

    client.send_request("Transaction Data")
    
    time.sleep(2)

    for block in blockchain.chain:
        print(f"Block {block.index} [Hash: {block.hash}]")

    is_valid = blockchain.is_chain_valid()
    print(f"Blockchain valid: {is_valid}")

    new_node = Node(4, 'localhost', 8003, blockchain)
    pbft.add_node(new_node)
    print(f"New node {new_node.node_id} added and registered.")
