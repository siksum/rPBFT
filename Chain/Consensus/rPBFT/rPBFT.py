from typing import List, Dict, Any, TYPE_CHECKING
from Consensus.node import PrimaryNode, ClientNode
from Consensus.pbft_handler import PBFTHandler
import time
import hashlib
from Utils.utils import *
import random

if TYPE_CHECKING:
    from Chain.Consensus.node import Node


class rPBFT():
    def __init__(self) -> None:
        self.client_node: 'ClientNode' = None
        self.primary_node: 'PrimaryNode' = None
        self.count_of_faulty_nodes: int = 0
        self.nodes: List['Node'] = []
        self.nodes_committee: List[Dict[str, Any]] = []
        self.pbft_handler: 'PBFTHandler' = None
        self.sharing_faulty_data_count: int = 4
        self.count_of_top_priorities: int = 0
        self.nodes_to_send_fault_data: Dict[str, Any] = {}
    
        
    def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:
        if message["stage"] == "PRE-PREPARE":
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_pre_prepare_messages.append(new_message)
            # print(f"[Recieve] Node: {node.node_id}, content: {message}")
            
            if node.is_faulty is True:
                return
            self.prepare(message, node)
            
        elif message["stage"] == "PREPARE":
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_prepare_messages.append(new_message)
            
            if not check_duplicate(new_message, node.received_prepare_messages[:-1]):
                # print(f"[Recieve] Node: {node.node_id}, content: {message}")
                pass
            else:
                node.received_prepare_messages = remove_duplicates(node.received_prepare_messages)
            
            sorted_by_seqnum = groupby_sorted(node.received_prepare_messages)
            equal_seqnum = sorted_by_seqnum.get(message['seq_num'])

            if node.is_faulty is True:
                return
            
            if len(equal_seqnum) >= 2 * self.count_of_faulty_nodes and node.validate_message(message, equal_seqnum) is True:
                self.commit(message, node)
        
        # COMMIT, VIEW-CHANGE, NEW-VIEW 메시지를 받은 노드는 더이상 타이머가 필요없으므로 종료시킴.
        elif message["stage"] == "COMMIT":
            # if node.view_change_timer:
            #     node.view_change_timer.cancel()
            
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_commit_messages.append(new_message)
            
            if not check_duplicate(new_message, node.received_commit_messages[:-1]):
                # print(f"[Recieve] Node: {node.node_id}, content: {message}")
                pass
            else:
                node.received_commit_messages = remove_duplicates(node.received_commit_messages)
            
            sorted_by_seqnum = groupby_sorted(node.received_commit_messages)
            equal_seqnum = sorted_by_seqnum.get(message['seq_num'])
            
            # if node.is_faulty is True:
            #     return
            
            if len(equal_seqnum) >= (2 * self.count_of_faulty_nodes + 1) and node.validate_message(message, equal_seqnum) is True:
                self.send_reply_to_client(message, node)
        
        elif message["stage"] == "FAULT-DATA":
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_fault_data.append(new_message)
            
            if not check_duplicate(new_message, node.received_fault_data[:-1]):
                # print(f"[Recieve] Node: {node.node_id}, content: {message}")
                pass
            else:
                node.received_fault_data = remove_duplicates(node.received_fault_data)
                
            sorted_by_seqnum = groupby_sorted(node.received_fault_data)
            equal_seqnum = sorted_by_seqnum.get(message['seq_num'])
            self.calculate_priority(node, equal_seqnum)
            # print("[PRIORITY AFTER FAULT DATA RECEIVE]",node.node_id, node.sum_of_priorities)

                
    def pre_prepare(self, request: Dict[str, Any], node: 'Node') -> None:
        if node.is_faulty is True:
            return
        
        request_digest = hashlib.sha256(str(request).encode()).hexdigest()
        
        pre_prepare_message: Dict[str, Any] = {
            "stage": "PRE-PREPARE",
            "view": node.current_view_number,
            "seq_num": node.current_sequence_number,
            "digest": request_digest,
            "data": request,
            "node_id": node.node_id
        }
        
        node.send_message_to_peers(pre_prepare_message, node.peers_list)
            
            
    def prepare(self, pre_prepare_message: Dict[str, Any], node: 'Node') -> None:
        prepare_message: Dict[str, Any] = {
            "stage": "PREPARE",
            "view": node.current_view_number,
            "seq_num": pre_prepare_message["seq_num"],
            "digest": pre_prepare_message["digest"],
            "node_id": node.node_id,
        }
        
        #fault data 존재 여부에 따라 전체에게 브로드캐스트 할수도 있고, 인접 노드 중 일부로 구성된 위원회 내부로만 전송할수도 있음.
        
        selected_committee_ids = self.select_committee(node)
        node.selected_committee_list = self.committee_node_list(node, selected_committee_ids)
        # self.nodes_committee.append({'node_id': node.node_id, 'committee': node.selected_committee_list})
        # print("[SELECTED COMMITTEE]", node.node_id, node.selected_committee_list)
        node.send_message_to_peers(prepare_message, node.selected_committee_list)
        
        # if self.check_fault_data(node) is True:
        #     selected_committee_ids = self.select_committee(prepare_message)
        #     selected_committee_list = self.committee_node_list(node, selected_committee_ids)
        #     self.nodes_committee.append({'node_id': node.node_id, 'committee': selected_committee_list})
        #     node.send_message_to_peers(prepare_message, selected_committee_list)
        # else:
        #     node.send_message_to_peers(prepare_message, node.peers_list)
        
            
    def commit(self, prepare_message: Dict[str, Any], node: 'Node') -> None:
        commit_message: Dict[str, Any] = {
            "stage": "COMMIT",
            "view": prepare_message["view"],
            "seq_num": prepare_message["seq_num"],
            "digest": prepare_message["digest"],
            "node_id": node.node_id,
        }
        
        node.send_message_to_peers(commit_message, node.selected_committee_list)
        
        # if self.check_fault_data(node) is True:
        #     # print(self.nodes_committee)
        #     # selected_committee_list = self.nodes_committee[node.node_id]['committee']
        #     print(node.selected_committee_list)
        #     node.send_message_to_peers(commit_message, node.selected_committee_list)
        # else:
        #     node.send_message_to_peers(commit_message, node.peers_list)
        
        
    def send_reply_to_client(self, commit_message: Dict[str, Any], node: 'Node') -> None:
        reply_message: Dict[str, Any] = {
            "stage": "REPLY",
            "view": commit_message["view"],
            "timestamp": int(time.time()),
            "client_id": node.client_node.client_node_id,
            "seq_num": commit_message["seq_num"],
            "result": "Execution Result",
            "digest": commit_message["digest"],
            "node_id": node.node_id
        }
        
        node.current_sequence_number = commit_message["seq_num"]

        success_add_block = node.client_node.receive_reply(reply_message, self.count_of_faulty_nodes)
        
        if success_add_block is True:
            self.make_fault_data(commit_message, node)
        else:
            return
        
    
    def make_fault_data(self, reply_message: Dict[str, Any], node: 'Node') -> None:
        fault_info = [0 for i in range(0, len(self.nodes))]
        node.sum_of_priorities = [0 for i in range(0, len(self.nodes))]
        
        prepare_set = [msg for msg in node.received_prepare_messages if msg["message"]["seq_num"] == reply_message["seq_num"]]
        prepare_set = {(msg['node_id_from'], msg['message']['seq_num']) for msg in prepare_set}
        commit_set = [msg for msg in node.received_commit_messages if msg["message"]["seq_num"] == reply_message["seq_num"]]
        commit_set = {(msg['node_id_from'], msg['message']['seq_num']) for msg in commit_set}
        
        common_messages = prepare_set.intersection(commit_set)
        
        for node_id_from, _ in common_messages:
            fault_info[node_id_from-1] += 1
        
        fault_data: Dict[str, Any] = {
            "stage": "FAULT-DATA", 
            "block_num": node.blockchain.get_latest_block().index,
            "view_num": node.current_view_number,
            "node_id": node.node_id,
            "seq_num": node.current_sequence_number,
            "digest": reply_message["digest"],
            "fault_info": fault_info
        }
        
        self.share_fault_data(node, fault_data)
        
        
    def share_fault_data(self, node: 'Node', fault_data) -> None:
        selected_adjacent_nodes = self.select_adjacent_nodes(self.sharing_faulty_data_count, node)
        node.send_message_to_peers(fault_data, selected_adjacent_nodes)
        
        
    def select_adjacent_nodes(self, count: int, node: 'Node') -> None:
        # start_index = max(0, node.node_id - count)
        # end_index = min(len(node.peers_list), node.node_id + count + 1)
        
        # sub_peers_list = node.peers_list[start_index:end_index]
        # selected_peers = random.sample(sub_peers_list, count)
        
        return node.peers_list[:count]
        
    
    def select_committee(self, node: 'Node') -> None:
        if node.sum_of_priorities == []:
            node.sum_of_priorities = [random.randint(0, len(self.nodes)) for _ in range(len(self.nodes))]
        
        node.sum_of_priorities = [random.randint(0, len(self.nodes)) for _ in range(len(self.nodes))]
        filtered_priorities = [(i, value) for i, value in enumerate(node.sum_of_priorities) if i != node.node_id]
        filtered_priorities.sort(key=lambda x: x[1], reverse=True)
        sorted_indices = [i for i, value in filtered_priorities]
        selected_committee_node_ids = sorted_indices[:len(sorted_indices)//2+1]
        return selected_committee_node_ids
    
    
    def committee_node_list(self, node: 'Node', selected_committee_node_ids) -> None:
        committee_node_list = []
        for peer in node.peers_list:
            if peer['node_id'] in selected_committee_node_ids:
                committee_node_list.append(peer)
        return committee_node_list
    
        
    def calculate_priority(self, node: 'Node', received_fault_data: List[Dict[str, Any]]) -> None:
        sum_of_priorities = [0 for i in range(0, len(self.nodes))]
        for fault_data in received_fault_data:
            sum_of_priorities = [x + y for x, y in zip(sum_of_priorities, fault_data['message']['fault_info'])]
        if len(received_fault_data) > node.count_of_fault_data :
            node.sum_of_priorities = sum_of_priorities
            node.count_of_fault_data = len(received_fault_data)
            # print("[UPDATED PRIORITY]", node.node_id, node.sum_of_priorities)
        else:
            return 
        
        
    def check_fault_data(self, node: 'Node') -> bool:
        if not node.hasFaultyData:
            return False
        else:
            return True
        
    