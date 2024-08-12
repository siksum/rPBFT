from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from Chain.Consensus.node import Node
    
class ConsensusAlgorithm(ABC):
    @abstractmethod
    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
        pass

    # @abstractmethod
    # def request_view_change(self, node_id: int, new_view: int) -> None:
    #     pass

    @abstractmethod
    def pre_prepare(self, request: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def prepare(self, pre_prepare_message: Dict[str, Any], node: 'Node') -> None:
        pass

    @abstractmethod
    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        pass

    # @abstractmethod
    # def handle_view_change(self, message: Dict[str, Any], node: 'Node') -> None:
    #     pass