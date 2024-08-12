from Reliability import *


class Node:
    def __init__(self, numberofNodes, reliability): # numberofNodes : 전체 노드 수, a : 증폭, s : 슬라이스
        self.numberofNodes = numberofNodes  # 전체 노드 수
        self.reliability = reliability
        self.nodes = [[0 for j in range(10)] for i in range(numberofNodes)]  # 노드[i] & 노드 데이터 리스트[i][j]


    """
    노드 초기화
    전체 노드 생성 -> 결함확률 설정
    """
    def generate(self):
        for i in range(0, self.numberofNodes):
            self.nodes[i] = [i, self.reliability[i], 0, 0, 0, None, [], [], [], {}, np.array([])]

        return self.nodes



