import hashlib
import numpy as np
import time


class ProposedMethod:
    """
    [i][0] : index : client, primary, 3, 4 ...
    [i][1] : 결함
    [i][2] : prepared_certificate
    [i][3] : commites_certificate
    [i][4] : reply 값
    [i][5] : stack 공간 --> 클라이언트는 이 자리에 block 값이 들어감
    [i][6] : commit message
    [i][7] : prepare message
    [i][8] : preprepare message
    [i][9] : 결함 정보 저장, 주변 노드로부터 받는것까지[[node1의 fault data],[node2의 fault data], [node3의 fault data], ...]
    """

    """ Request : client가 primary 노드에게 블록 전송 """
    def request(self, nodes, block):
        #print(nodes)
        nodes[0][5] = block
        nodes[1][5] = nodes[0][5]  # request요청이 오면  client 노드의 스택에 저장된 블록(nodes[0][5]를  primary 스택(nodes[1][5])에 복사
        nodes[1][8].append([nodes[0][0], 0])  # 리퀘스트 기록   [노드인덱스, 단계]
        #print(nodes)

    """ Pre-prepare : primary 노드가 client로부터 전달받은 블록을 검증 후, 참이면 모든 노드에게 Pre-prepare 메시지 브로드캐스팅 """
    def pre_prepare(self, nodes, t):
        if nodes[0][5] == nodes[1][5]:  # 블록 데이터(nodes[1][5])을 다시 해시한 값이 블록 해시(nodes[0][5])과 같은지 확인
            for i in range(2, len(nodes)):  # primary 노드 부터
                if nodes[i][1].faultrate[t] == 0:
                    # 정상노드면 Pre-Prepare 메시지 수신 + 블록 수신
                    nodes[i][8].append([nodes[1][0], 1])  # [sender설정, 단계, 블록] prepare message를 리스트에 추가
                    nodes[i][5] = nodes[1][5]  # 노드 i의 스택에 블록을 저장
                    ###print(True, nodes[i][1].faultrate[t])
                elif nodes[i][1].faultrate[t] == 1:  # 악성노드면 Pre-Prepare 메시지 수신X
                    ###print(False, nodes[i][1].faultrate[t])
                    pass
                #else:
                    #print('error in pre_prepare : point1')
            #print(nodes)
            return True
        else:
            #print('error in pre_prepare : point2')
            #print("nodes[1][5] : %s" % nodes[1][5])
            #print("hashlib.sha256(nodes[1][5]).digest() : $s" % hashlib.sha256(nodes[1][5]).digest())
            return False

    """ Prepare : Pre-prepare 메시지를 받은 노드(client 제외)가 다른 노드들에게 Prepare 메시지 브로드캐스팅. 만약 i번째 노드에게 preprepare 메세지가 존재하면 다른 노드들에게 prepare메세지 전달 """
    def prepare(self, nodes, t, c):
        #print(t)
        for i in range(2, len(nodes)):
            #print(i, nodes[i][10])
            if nodes[i][8]:  # Pre-prepare 메시지를 받은 기록이 있으면
                if nodes[i][10].size == 0:
                    for j in range(2, len(nodes)):
                        if (i != j) & (nodes[j][1].faultrate[t] == 0):  # 자기 자신이 아니고, 정상노드라면 Prepare 메시지 수신
                            nodes[i][7].append([nodes[j][0], 2])  # [i][7] prepare message 메세지 저장
                            #print(True, i, nodes[i][7])
                else:
                    count=0
                    for j in nodes[i][10]:
                        if (i != j) & (nodes[j][1].faultrate[t] == 0):  # 자기 자신이 아니고, 정상노드라면 Prepare 메시지 수신
                            nodes[i][7].append([nodes[j][0], 2])  # [i][7] prepare message 메세지 저장
                            count+=1
                        if count >= c:
                            break
                            #print(False, i, nodes[i][7])
                #print(nodes)
            else:
                #print("preprepare 메세지를 정상적으로 받지 못하였습니다")
                pass


    """ Prepared certificate : Pre-prepare 메시지 + Prepare 메시지의 합이 2*f +1 이상 """
    def preparedcertificate_commit(self, nodes, f, t):
        for i in range(2, len(nodes)):
            if len(nodes[i][7]) + len(nodes[i][8]) >= (2 * f) + 1:  # Pre-prepare 메시지 + Prepare 메시지의 합이 2*f +1 이상이면 Prepared certificate
                nodes[i][2] = 1
            #print(i, nodes[i][2])
                #for j in range(1, len(nodes)):
                    #if (i != j) & (nodes[i][5] == nodes[j][5]) & (nodes[j][1].faultrate[t] == 0):  # 자기 자신이 아니고, 갖고 있는 블록이 같고, 정상노드라면 Prepared certificate 설정
                        #nodes[j][2] = 1
                        #print(j, nodes[j][2])
            #else:
                #pass
                #print("preparedcertificate 메세지를 전송할 수 없습니다")
        #print(nodes)

    """ Commit : Prepared certificate인 노드가 다른 노드들에게 Commit 메시지 브로드캐스팅 """
    def commit(self, nodes, f, t, c):
        for i in range(2, len(nodes)):
            if nodes[i][2] == 1:  # Prepared certificate라면
                if nodes[i][10].size == 0:
                    for j in range(2, len(nodes)):
                        if (i != j) & (nodes[i][5] == nodes[j][5]) & (nodes[j][1].faultrate[t] == 0):  # 자기 자신이 아니고, 갖고 있는 블록이 같고, 정상노드라면 Commit 메시지 수신
                            nodes[i][6].append([nodes[j][0], 3])
                            #print(True, i, nodes[i][6])
                else:
                    count=0
                    for j in nodes[i][10]:
                        if (i != j) & (nodes[j][1].faultrate[t] == 0):  # 자기 자신이 아니고, 정상노드라면 Prepare 메시지 수신
                            nodes[i][6].append([nodes[j][0], 3])  # [i][7] prepare message 메세지 저장
                            #print(False, i, nodes[i][6])
                        if count >= c:
                            print(c)
                            break

            else:
                pass
                #print('commit 메세지를 정상적으로 받지 못하였습니다')
        #print(nodes)

    """ Commit certificate : Commit 메시지가 2*f +1 이상 """
    def commit_certificate(self, nodes, f):
        for i in range(2, len(nodes)):
            if len(nodes[i][6]) >= (2 * f) + 1:  # Commit 메시지가 2*f +1 이상이면 Commit certificate
                nodes[i][3] = 1  # Commit certificate
            #else:
                #pass
                #print('오류')
        #print(nodes)

    """ Committed certificate : 노드가 Prepared certificate, Commit certificate라면 각 노드의 reply를 1로 변경 """
    def committed_certificate(self, nodes):
        for i in range(2, len(nodes)):
            if (nodes[i][2] == 1) & (nodes[i][3] == 1):
                nodes[i][4] = 1
                #print(nodes[i][0], True)
            else:
                pass
        #print(nodes)

    """ Reply : client가 받은 리플라이 메시지가 f+1이상이면 정상적으로 결과가 수용됐다고 인지 """
    def reply(self, nodes, f):
        reply_sum = 0
        for i in range(2, len(nodes)):
            reply_sum = reply_sum + nodes[i][4]
        # reply_sum에 노드들의 reply 수를 저장
        #print(nodes)
        if reply_sum >= 23 + 1:  ### 여기
            nodes[0][4] = 1  # 클라이언트에게 reply 전달 여부 확인
            #print(nodes)
            return True
        else:
            return False
            #pass  # reply 전달 여부 확인


    """ faultdata_request : 결함 데이터 공유 """
    def faultdata_request(self, nodes, t):
        sharing = 4   # 데이터를 공유받을 노드의 수
        w = 10

        # 먼저 자기자신의 faultdata를 비트맵으로 변환
        for i in range(2, len(nodes)):
            priority = [0 for i in range(len(nodes))]

            if nodes[i][1].faultrate[t] == 0:
                fault_data = nodes[i][6]+nodes[i][7]+nodes[i][8]
                for j in fault_data:
                    node_index = j[0]
                    priority[node_index] = 1   # 비트맵으로 표현 가능하기 때문에 데이터를 효율적으로 전달 가능
                    #priority[node_index] += 1   # 받은 메시지 수에 가중치를 주는 버전. 하지만 지금 시뮬은 노드를 결함노드로 만들기 때문에 메시지 수에 차이가 없음
            priority[0] = 0
            priority[1] = 0
            nodes[i][9][t] = [priority]

            #nodes[i][5].clear()

            #print(nodes[i][9])

        for i in range(2, len(nodes)):
            if nodes[i][1].faultrate[t] == 0:
                for j in range(1, sharing+1):
                    if (i + j) < len(nodes):
                        #print(i+j, nodes[(i + j)][9][t])
                        nodes[i][9][t].append(nodes[(i + j)][9][t][0])
                    elif (i + j) >= len(nodes):
                        #print(i + j, nodes[(i + j)% len(nodes)+2][9][t])
                        nodes[i][9][t].append(nodes[((i + j) % len(nodes)) + 2][9][t][0])
            if t >= w:
                del nodes[i][9][t - w]

            priority = []
            for j in nodes[i][9].values():
                #print('a', j)
                priority.append(np.array(j).sum(axis=0))
            priority = np.array(priority).sum(axis=0)
            priority = priority.argsort()[::-1]
            nodes[i][10] = priority


        """
        if t >= w:
            for i in range(2, len(nodes)):
                #print('a', t - w)
                del nodes[i][9][t-w]
                #print(nodes[i][9])
                #print(len(nodes[i][9]))
        """

    """
    Priority : 우선순위 산정
    def Priority(self, nodes, t):
        w = 10

        for i in range(2, len(nodes)):
            priority = []
            #print('b', nodes[i][9])
            for j in nodes[i][9].values():
                #print('a', j)
                priority.append(np.array(j).sum(axis=0))
                #print('priority 1', len(priority), priority)

            priority = np.array(priority).sum(axis=0)
            #print('priority 2', priority)
            #print('priority 2', priority.argsort())
            #print('priority 2', priority.argsort()[::-1])
            priority = priority.argsort()[::-1]
            nodes[i][10] = priority
            #print(nodes[i][10])
    """

    """ start : 합의 시작 버튼 """
    def start(self, nodes, f, block, t):
        c = 23   # 여기
        #start = time.time()  # 시간 측정 시작
        self.request(nodes, block)  # request
        #print("request", time.time() - start)
        #print("request : %s" %nodes)
        if not self.pre_prepare(nodes, t):  # Pre-prepare
            return False
        #print("pre_prepare", time.time() - start)
        #print("pre_prepare : %s" %nodes)
        self.prepare(nodes, t, c)  # Prepare
        #print("prepare", time.time() - start)
        #print("prepare : %s" %nodes)
        self.preparedcertificate_commit(nodes, f, t)  # Preparedcertificate commit
        #print("preparedcertificate_commit", time.time() - start)
        #print("preparedcertificate_commit : %s" %nodes)
        self.commit(nodes, f, t, c)  # Commit
        #print("commit", time.time() - start)
        #print("commit : %s" %nodes)
        self.commit_certificate(nodes, f)  # Commit certificate
        #print("commit_certificate", time.time() - start)
        #print("commit_certificate : %s" %nodes)
        self.committed_certificate(nodes)  # Commited certificate
        #print("committed_certificate", time.time() - start)
        #print("commited_certificate : %s" %nodes)


        result = self.reply(nodes, f)  # Reply
        #print("reply", time.time() - start)

        #start = time.time()  # 시간 측정 시작
        self.faultdata_request(nodes, t)
        #self.Priority(nodes, t)
        #print("faultdata : %s" % nodes)
        #print("priority", time.time() - start)

        for i in range(1, len(nodes)):
            nodes[i][6].clear()
            nodes[i][7].clear()
            nodes[i][8].clear()

            nodes[i][4] = 0
            nodes[i][3] = 0
            nodes[i][2] = 0

        nodes[0][4] = 0


        return result
