from Blockchain import *
from PBFT import *
from ProposedMethod import *
from Evaluation import *

import time
from tqdm import tqdm


def simulation_PBFT(rel=0):
    # Setting
    round = 1  # 라운드 수 (실제 실험은 1000 이상으로 설정)
    blockSize = "test"  # 블록 사이즈 : max(4MB), ave(1MB), test(10bytes) / (실제 실험은 max, ave로 설정)

    testcase = len(rel.faultrate)  # 테스트케이스 개수
    nodebase = 100  # 기본 노드 수
    consensus = PBFT()  # 합의 알고리즘

    numberofFaults = rel.faultrate  # 결함 노드 수
    # 노드 수 설정
    numberofNodes = [nodebase for i in
                     range(1, testcase + 1)]  # 배수로 테스트하고 싶을 때 [nodebase*1, nodebase*2, ... , nodebase*testcase]
    # numberofNodes = [nodebase**(i) for i in range(1, testcase+1)]   # 거듭제곱으로 테스트하고 싶을 때 [nodebase**1, nodebase**2, ... , nodebase**testcase]

    # 시뮬레이션 데이터(테스트 케이스 별 전체 라운드 데이터)
    data_latency = {}  # latency 측정 결과 데이터() : {numberofNodes : [latency1, latency2, ..., latencyround]}
    data_bps = {}  # bps 측정 결과 데이터() : {numberofNodes : [bps1, bps2, ..., bpsround]}
    data_security = {}  # security 측정 결과 데이터() : {numberofFaults : [security1, security2, ..., securityround]}


    # 시뮬레이션 데이터(테스트 케이스 별 평균값)
    x_l = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_l = [0 for j in range(testcase)]  # latency average : [latencyaverage100, latencyaverage200, ..., latencyaverage1000]

    x_b = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_b = [0 for j in range(testcase)]  # bps average : [bpsaverage100, bpsaverage200, ..., bpsaverage1000]

    x_s = [0 for j in range(testcase + 1)]  # numberofFaults : [10, 20, 30]
    y_s = [0 for j in range(testcase + 1)]  # security average : [securityaverage10, securityaverage100, securityaverage1000]

    for i in tqdm(range(0, testcase), desc=rel.name):
        latency = []  # 각 라운드별 latency 결과 저장 : [latencyround1, latencyround2, ...]
        bps = []  # 각 라운드별 bps 결과 저장 : [bpsround1, bpsround2, ...]
        security = []  # 각 라운드별 security 결과 저장 : [securityround1, securityround2, ...]

        count = 0
        while (count < round):
            start = time.time()  # 시간 측정 시작

            Blockchain.__init__(Blockchain, numberofNodes[i], numberofFaults[i], blockSize, consensus)  # 블록체인 초기화

            block = Blockchain.new_block(Blockchain)  # 블록 생성
            node = Blockchain.node(Blockchain, block)  # 노드 초기화

            result = Blockchain.consensus_start(Blockchain)  # result : 합의 결과(True, False)

            if result:
                Blockchain.add_block(Blockchain, block)
            else:
                Blockchain.delete_block(Blockchain)

            round_time = time.time() - start  # 라운드 소요 시간

            bps.append(((1e+6)*len(Blockchain.chain)) / round_time)  # 각 라운드별 bps 결과 저장
            latency.append(round_time)  # 각 라운드별 latency 결과 저장
            security.append(result)

            count += 1


        Testcase = str(i) + "(" + str(numberofNodes[i])+"/"+str(numberofFaults[i]) + ")"
        data_latency[Testcase] = latency  # 테스트 케이스 별 전체 라운드 latency값 저장
        data_bps[Testcase] = bps  # 테스트 케이스 별 전체 라운드 bps값 저장
        data_security[Testcase] = security  # 테스트 케이스 별 전체 라운드 security값 저장


        #print("Testcase : %s" %Testcase)
        evaluation_generator = Evaluation()
        x_l, y_l = evaluation_generator.latency(i, x_l, y_l, latency, round, numberofNodes[i], numberofFaults[i])  # 테스트 케이스 별 latency 평균값 저장
        x_b, y_b = evaluation_generator.bps(i, x_b, y_b, bps, round, numberofNodes[i], numberofFaults[i])  # 테스트 케이스 별 bps 평균값 저장
        x_s, y_s = evaluation_generator.security(i, x_s, y_s, security, round, numberofNodes[i], numberofFaults[i])  # 테스트 케이스 별 latency 평균값 저장

        i += 1

    evaluation_generator.latency_plot(y_l, x_l, rel.name)
    evaluation_generator.bps_plot(y_b, x_b, rel.name)
    evaluation_generator.security_plot(y_s, x_s, rel.name)

    filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + rel.name
    data1 = pd.DataFrame(data_latency)
    data1.to_excel(filename + '-latency-graph.xlsx')

    data2 = pd.DataFrame(data_bps)
    data2.to_excel(filename + '-bps-graph.xlsx')

    data3 = pd.DataFrame(data_security)
    data3.to_excel(filename + '-security-graph.xlsx')

