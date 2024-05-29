# blockchain.py
import time
import hashlib
import json

class Block:
    def __init__(
        self, 
        index: int, 
        previous_hash: str, 
        timestamp: int, 
        data: str, 
        current_block_hash: str,
        # consensus_round: int,
        # validator_signatures: List[str]        
    ):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.current_block_hash = current_block_hash
        
        # 필요?
        # self.consensus_round = consensus_round
        # self.validator_signatures = validator_signatures
    
    @property
    def block_header(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "current_block_hash": self.current_block_hash,
            # "validator_signatures": self.validator_signatures,
            # "consensus_round": self.consensus_round,
        }

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        genesis_data = "Genesis Block"
        genesis_hash = self.calculate_hash(genesis_data, 0, "0", int(time.time()))
        return Block(
            index=0, 
            previous_hash=bytes(64), 
            timestamp=int(time.time()), 
            data=genesis_data, 
            current_block_hash=genesis_hash,
            # validator_signatures=[],
            # consensus_round=0
        )

    def get_latest_block(self):
        return self.chain[-1]
    
    def create_new_block(self, previous_block, data):
        index = previous_block.index + 1
        timestamp = int(time.time())
        previous_hash = previous_block.current_block_hash
        current_block_hash = self.calculate_hash(data, index, previous_hash, timestamp)
        return Block(index, previous_hash, timestamp, data, current_block_hash)
    
    def add_block(self, data):
        previous_block = self.get_latest_block()
        new_block = self.create_new_block(previous_block, data)
        self.chain.append(new_block)


    # 체인 전체를 스캔하면 너무 성능을 해치는 것 같아서 블록 생성시에 한번 체크하는게 좋을듯.
    def is_valid_block(self, block):
        previous_block = self.get_latest_block()
        if  block.index != previous_block.index + 1 or \
            block.previous_hash != previous_block.hash or \
            block.current_block_hash != self.calculate_hash(block.data, block.index, block.previous_hash, block.timestamp):
            return False
        return True

    # def synchronize(self, blockchain):
    #     if len(blockchain.chain) > len(self.chain):
    #         self.chain = blockchain.chain

    def calculate_hash(self, data, index, previous_hash, timestamp):
        payload = {
            'index': index,
            'previous_hash': previous_hash,
            'timestamp': timestamp,
            'data': data
        }
        payload_str = json.dumps(payload, sort_keys=True)
        
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
