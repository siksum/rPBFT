import hashlib
import time
from typing import List, Dict



class Block:
    def __init__(self, 
                 index: int, 
                 previous_hash: str,
                 timestamp: int, 
                 validator_signatures: List[str], 
                 consensus_round: int,
                 data: str,
                 current_block_hash: str):
        self.index = index
        self.previous_hash = previous_hash 
        self.timestamp = timestamp
        self.validator_signatures = validator_signatures
        self.consensus_round = consensus_round
        self.data = data    
        self.current_block_hash = current_block_hash

    @property
    def block_header(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "validator_signatures": self.validator_signatures,
            "consensus_round": self.consensus_round,
            "data": self.data,
            "current_block_hash": self.current_block_hash
        }


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        genesis_data = "Genesis Block"
        genesis_hash = self.calculate_hash(genesis_data)
        return Block(
            index=0, 
            previous_hash="0"*64, 
            timestamp=int(time.time()), 
            validator_signatures=[],
            consensus_round=0,
            data=genesis_data,
            current_block_hash=genesis_hash
        )

    
    def get_latest_block(self):
        return self.chain[-1]
    
    def create_new_block(self, previous_block, new_block_data):
        index = previous_block.index + 1
        timestamp = int(time.time())
        previous_hash = previous_block.current_block_hash
        validator_signatures = ["signature1", "signature2"]
        consensus_round = 1
        data = new_block_data
        current_block_hash = self.calculate_hash(str(index) + previous_hash + str(timestamp) + str(validator_signatures) + str(consensus_round) + str(data))
        if previous_block.data != new_block_data:
            return Block(
                index=index, 
                previous_hash=previous_hash, 
                timestamp=timestamp, 
                validator_signatures=validator_signatures, 
                consensus_round=consensus_round, 
                data = new_block_data,
                current_block_hash=current_block_hash
            )
        return None


    def add_block(self, new_block_data):
        previous_block = self.get_latest_block()
        new_block = self.create_new_block(previous_block, new_block_data)
        if new_block != None:
            self.chain.append(new_block)
            print("new_block")
        return None
        

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.current_block_hash != self.calculate_hash(str(current_block.index) + current_block.previous_hash + str(current_block.timestamp) + str(current_block.validator_signatures) + str(current_block.consensus_round) + str(current_block.data)):
                return False
            if current_block.previous_hash != previous_block.current_block_hash:
                return False
        return True
    
    def calculate_hash(self, value: str) -> str:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
