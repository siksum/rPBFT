import hashlib
import json
import time
from typing import List, Dict

def calculate_hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def calculate_merkle_root(values: List[str]) -> str:
    if not values:
        return ""
    
    hash_list = [calculate_hash(value) for value in values]
    
    while len(hash_list) > 1:
        if len(hash_list) % 2 != 0:
            hash_list.append(hash_list[-1])
        
        new_hash_list = []
        for i in range(0, len(hash_list), 2):
            new_hash = calculate_hash(hash_list[i] + hash_list[i + 1])
            new_hash_list.append(new_hash)
        
        hash_list = new_hash_list
    
    return hash_list[0]

class State:
    def __init__(self):
        self.accounts = {}  # 각 계정의 잔액을 저장하는 딕셔너리
    
    def update_state(self, transactions: List[Dict[str, int]]):
        for tx in transactions:
            sender = tx['sender']
            recipient = tx['recipient']
            amount = tx['amount']
            
            if sender in self.accounts:
                self.accounts[sender] -= amount
            else:
                self.accounts[sender] = -amount
            
            if recipient in self.accounts:
                self.accounts[recipient] += amount
            else:
                self.accounts[recipient] = amount
    
    def get_state_root_hash(self) -> str:
        state_list = [f"{k}:{v}" for k, v in sorted(self.accounts.items())]
        return calculate_merkle_root(state_list)

class Block:
    def __init__(self, 
                 index: int, 
                 previous_hash: str,
                 timestamp: int, 
                 merkle_root: str, 
                 state_root_hash: str, 
                 validator_signatures: List[str], 
                 consensus_round: int,
                 data: str,
                 current_block_hash: str):
        self.index = index
        self.previous_hash = previous_hash 
        self.timestamp = timestamp
        self.merkle_root = merkle_root
        self.state_root_hash = state_root_hash
        self.validator_signatures = validator_signatures
        self.consensus_round = consensus_round
        self.data = data    
        self.current_block_hash = current_block_hash
        
    def convert_to_json(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "validator_signatures": self.validator_signatures,
            "state_root_hash": self.state_root_hash,
            "consensus_round": self.consensus_round,
            "data": self.data,
            "current_block_hash": self.current_block_hash
        }

    @property
    def block_header(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "validator_signatures": self.validator_signatures,
            "state_root_hash": self.state_root_hash,
            "consensus_round": self.consensus_round
        }

def create_genesis_block(state: State):
    genesis_data = "Genesis Block"
    genesis_hash = calculate_hash(genesis_data)
    state_root_hash = state.get_state_root_hash()
    return Block(
        index=0, 
        previous_hash="0"*64, 
        timestamp=int(time.time()), 
        merkle_root="0"*64, 
        state_root_hash=state_root_hash,
        validator_signatures=[],
        consensus_round=0,
        data=genesis_data,
        current_block_hash=genesis_hash
    )

def create_new_block(previous_block, transactions: List[Dict[str, int]], state: State):
    index = previous_block.index + 1
    timestamp = int(time.time())
    previous_hash = previous_block.current_block_hash
    merkle_root = calculate_merkle_root([json.dumps(tx) for tx in transactions])

    state.update_state(transactions)
    state_root_hash = state.get_state_root_hash()

    validator_signatures = ["signature1", "signature2"]
    consensus_round = 1
    data = json.dumps(transactions)
    
    current_block_hash = calculate_hash(str(index) + previous_hash + str(timestamp) + data + merkle_root + state_root_hash + str(validator_signatures) + str(consensus_round))
    
    return Block(index, previous_hash, timestamp, merkle_root, state_root_hash, validator_signatures, consensus_round, data, current_block_hash)

class Blockchain:
    def __init__(self):
        self.state = State()
        self.chain = [create_genesis_block(self.state)]

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions: List[Dict[str, int]]):
        previous_block = self.get_latest_block()
        new_block = create_new_block(previous_block, transactions, self.state)
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.current_block_hash != calculate_hash(str(current_block.index) + current_block.previous_hash + str(current_block.timestamp) + current_block.data + current_block.merkle_root + current_block.state_root_hash + str(current_block.validator_signatures) + str(current_block.consensus_round)):
                return False
            if current_block.previous_hash != previous_block.current_block_hash:
                return False
        return True

# # 사용 예시
# blockchain = Blockchain()
# blockchain.add_block([{"sender": "Alice", "recipient": "Bob", "amount": 50}, {"sender": "Bob", "recipient": "Charlie", "amount": 30}])
# blockchain.add_block([{"sender": "Charlie", "recipient": "Alice", "amount": 20}, {"sender": "Alice", "recipient": "David", "amount": 10}])

# # 블록체인 출력
# for block in blockchain.chain:
#     print(block.convert_to_json())
