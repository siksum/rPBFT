from typing import List, Dict, Any, TYPE_CHECKING
from Consensus.node import PrimaryNode, ClientNode
from Consensus.pbft_handler import PBFTHandler
import time
import hashlib
from Utils.utils import *
import asyncio

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
        self.sharing_faulty_data_count: int = 6
        self.count_of_top_priorities: int = 0
        self.nodes_to_send_fault_data: Dict[str, Any] = {}
    
        
    async def handle_message(self, message: Dict[str, Any], node: 'Node') -> None:       
        if message["stage"] == "PRE-PREPARE":
            if node.is_faulty is True:
                return
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_pre_prepare_messages.append(new_message)
            print(f"[Recieve] Node: {node.node_id}, content: {message}")

            await asyncio.sleep(0)
            self.prepare(message, node)
            
        elif message["stage"] == "PREPARE":
            if node.is_faulty is True:
                return
            if node.client_node.is_block_added[message["digest"]] is True:
                return
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_prepare_messages.append(new_message)
            
            if not check_duplicate(new_message, node.received_prepare_messages[:-1]):
                print(f"[Recieve] Node: {node.node_id}, content: {message}")
            else:
                node.received_prepare_messages = remove_duplicates(node.received_prepare_messages)
            
            sorted_by_seqnum = groupby_sorted(node.received_prepare_messages)
            equal_seqnum = sorted_by_seqnum.get(message['seq_num'])
            
            await asyncio.sleep(0)
            if len(equal_seqnum) >= 2 * self.count_of_faulty_nodes and node.validate_message(message, equal_seqnum) is True:
                self.commit(message, node)
        
        # COMMIT, VIEW-CHANGE, NEW-VIEW 메시지를 받은 노드는 더이상 타이머가 필요없으므로 종료시킴.
        elif message["stage"] == "COMMIT":
            if node.is_faulty is True:
                return
            if node.client_node.is_block_added[message["digest"]] is True:
                return
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_commit_messages.append(new_message)
            
            if not check_duplicate(new_message, node.received_commit_messages[:-1]):
                print(f"[Recieve] Node: {node.node_id}, content: {message}")
            else:
                node.received_commit_messages = remove_duplicates(node.received_commit_messages)
            
            sorted_by_seqnum = groupby_sorted(node.received_commit_messages)
            equal_seqnum = sorted_by_seqnum.get(message['seq_num'])
            
            await asyncio.sleep(0)
            if len(equal_seqnum) >= (2 * self.count_of_faulty_nodes + 1) and node.validate_message(message, equal_seqnum) is True:
                self.send_reply_to_client(message, node)
        
        elif message["stage"] == "FAULT-DATA":
            new_message = {'node_id_to': node.node_id, 'node_id_from': message['node_id'], 'message': message}
            node.received_fault_data.append(new_message)
            
            if not check_duplicate(new_message, node.received_fault_data[:-1]):
                print(f"[Recieve] Node: {node.node_id}, content: {message}")
            else:
                node.received_fault_data = remove_duplicates(node.received_fault_data)
                
            sorted_by_seqnum = groupby_sorted(node.received_fault_data)
            equal_seqnum = sorted_by_seqnum.get(message['seq_num'])
            
            await asyncio.sleep(0)
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
        print("[SELECTED COMMITTEE]", node.node_id, node.selected_committee_list)
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

        node.client_node.receive_reply(reply_message, self.count_of_faulty_nodes)
        if node.client_node.is_block_added[commit_message["digest"]] is True and len(node.client_node.blockchain.chain) % 10 == 0:
            self.make_fault_data(commit_message, node)
        else:
            return
        
    
    def make_fault_data(self, reply_message: Dict[str, Any], node: 'Node') -> None:
        fault_info = [0] * len(self.nodes)
        node.sum_of_priorities = [0] * len(self.nodes)
        
        # prepare_set과 commit_set의 교집합만 계산
        prepare_set = {
            (msg['node_id_from'], msg['message']['seq_num'])
            for msg in node.received_prepare_messages
            if msg["message"]["seq_num"] == reply_message["seq_num"]
        }
        commit_set = {
            (msg['node_id_from'], msg['message']['seq_num'])
            for msg in node.received_commit_messages
            if msg["message"]["seq_num"] == reply_message["seq_num"]
        }
        
        common_messages = prepare_set & commit_set
        
        for node_id_from, _ in common_messages:
            fault_info[node_id_from - 1] += 1
        
        latest_block_index = node.blockchain.get_latest_block().index

        fault_data: Dict[str, Any] = {
            "stage": "FAULT-DATA", 
            "block_num": latest_block_index,
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
        if not node.sum_of_priorities:
            # 기본값으로 사용할 우선순위 리스트 설정
            node.sum_of_priorities = [6, 0, 0, 0, 3, 4, 5, 6, 7, 8]
            # node.sum_of_priorities = [6, 0, 0, 0, 0, 0, 0, 3, 4, 5, 6, 7, 8, 3, 4, 5, 6, 7, 8, 5]

        # 자신을 제외한 우선순위 리스트 필터링 및 정렬
        sorted_indices = sorted(
            (i for i in range(len(node.sum_of_priorities)) if i != node.node_id),
            key=lambda i: node.sum_of_priorities[i],
            reverse=True
        )
        
        # 상위 1/3 노드 선택
        selected_committee_node_ids = sorted_indices[:len(sorted_indices) // 3 + 1]
        return selected_committee_node_ids

    def committee_node_list(self, node: 'Node', selected_committee_node_ids) -> None:
        # 리스트 컴프리헨션을 사용한 간결한 필터링
        return [peer for peer in node.peers_list if peer['node_id'] in selected_committee_node_ids]

    def calculate_priority(self, node: 'Node', received_fault_data: List[Dict[str, Any]]) -> None:
        # sum_of_priorities를 한 번에 계산
        sum_of_priorities = [sum(fault['message']['fault_info'][i] for fault in received_fault_data) 
                            for i in range(len(self.nodes))]

        # 우선순위 리스트 업데이트 조건
        if len(received_fault_data) > node.count_of_fault_data:
            node.sum_of_priorities = sum_of_priorities
            node.count_of_fault_data = len(received_fault_data)
        
    def check_fault_data(self, node: 'Node') -> bool:
        if not node.hasFaultyData:
            return False
        else:
            return True
        
    