def simulation_ProposedMethod(set):
    # Setting
    round = set['round']  # 라운드 수
    testcase = set['testcase'] # 테스트케이스 개수

    blockSize = set['blockSize']
    numberofNodes = set['numberofNodes']  # 기본 노드 수
    numberofFaults = set['reliability']  # 결함 노드 수
    reliabilitymodel = set['reliability'].name

    consensus = ProposedMethod()  # 합의 알고리즘

    # 시뮬레이션 데이터(테스트 케이스 별 전체 라운드 데이터)
    data_latency = {}  # latency 측정 결과 데이터() : {numberofNodes : [latency1, latency2, ..., latencyround]}
    data_bps = {}  # bps 측정 결과 데이터() : {numberofNodes : [bps1, bps2, ..., bpsround]}
    data_security = {}  # security 측정 결과 데이터() : {numberofFaults : [security1, security2, ..., securityround]}


    # 시뮬레이션 데이터(테스트 케이스 별 평균값)
    x_l = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_l = [0 for j in range(testcase)]  # latency average : [latencyaverage100, latencyaverage200, ..., latencyaverage1000]

    x_b = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_b = [0 for j in range(testcase)]  # bps average : [bpsaverage100, bpsaverage200, ..., bpsaverage1000]

    x_s = [0 for j in range(testcase + 1)]  # numberofFaults : [10, 20, 30]
    y_s = [0 for j in range(testcase + 1)]  # security average : [securityaverage10, securityaverage100, securityaverage1000]

    for i in tqdm(range(0, testcase), desc=reliabilitymodel):
        latency = []  # 각 라운드별 latency 결과 저장 : [latencyround1, latencyround2, ...]
        bps = []  # 각 라운드별 bps 결과 저장 : [bpsround1, bpsround2, ...]
        security = []  # 각 라운드별 security 결과 저장 : [securityround1, securityround2, ...]

        Blockchain.__init__(Blockchain, numberofNodes[i], numberofFaults[i], blockSize, consensus)  # 블록체인 초기화

        block = Blockchain.new_block(Blockchain)  # 블록 생성
        node = Blockchain.node(Blockchain, block)  # 노드 초기화


        count = 0
        while (count < round):
            start = time.time()  # 시간 측정 시작

            result = Blockchain.consensus_start(Blockchain)  # result : 합의 결과(True, False)

            if result:
                Blockchain.add_block(Blockchain, block)
            else:
                Blockchain.delete_block(Blockchain)

            round_time = time.time() - start  # 라운드 소요 시간

            bps.append(((1e+6)*len(Blockchain.chain)) / round_time)  # 각 라운드별 bps 결과 저장
            latency.append(round_time)  # 각 라운드별 latency 결과 저장
            security.append(result)

            count += 1


        Testcase = str(i) + "(" + str(numberofNodes[i])+"/"+str(numberofFaults[i]) + ")"
        data_latency[Testcase] = latency  # 테스트 케이스 별 전체 라운드 latency값 저장
        data_bps[Testcase] = bps  # 테스트 케이스 별 전체 라운드 bps값 저장
        data_security[Testcase] = security  # 테스트 케이스 별 전체 라운드 security값 저장


        #print("Testcase : %s" %Testcase)
        evaluation_generator = Evaluation()
        x_l, y_l = evaluation_generator.latency(i, x_l, y_l, latency, round, numberofNodes[i], numberofFaults[i])  # 테스트 케이스 별 latency 평균값 저장
        x_b, y_b = evaluation_generator.bps(i, x_b, y_b, bps, round, numberofNodes[i], numberofFaults[i])  # 테스트 케이스 별 bps 평균값 저장
        x_s, y_s = evaluation_generator.security(i, x_s, y_s, security, round, numberofNodes[i], numberofFaults[i])  # 테스트 케이스 별 latency 평균값 저장

        i += 1

    evaluation_generator.latency_plot(y_l, x_l, rel.name)
    evaluation_generator.bps_plot(y_b, x_b, rel.name)
    evaluation_generator.security_plot(y_s, x_s, rel.name)

    filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + rel.name
    data1 = pd.DataFrame(data_latency)
    data1.to_excel(filename + '-latency-graph.xlsx')

    data2 = pd.DataFrame(data_bps)
    data2.to_excel(filename + '-bps-graph.xlsx')

    data3 = pd.DataFrame(data_security)
    data3.to_excel(filename + '-security-graph.xlsx')

