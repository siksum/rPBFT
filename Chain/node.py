from network import Server, Client


class Node:
    def __init__(self, node_id, host, port, blockchain, consensus_algorithm):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.consensus_algorithm = consensus_algorithm
        self.server = Server(host, port, self)
        self.server.start()
        self.peers = []
        self.processed_messages = set()
        self.pre_prepared_messages = set()
        self.prepared_messages = set()
        self.committed_messages = set()

    def connect_to_peer(self, host, port):
        client = Client(host, port)
        self.peers.append(client)

    def send_message_to_all(self, message):
        for peer in self.peers:
            peer.send_message(message)

    def receive_message(self, message):
        print(f"Node {self.node_id} received message: {message}")
        message_type = message.get('type')
        if message_type == 'request':
            self.handle_request(message)
        elif message_type == 'pre-prepare':
            self.handle_pre_prepare(message)
        elif message_type == 'prepare':
            self.handle_prepare(message)
        elif message_type == 'commit':
            self.handle_commit(message)
        elif message_type == 'view-change':
            self.handle_view_change(message)
        elif message_type == 'new-view':
            self.handle_new_view(message)
        else:
            print(f"Node {self.node_id} received unknown message type: {message_type}")

    def process_request(self, message):
        if message not in self.processed_messages:
            self.processed_messages.add(message)
            self.pre_prepared_messages.add(message)
            self.consensus_algorithm.pre_prepare(message, self)
            self.send_message_to_all(f"PREPARE:{message}")

    def process_prepare(self, request):
        if request not in self.prepared_messages:
            if request in self.pre_prepared_messages:
                self.prepared_messages.add(request)
                self.consensus_algorithm.prepare(request, self)
                self.send_message_to_all(f"COMMIT:{request}")

    def process_commit(self, request):
        if request not in self.committed_messages:
            if request in self.prepared_messages:
                self.committed_messages.add(request)
                self.consensus_algorithm.commit(request, self)

    def stop(self):
        self.server.stop()
        for peer in self.peers:
            peer.close()


class ClientNode:
    def __init__(self, client_id, pbft_network, list_of_nodes):
        self.client_node_id = client_id
        self.pbft_network = pbft_network
        self._request = None
        self.list_of_nodes = list_of_nodes
        self.nodes = []
        self.primary_node = self.pbft_network.primary_node
            
    def send_request(self, request): # 1. request = "Transaction Data"
        self._request = request
        
        if self.client_node_id == 0 and self.pbft_network.primary_node is not None and self.list_of_nodes is not None:
            print(f"Client Node {self.client_node_id} send request to primary node")
            # self.list_of_nodes[0].receive_request = request
            self.pbft_network.broadcast_request(request)

    @property
    def request(self):
        return self._request

        
class PrimaryNode:
    def __init__(self, primary_node, pbft_network, pbft):
        self.node = primary_node
        self.pbft_network = pbft_network
        self.pbft = pbft
        self._request = None

    def broadcast_pre_prepare_message(self, request): # 2. pre_prepare
        print(f"Primary Node {self.node.node_id} broadcasting pre-prepare message")
        self._request = request
        # Node.send_message_to_all(request)
        self.pbft.pre_prepare(request, self.node)


    def receive_request(self, request):
        if request not in self.node.processed_messages:
            self.node.process_request(request)
            self.pbft.pre_prepare(request, self.node)
        self.pbft.pre_prepare(request, self.node)
        
    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        self._request = value

