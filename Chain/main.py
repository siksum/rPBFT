from Chain.blockchain import Blockchain
from Chain.node import Node, PBFT
import time

class Client:
    def __init__(self, client_id, pbft):
        self.client_id = client_id
        self.pbft = pbft

    def send_request(self, request):
        self.pbft.broadcast_request(request)

if __name__ == "__main__":
    blockchain = Blockchain()
    nodes = [Node(i, blockchain) for i in range(4)]
    pbft = PBFT(nodes)
    pbft.initialize_network()
    client = Client(0, pbft)

    client.send_request("Transaction Data")
    
    time.sleep(2)

    for block in blockchain.chain:
        print(f"Block {block.index} [Hash: {block.hash}]")
    
    is_valid = all(node.validate_chain() for node in nodes)
    print(f"Blockchain valid: {is_valid}")
    
    new_node = Node(4, blockchain)
    pbft.add_node(new_node)
    print(f"New node {new_node.node_id} added and registered.")
