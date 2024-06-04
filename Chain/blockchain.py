import hashlib
import time
from typing import List, Dict, Any
import json

from block import Block


class Blockchain:
    def __init__(self, consensus, blocksize: int):
        self.chain: List[Block] = [self.create_genesis_block()]
        self.consensus= consensus
        self.blocksize: int = blocksize

    def create_genesis_block(self)-> Block:
        genesis_data: str = "Genesis Block"
        genesis_hash: str = self.calculate_hash(0, "0"*64, int(time.time()), genesis_data, "0"*64)
        return Block(
            index=0, 
            previous_hash="0"*64, 
            timestamp=int(time.time()), 
            data=genesis_data,
            current_block_hash=genesis_hash
        )
    
    def get_latest_block(self)-> Block: 
        return self.chain[-1]
    
    def create_new_block(self, previous_block: Block, data: Dict[str, Any]) -> Block:
        index: int = previous_block.index + 1
        timestamp: int = int(time.time())
        previous_hash: str = previous_block.current_block_hash
        current_block_hash: str = self.calculate_hash(index, previous_hash, timestamp, previous_block.data, previous_block.current_block_hash)
        return Block(index, previous_hash, timestamp, data, current_block_hash)

    def add_block_to_blockchain(self, data:Dict[str, Any])-> List[Block]:
        previous_block: Block = self.get_latest_block()
        new_block: Block = self.create_new_block(previous_block, data)
        self.chain.append(new_block)

    def is_valid_block(self, block: Block) -> bool:
        previous_block: Block = self.chain[-2]
        if  block.index != previous_block.index + 1 or \
            block.previous_hash != previous_block.current_block_hash or \
            block.current_block_hash != self.calculate_hash(block.index, block.previous_hash, block.timestamp, block.data, block.current_block_hash):
            return False
        return True
    
    def calculate_hash(self, index: int, previous_hash: str, timestamp: int, data: str, current_block_hash: str) -> str:
        payload = {
            'index': index,
            'previous_hash': previous_hash,
            'timestamp': timestamp,
            'data': data,
            'current_block_hash': current_block_hash
        }
        payload_str: str = json.dumps(payload, sort_keys=True)
        
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
    
    @property
    def updated_chain(self)-> List[Block]:
        return self.chain
