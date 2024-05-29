import hashlib
import time
from typing import List, Dict

class View:
    def __init__(self, node_id: int):
        self.total_view_count: int = 0
        self.current_view: Dict[str, int] = {}
        self.view_change: bool = False
        self.view_change_count: int = 0
        self.node_id: int = node_id    
    
    def change_view(self):
        self.view_change = True
        self.view_change_count += 1
        self.total_view_count += 1
        self.current_view = {f"View {self.total_view_count}": self.node_id}
        return self.current_view
    
    def reset_view_change(self):
        self.view_change = False
        self.view_change_count = 0
        self.current_view = {}
        self.view_count = 0
    
    @property
    def current_view(self)-> Dict[str, int]:
        return self.current_view
    
    @property
    def view_change_count(self)-> int:
        return self.view_change_count
    
    @property
    def view_change_status(self)-> bool:
        return self.view_change
    
    @property
    def total_view_count(self)-> int:
        return self.total_view_count
    
    def set_node_id(self, node_id: int):
        self.node_id = node_id
    
    @property   
    def node_id(self)-> int:
        return self.node_id
    
    def __str__(self):
        return f"View Change Status: {self.view_change}, View Change Count: {self.view_change_count}, Current View: {self.current_view}, View Count: {self.total_view_count}, Node ID: {self.node_id}"    




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
    
    @property
    def updated_chain(self)-> List[Block]:
        return self.chain