def sim_ProposedMethod(set):
    # 설정값 너무 많아져서 딕셔너리로 가져와버림 으아아ㅏㅇㄹ
    round = set['round']  # 라운드 수
    testcase = set['testcase']  # 테스트케이스 개수

    blockSize = set['blockSize']
    numberofNodes = set['numberofNodes']  # 기본 노드 수
    numberofFaults = set['reliability']  # 결함 노드 수
    reliabilitymodel = set['reliabilitymodel']
    nodes = set['nodes']

    consensus = ProposedMethod()  # 합의 알고리즘

    # 시뮬레이션 데이터(테스트 케이스 별 전체 라운드 데이터)
    data_latency = {}  # latency 측정 결과 데이터() : {numberofNodes : [latency1, latency2, ..., latencyround]}
    data_bps = {}  # bps 측정 결과 데이터() : {numberofNodes : [bps1, bps2, ..., bpsround]}
    data_security = {}  # security 측정 결과 데이터() : {numberofFaults : [security1, security2, ..., securityround]}

    # 시뮬레이션 데이터(테스트 케이스 별 평균값)
    x_l = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_l = [0 for j in range(testcase)]  # latency average : [latencyaverage100, latencyaverage200, ..., latencyaverage1000]

    x_b = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_b = [0 for j in range(testcase)]  # bps average : [bpsaverage100, bpsaverage200, ..., bpsaverage1000]

    x_s = [0 for j in range(testcase + 1)]  # numberofFaults : [10, 20, 30]
    y_s = [0 for j in range(testcase + 1)]  # security average : [securityaverage10, securityaverage100, securityaverage1000]

    for i in tqdm(range(0, round), desc=reliabilitymodel):
        latency = []  # 각 라운드별 latency 결과 저장 : [latencyround1, latencyround2, ...]
        bps = []  # 각 라운드별 bps 결과 저장 : [bpsround1, bpsround2, ...]
        security = []  # 각 라운드별 security 결과 저장 : [securityround1, securityround2, ...]

        blockchain = Blockchain(numberofNodes, blockSize, nodes, consensus)  # 블록체인 초기화


        for t in range(0, testcase):
            #print(t)
            start = time.time()  # 시간 측정 시작
            block = blockchain.new_block()  # 블록 생성
            blockchain.block = block

            result = blockchain.consensus_start(t)  # result : 합의 결과(True, False)

            if result:
                blockchain.add_block(block)
                round_time = time.time() - start  # 라운드 소요 시간
                bps.append(1e+6)

                # 각 라운드별 bps 결과 저장
                #bps.append(((1e+6)) / round_time)  # 각 라운드별 bps 결과 저장
            else:
                blockchain.delete_block()
                round_time = time.time() - start  # 라운드 소요 시간
                bps.append(0)  # 각 라운드별 bps 결과 저장
            """
            blockchain.consensus.faultdata_request(nodes, t)
            blockchain.consensus.Priority(nodes, t)

            for i in range(1, len(nodes)):
                nodes[i][6].clear()
                nodes[i][7].clear()
                nodes[i][8].clear()

                nodes[i][4] = 0
                nodes[i][3] = 0
                nodes[i][2] = 0

            nodes[0][4] = 0
            """


            latency.append(round_time)  # 각 라운드별 latency 결과 저장
            security.append(result)
        print(len(blockchain.chain))
        #print('latency', len(latency), latency)
        Testcase = str(i)
        data_latency[Testcase] = latency  # 테스트 케이스 별 전체 라운드 latency값 저장
        data_bps[Testcase] = bps  # 테스트 케이스 별 전체 라운드 bps값 저장
        data_security[Testcase] = security  # 테스트 케이스 별 전체 라운드 security값 저장
        #print('data_latency', len(data_latency), len(data_latency[Testcase]))

        # print("Testcase : %s" %Testcase)
        evaluation_generator = Evaluation()
        x_l, y_l = evaluation_generator.latency(i, x_l, y_l, latency, numberofNodes, t)  # 테스트 케이스 별 latency 평균값 저장
        x_b, y_b = evaluation_generator.bps(i, x_b, y_b, bps, numberofNodes, t)  # 테스트 케이스 별 bps 평균값 저장
        x_s, y_s = evaluation_generator.security(i, x_s, y_s, security, numberofNodes, t)  # 테스트 케이스 별 latency 평균값 저장

        #i += 1

    #evaluation_generator.latency_plot(y_l, x_l, reliabilitymodel)
    #evaluation_generator.bps_plot(y_b, x_b, reliabilitymodel)
    #evaluation_generator.security_plot(y_s, x_s, reliabilitymodel)

    filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + reliabilitymodel
    data1 = pd.DataFrame(data_latency)
    data1.to_excel(filename + '-latency-data.xlsx')

    data2 = pd.DataFrame(data_bps)
    #data2.to_excel(filename + '-bps-data.xlsx')

    data3 = pd.DataFrame(data_security)
    data3.to_excel(filename + '-security-data.xlsx')

