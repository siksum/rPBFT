from typing import Dict


class ViewChange:
    def __init__(self, node_id: int):
        self._total_view_count: int = 0
        self._current_view: Dict[str, int] = {}
        self._view_change: bool = False
        self._view_change_count: int = 0
        self._node_id: int = node_id    
    
    def change_view(self) -> Dict[str, int]:
        self._view_change = True
        self._view_change_count += 1
        self._total_view_count += 1
        self._current_view = {f"View {self._total_view_count}": self._node_id}
        return self._current_view
    
    def reset_view_change(self) -> None:
        self._view_change = False
        self._view_change_count = 0
        self._current_view = {}
        self._total_view_count = 0
    
    @property
    def current_view(self) -> Dict[str, int]:
        return self._current_view
    
    @property
    def view_change_count(self) -> int:
        return self._view_change_count
    
    @property
    def view_change_status(self) -> bool:
        return self._view_change
    
    @property
    def total_view_count(self) -> int:
        return self._total_view_count
    
    @property
    def node_id(self) -> int:
        return self._node_id
    
    def set_node_id(self, node_id: int) -> None:
        self._node_id = node_id
    
    def __str__(self) -> str:
        return (f"View Change Status: {self._view_change}, "
                f"View Change Count: {self._view_change_count}, "
                f"Current View: {self._current_view}, "
                f"Total View Count: {self._total_view_count}, "
                f"Node ID: {self._node_id}")
