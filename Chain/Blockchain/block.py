from typing import Dict

class Block:
    def __init__(self, 
                 index: int, 
                 previous_hash: str,
                 timestamp: int, 
                 data: str,
                 current_block_hash: str):
        self.index: int = index
        self.previous_hash: str = previous_hash 
        self.timestamp: int = timestamp
        self.data: str = data    
        self.current_block_hash: str = current_block_hash

    @property
    def block_header(self) -> Dict[str, str]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "current_block_hash": self.current_block_hash
        }
