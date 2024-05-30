import hashlib
import json
import pickle
import socket
from network import Server, Client

F = 0
CLIENT_BASE_PORT = 5100
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
        
        # message storage
        self.requests = []
        self.pre_prepared = []
        self.prepared = []
        self.replies = []
        
        # view change에 대한 voting
        self.view_change_votes = []
        
        # view, seq, checkpoint, bound
        self.view_num = 0
        self.seq_num = 0
        self.last_stable_checkpoint = 0
        self.low_bound = 0
        self.high_bound = 0
        
        # view change 타이머
        self.view_change_timer = None
        

    def connect_to_peer(self, host, port):
        client = Client(host, port)
        self.peers.append(client)

    def send_message_to_all(self, message):
        for peer in self.peers:
            peer.send_message(message)

    def is_primary(self):
        if self.node_id == 1:
            return True 
        return False
    
    def receive_message(self, message):
        print(f"Node {self.node_id} received message: {message}")
        message = json.loads(message)
        if message not in self.requests:
            if message["message_type"] == "PrePrepare":
                print(f"[RECV_PRE_PREPARE] Node {self.node_id} received PRE-PREPARE: view={message["view_num"]}, seq={message["seq_num"]}, digest={message["digest"]}")

                # TODO: view change 구현
                # if pre_prepare.seq_num in self.pre_prepared:
                #     if pre_prepare.digest != self.pre_prepared[pre_prepare.seq_num].digest:
                #         self.send_view_change()
                #     return
                
                self.pre_prepared.append(message)
                
                # print("pre_prepared:", self.pre_prepared)
                
                processed_pre_prepare = {
                    "message_type": "Prepare",
                    "view_num": message["view_num"],
                    "seq_num": message["seq_num"],
                    "digest": message["digest"],
                    "node_id": self.node_id
                }
                
                self.prepared.append(processed_pre_prepare)
                
                processed_pre_prepare = json.dumps(processed_pre_prepare).encode()
                self.send_message_to_all(processed_pre_prepare)
                
        if message["message_type"] == "Prepare":
            self.process_prepare(message)
            
        if message["message_type"] == "Commit":
            self.process_commit(message)
            

    def process_request(self, request):
        print(f"[RECV_REQ] Node {self.node_id} received request: {request}")
        if self.is_primary():
            digest = hashlib.sha256(pickle.dumps(request)).hexdigest()
            
            
            processed_request = {
                "message_type": "PrePrepare",
                "view_num": self.view_num,
                "seq_num": self.seq_num,
                "digest": digest,
                "request": str(request)
            }
            
            self.requests.append(processed_request)
            self.seq_num += 1
            return processed_request
            

    def process_prepare(self, prepare):
        print(f"[RECV_PREPARE] Node {self.node_id} received PREPARE: view={prepare["view_num"]}, seq={prepare["seq_num"]}")
        if prepare["seq_num"] != self.seq_num or \
           prepare["view_num"] != self.view_num or \
           prepare["digest"] != self.pre_prepared[prepare["seq_num"]]["digest"]:
               print("fucked up")
               return
           
        print(self.is_prepared(prepare["seq_num"]))
        self.prepared.append(prepare)
        
        if self.is_prepared(prepare["seq_num"]):
            processed_prepare = {
                "message_type": "Commit",
                "view_num": self.view_num,
                "seq_num": self.seq_num,
                "node_id": self.node_id
            }
            print("commit msg:", processed_prepare)
            
            commit_message = json.dumps(processed_prepare).encode()
            self.send_message_to_all(commit_message)

    def is_prepared(self, seq_num):
        print(self.prepared)
        if not any(message['seq_num'] == seq_num for message in self.prepared):
            return False
        return len(self.prepared[seq_num]) >= 2 * F + 1

    def process_commit(self, commit):
        print(f"[RECV_COMMIT] Node {self.node_id} received COMMIT: view={commit["view_num"]}, seq={commit["seq_num"]}")
        
        if not (any(commit["view_num"] == self.view_num for commit in self.prepared) and commit["view_num"] == self.view_num):
            return
        
        
        # TODO:  is_committed_local, execute_operation
        if self.is_commmitted_local(commit["seq_num"]):
            self.execute_operation(commit["seq_num"])
        
        self.replies.append(commit)
        # if request not in self.committed_messages:
        #     if request in self.prepared_messages:
        #         self.committed_messages.add(request)
        #         self.consensus_algorithm.commit(request, self)
        
    def is_commmitted_local(self, seq_num):
        # commit 메시지의 seq num에 해당하는 prepare 메시지가 없는 경우 False 반환 (중간 절차를 안거친 commit으로 간주)
        if not any(commit['seq_num'] == seq_num for commit in self.prepared):
            return False
        return len(self.prepared[seq_num]) >= 2 * F + 1

    
    def execute_operation(self, seq_num):
        print(f"[EXEC_OP] Node {self.node_id} executed request with seq_num={seq_num}")

        pre_prepare = self.pre_prepared[seq_num]
        
        if any(message["seq_num"] == seq_num for message in self.replies):
            return     
        #TODO: checkpoint 구현
        # if pre_prepare.seq_num % CHECKPOINT_INTERVAL == 0:
        #     self.checkpoint()

        reply = {
            "message_type": "Reply",
            "view_num": self.view_num,
            "timestamp": json.loads(pre_prepare["request"].replace("'", "\""))["timestamp"],
            "client_id": 0,
            "result": "Execution Result"
        }

        self.replies.append(reply)
        reply = json.dumps(reply).encode()

        # block = self.create_block(pre_prepare.request)
        # if self.blockchain.is_valid_block(block):
        #     self.blockchain.add_block(block.data)
        #     print(f"[EXEC_OP] Node {self.node_id} added block: {block.data}")
        #     self.broadcast_blockchain()
        # else:
        #     print(f"[EXEC_OP] Node {self.node_id} created an invalid block")
        # pass
            

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