def sim_PBFT(set):
    # 설정값 너무 많아져서 딕셔너리로 가져와버림 으아아ㅏㅇㄹ
    round = set['round']  # 라운드 수
    testcase = set['testcase']  # 테스트케이스 개수

    blockSize = set['blockSize']
    numberofNodes = set['numberofNodes']  # 기본 노드 수
    numberofFaults = set['reliability']  # 결함 노드 수
    reliabilitymodel = set['reliabilitymodel']
    nodes = set['nodes']

    consensus = PBFT()  # 합의 알고리즘

    # 시뮬레이션 데이터(테스트 케이스 별 전체 라운드 데이터)
    data_latency = {}  # latency 측정 결과 데이터() : {numberofNodes : [latency1, latency2, ..., latencyround]}
    data_bps = {}  # bps 측정 결과 데이터() : {numberofNodes : [bps1, bps2, ..., bpsround]}
    data_security = {}  # security 측정 결과 데이터() : {numberofFaults : [security1, security2, ..., securityround]}

    # 시뮬레이션 데이터(테스트 케이스 별 평균값)
    x_l = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_l = [0 for j in range(testcase)]  # latency average : [latencyaverage100, latencyaverage200, ..., latencyaverage1000]

    x_b = [0 for j in range(testcase)]  # numberofNodes : [100, 200, ..., 1000]
    y_b = [0 for j in range(testcase)]  # bps average : [bpsaverage100, bpsaverage200, ..., bpsaverage1000]

    x_s = [0 for j in range(testcase + 1)]  # numberofFaults : [10, 20, 30]
    y_s = [0 for j in range(testcase + 1)]  # security average : [securityaverage10, securityaverage100, securityaverage1000]

    for i in tqdm(range(0, round), desc=reliabilitymodel):
        latency = []  # 각 라운드별 latency 결과 저장 : [latencyround1, latencyround2, ...]
        bps = []  # 각 라운드별 bps 결과 저장 : [bpsround1, bpsround2, ...]
        security = []  # 각 라운드별 security 결과 저장 : [securityround1, securityround2, ...]

        blockchain = Blockchain(numberofNodes, blockSize, nodes, consensus)  # 블록체인 초기화


        for t in range(0, testcase):
            #print(t)
            start = time.time()  # 시간 측정 시작
            block = blockchain.new_block()  # 블록 생성
            blockchain.block = block

            result = blockchain.consensus_start(t)  # result : 합의 결과(True, False)

            if result:
                blockchain.add_block(block)
                round_time = time.time() - start  # 라운드 소요 시간
                bps.append(1e+6)  # 각 라운드별 bps 결과 저장
            else:
                blockchain.delete_block()
                round_time = time.time() - start  # 라운드 소요 시간
                bps.append(0)  # 각 라운드별 bps 결과 저장


            latency.append(round_time)  # 각 라운드별 latency 결과 저장
            security.append(result)
        print(len(blockchain.chain))
        #print('latency', len(latency), latency)
        Testcase = str(i)
        data_latency[Testcase] = latency  # 테스트 케이스 별 전체 라운드 latency값 저장
        data_bps[Testcase] = bps  # 테스트 케이스 별 전체 라운드 bps값 저장
        data_security[Testcase] = security  # 테스트 케이스 별 전체 라운드 security값 저장
        #print('data_latency', len(data_latency), len(data_latency[Testcase]))

        # print("Testcase : %s" %Testcase)
        evaluation_generator = Evaluation()
        x_l, y_l = evaluation_generator.latency(i, x_l, y_l, latency, numberofNodes, t)  # 테스트 케이스 별 latency 평균값 저장
        x_b, y_b = evaluation_generator.bps(i, x_b, y_b, bps, numberofNodes, t)  # 테스트 케이스 별 bps 평균값 저장
        x_s, y_s = evaluation_generator.security(i, x_s, y_s, security, numberofNodes, t)  # 테스트 케이스 별 latency 평균값 저장

        #i += 1

    #evaluation_generator.latency_plot(y_l, x_l, reliabilitymodel)
    #evaluation_generator.bps_plot(y_b, x_b, reliabilitymodel)
    #evaluation_generator.security_plot(y_s, x_s, reliabilitymodel)

    filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + reliabilitymodel
    data1 = pd.DataFrame(data_latency)
    data1.to_excel(filename + '-latency-data.xlsx')

    data2 = pd.DataFrame(data_bps)
    #data2.to_excel(filename + '-bps-data.xlsx')

    data3 = pd.DataFrame(data_security)
    data3.to_excel(filename + '-security-data.xlsx')


