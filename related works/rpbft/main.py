from Blockchain import *
from PBFT import *
from Reliability import *
from Node import *
from Simulations import *


if __name__ == "__main__":
    for i in range(0, 100):
        round = 1
        blockSize = "ave"  # 블록 사이즈 : max(4MB), ave(1MB), test(10bytes) / (실제 실험은 max, ave로 설정)

        a = 50  # 결함확률 증폭 정도  ## 1000이면 20/40 300이면 50
        s = 300  # 결함확률 슬라이스 수

        numberofNodes = 40

        # 신뢰성 모델 생성
        reliability_generator = Reliability()
        reliability_infant = []
        reliability_wearout = []
        reliability_random = []
        reliability_combined = []
        reliability_none = []
        for i in range(0, numberofNodes):
            reliability_infant.append(reliability_generator.generate(a, s, reliability_generator.infant_mortality))
            reliability_wearout.append(reliability_generator.generate(a, s, reliability_generator.wear_out))
            reliability_random.append(reliability_generator.generate(a, s, reliability_generator.random_failures))
            reliability_combined.append(reliability_generator.generate(a, s, reliability_generator.combined))
            reliability_none.append(reliability_generator.generate(a, s, reliability_generator.none))

        print(reliability_infant)
        # print(len(reliability_infant))
        print(reliability_combined[0].faultrate)
        # print(reliability_combined[1].faultrate)
        # 노드 생성
        infant_node_generator = Node(numberofNodes, reliability_infant)
        nodes_infant = infant_node_generator.generate()  # print(nodes[0])   # [0, <Reliability.rel_data object at 0x1231e4970>, 0, 0, 0, None, [], [], [], []]

        # 설정값 리스트로 넘겨버리기
        set_infant = {
            'round': round,
            'testcase': s,
            'blockSize': blockSize,
            'numberofNodes': numberofNodes,
            'reliability': reliability_infant,
            'reliabilitymodel': reliability_infant[0].name,
            'nodes': nodes_infant
        }

        combined_node_generator = Node(numberofNodes, reliability_combined)
        nodes_combined = combined_node_generator.generate()  # print(nodes[0])   # [0, <Reliability.rel_data object at 0x1231e4970>, 0, 0, 0, None, [], [], [], []]

        # 설정값 리스트로 넘겨버리기
        set_combined = {
            'round': round,
            'testcase': s,
            'blockSize': blockSize,
            'numberofNodes': numberofNodes,
            'reliability': reliability_combined,
            'reliabilitymodel': reliability_combined[0].name,
            'nodes': nodes_combined
        }

        none_node_generator = Node(numberofNodes, reliability_none)
        nodes_none = none_node_generator.generate()  # print(nodes[0])   # [0, <Reliability.rel_data object at 0x1231e4970>, 0, 0, 0, None, [], [], [], []]

        # 설정값 리스트로 넘겨버리기
        set_none = {
            'round': round,
            'testcase': s,
            'blockSize': blockSize,
            'numberofNodes': numberofNodes,
            'reliability': reliability_none,
            'reliabilitymodel': reliability_none[0].name,
            'nodes': nodes_none
        }

        random_node_generator = Node(numberofNodes, reliability_random)
        nodes_random = random_node_generator.generate()  # print(nodes[0])   # [0, <Reliability.rel_data object at 0x1231e4970>, 0, 0, 0, None, [], [], [], []]

        # 설정값 리스트로 넘겨버리기
        set_random = {
            'round': round,
            'testcase': s,
            'blockSize': blockSize,
            'numberofNodes': numberofNodes,
            'reliability': reliability_random,
            'reliabilitymodel': reliability_random[0].name,
            'nodes': nodes_random
        }
        wearout_node_generator = Node(numberofNodes, reliability_wearout)
        nodes_wearout = wearout_node_generator.generate()  # print(nodes[0])   # [0, <Reliability.rel_data object at 0x1231e4970>, 0, 0, 0, None, [], [], [], []]

        # 설정값 리스트로 넘겨버리기
        set_wearout = {
            'round': round,
            'testcase': s,
            'blockSize': blockSize,
            'numberofNodes': numberofNodes,
            'reliability': reliability_wearout,
            'reliabilitymodel': reliability_wearout[0].name,
            'nodes': nodes_wearout
        }


        sim_PBFT(set_none)
        sim_PBFT(set_combined)
        #sim_PBFT(set_random)
        #sim_PBFT(set_wearout)
        #sim_PBFT(set_infant)


        #sim_ProposedMethod(set_none)
        #sim_ProposedMethod(set_combined)
        #sim_ProposedMethod(set_random)
        #sim_ProposedMethod(set_wearout)
        #sim_ProposedMethod(set_infant)

        # proposedmethod = ProposedMethod()
        # blockchain = Blockchain(set_infant['numberofNodes'], set_infant['blockSize'], set_infant['nodes'], proposedmethod)  # 블록체인 초기화

        # block = blockchain.new_block()  # 블록 생성
        # blockchain.add_block(block)

        # t = 0
        # proposedmethod.start(setting['nodes'], 2, block, t)

        # for i in range(0, 10):
        # blockchain.consensus_start(i)

        # sim_ProposedMethod(set_infant)

        """
        print(node)
        print(len(node))   # numberofNodes
        print(node[9][1])   # Reliability class
        print(node[9][1].name)   # infant
        print(node[9][1].faultrate)   # [0, 1, ...]
        """
        # reliability_generator = Reliability()
        # infant, random, wearout, combined, none = reliability_generator.test()
        # infant, random, wearout, combined, none = reliability_generator.test2()

        # print(len(infant.faultrate))
        # print(infant.faultrate)

        # simulation_PBFT(combined)

        # simulation_ProposedMethod(none)
        # simulation_ProposedMethod(infant)
        # simulation_PBFT(random)
        # simulation_ProposedMethod(wearout)
        # simulation_ProposedMethod(combined)

        # simulation_PBFT_security()
        # simulation_PBFT_security(infant)

        # simulation_PBFT_reliability(random)
        # simulation_PBFT_reliability(wearout)
        # simulation_PBFT_reliability(combined)
