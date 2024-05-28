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
        self.index: int = index
        self.previous_hash: str = previous_hash 
        self.timestamp: int = timestamp
        self.validator_signatures: List[str] = validator_signatures
        self.consensus_round: int = consensus_round
        self.data: str = data    
        self.current_block_hash: str = current_block_hash

    @property
    def block_header(self)-> Dict[str, str]:
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
    def __init__(self, blocksize: int):
        self.chain: List[Block] = [self.create_genesis_block()]
        self.blocksize: int = blocksize

    def create_genesis_block(self)-> Block:
        genesis_data: str = "Genesis Block"
        genesis_hash: str = self.calculate_hash(genesis_data)
        return Block(
            index=0, 
            previous_hash="0"*64, 
            timestamp=int(time.time()), 
            validator_signatures=[],
            consensus_round=0,
            data=genesis_data,
            current_block_hash=genesis_hash
        )

    
    def get_latest_block(self)-> Block: 
        return self.chain[-1]
    
    def create_new_block(self, previous_block: Block) -> Block:
        index: int = previous_block.index + 1
        timestamp: int = int(time.time())
        previous_hash: str = previous_block.current_block_hash
        validator_signatures: List[str] = ["signature1", "signature2"]
        consensus_round: int = 1
        current_block_hash: str = self.calculate_hash(str(index) + previous_hash + str(timestamp) + str(validator_signatures) + str(consensus_round))
    
        return Block(index, previous_hash, timestamp, validator_signatures, consensus_round, current_block_hash)


    def add_block(self)-> List[Block]:
        previous_block: Block = self.get_latest_block()
        new_block: Block = self.create_new_block(previous_block)
        self.chain.append(new_block)

    def is_chain_valid(self)-> bool:
        for i in range(1, len(self.chain)):
            current_block: Block = self.chain[i]
            previous_block: Block = self.chain[i - 1]
            if current_block.current_block_hash != self.calculate_hash(str(current_block.index) + current_block.previous_hash + str(current_block.timestamp) + current_block.data + current_block.merkle_root + current_block.state_root_hash + str(current_block.validator_signatures) + str(current_block.consensus_round)):
                return False
            if current_block.previous_hash != previous_block.current_block_hash:
                return False
        return True
    
    def calculate_hash(self, value: str) -> str:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
