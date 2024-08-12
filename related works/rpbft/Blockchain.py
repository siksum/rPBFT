import hashlib


class Blockchain:
    def __init__(self, numberofNodes, blockSize, nodes, consensus):   # (self, numberofNodes, numberofFaults, blockSize, consensus):
        """
        시뮬레이션 변수 저장
        """
        self.numberofNodes = numberofNodes  # 전체 노드 수
        #self.numberofFaults = numberofFaults  # 결함 노드 수
        self.f = (numberofNodes - 1) / 3     # f : 합의 성공 여부를 측정하기위한 변수   f = (numberofNodes-1-1(client 배제))/3
        self.blockSize = blockSize  # 블록 사이즈
            # 1. max : 비트코인의 최대 블록 사이즈 4MB (BIP141 : https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#cite_note-3)
            # 2. ave : 비트코인 평균 블록 사이즈 1MB (https://www.blockchain.com/charts/avg-block-size)
            # 3. test : test용 10Bytes
        self.consensus = consensus  # 합의 알고리즘

        self.block = [None]  # 블록(단기 저장)
        self.chain = []  # 블록체인
        self.nodes = nodes

    """
    블록 합의 시작 버튼
    사용 방법 : Blockchain.consensus.start(self.nodes)
    """
    def consensus_start(self, t):
        result = self.consensus.start(self.nodes, self.f, self.block, t)
        return result

    """
    블록을 생성하는 함수
    블록 사이즈에 따라 데이터를 임의로 생성 후 블록에 추가
    """
    def new_block(self):
        # 블록 구조 : [hash, data]
        if self.blockSize == "max":
            data = bytes(int(4 * (1e+6) - 32))  # 4MB
            hash = hashlib.sha256(data).digest()
            self.block = [hash, data]
            return self.block
        elif self.blockSize == "ave":  # 1MB
            data = bytes(int(1e+6))
            hash = hashlib.sha256(data).digest()
            self.block = [hash, data]
            return self.block
        elif self.blockSize == "test":  # 10Bytes
            data = bytes(int(10))
            hash = hashlib.sha256(data).digest()
            self.block = [hash, data]
            return self.block
        else:
            print("ERROR : block size error")

    """
    노드를 초기화하는 함수
    전체 노드 생성 -> client 블록 생성 -> 정상노드 결함노드 설정

    def node(self, block):
        for i in range(0, len(self.nodes)):
            if i == 0:
                self.nodes[i] = [i, 0, 0, 0, 0, block, [], [], [], []]
            else:
                if i - 1 <= (self.numberofNodes - self.numberofFaults):
                    self.nodes[i] = [i, 0, 0, 0, 0, None, [], [], [], []]
                else:
                    self.nodes[i] = [i, 1, 0, 0, 0, None, [], [], [], []]
        return self.nodes
        
    """

    """
    블록 추가 함수
    """
    def add_block(self, block):
        # 블록 추가
        self.chain.append(block)
        self.block = []
        #print("add block")

    """
    블록 삭제 함수
    """
    def delete_block(self):
        self.block = []
        #print("delete block")
