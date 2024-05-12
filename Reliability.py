import numpy as np
import matplotlib.pyplot as plt
from reliability.Distributions import Weibull_Distribution, Lognormal_Distribution, Exponential_Distribution
import random


# 신뢰성 모델을 구조체처럼 쓰기 위해 사용하는 클래스
class rel_data:
    def __init__(self, name, faultrate):
        self.name = name
        self.faultrate = faultrate
        print(self.name, self.faultrate)


# 신뢰성 모델을 활용한 결함 확률 산출
class Reliability:
    def __init__(self):
        self.xvals = np.linspace(0, 1000, 1000)
        self.infant_mortality = rel_data('infant', Weibull_Distribution(alpha=400, beta=0.7).HF(xvals=self.xvals, show_plot=False))  # infant mortality [Weibull]
        self.random_failures = rel_data('random', Exponential_Distribution(Lambda=0.001).HF(xvals=self.xvals, show_plot=False))  # random failures [Exponential]
        self.wear_out = rel_data('wearout', Lognormal_Distribution(mu=6.8, sigma=0.1).HF(xvals=self.xvals, show_plot=False))  # wear out [Lognormal]
        self.combined = rel_data('combined', self.infant_mortality.faultrate + self.random_failures.faultrate + self.wear_out.faultrate)
        self.none = rel_data('none', [0 for i in range(0, 1000)])

    # 결함 확률을 a배 증폭하는 함수
    def amplifier(self, a, p):
        prob = rel_data(p.name, np.linspace(0, 1000, 1000))

        for i in range(1, 1000):
            prob.faultrate[i] = p.faultrate[i] * a

        return prob

    # 결함 확률을 a배 증폭, s개 슬라이싱하는 함수
    def generate(self, a, s, p):
        prob = self.amplifier(a, p)
        #print(prob.name, prob.faultrate)
        i = random.randint(0, 1000-s)
        #print(i, i+s)
        prob.faultrate = prob.faultrate[i : i+s]

        for j in range(0, len(prob.faultrate)):
            weights = [1 - prob.faultrate[j], prob.faultrate[j]]
            #print(j, weights)
            prob.faultrate[j] = int(random.choices([0, 1], weights)[0])
        #print(prob.faultrate)
        #print(prob.faultrate)
        return prob

    def generate2(self):
        prob = rel_data('general', [0, 0.1, 0.2, 0.3, 0.4, 0.5])

        print(prob.name, prob.faultrate)

        for j in range(0, len(prob.faultrate)):
            weights = [1 - prob.faultrate[j], prob.faultrate[j]]
            #print(j, weights)
            prob.faultrate[j] = int(random.choices([0, 1], weights)[0])
        #print(prob.faultrate)
        #print(prob.faultrate)
        return prob




    #a = random.choices([0, 1], weights=[0.3, 1])

    #print(a)
    # reliability_generator = Reliability()
    # infant = reliability_enerator.generate(50, 300, reliability_generator.infant_mortality)


    #reliability_generator = Reliability()
    #infant, random, wearout, combined, none = reliability_generator.test()

    #simulation_ProposedMethod(none)


#reliability_generator = Reliability()
#infant = reliability_generator.generate(50, 300, reliability_generator.infant_mortality)

#print(infant, infant.name, infant.faultrate)
#print(len(infant.faultrate))

"""


    #test : reliability 확률을 7000배하고, 빠른 테스트를 위해 100개를 뽑아 리턴하는 함수

    #show_plot=False

    def test(self):
        infant = [0 for i in range(len(self.infant_mortality))]
        random = [0 for i in range(len(self.random_failures))]
        wearout = [0 for i in range(len(self.wear_out))]
        combined = [0 for i in range(len(self.combined))]

        # 7000배
        for i in range(1, 1000):
            infant[i] = int(self.infant_mortality[i] * 7000)
            random[i] = int(self.random_failures[i] * 7000)
            wearout[i] = int(self.wear_out[i] * 7000)
            combined[i] = int(self.combined[i] * 7000)

        # 1000개 중 10개의 확률 뽑기
        infant = rel_data('infant', infant[1::10])
        random = rel_data('random', random[1::10])
        wearout = rel_data('wareout', wearout[1::10])
        combined = rel_data('combined', combined[1::10])

        none = rel_data('none', [0 for i in range(10)])

        return infant, random, wearout, combined, none

    def test2(self):
        infant = [0 for i in range(len(self.infant_mortality))]
        random = [0 for i in range(len(self.random_failures))]
        wearout = [0 for i in range(len(self.wear_out))]
        combined = [0 for i in range(len(self.combined))]

        # 7000배
        for i in range(1, 1000):
            infant[i] = int(self.infant_mortality[i] * 5000)
            random[i] = int(self.random_failures[i] * 5000)
            wearout[i] = int(self.wear_out[i] * 5000)
            combined[i] = int(self.combined[i] * 5000)

        none = rel_data('none', [0 for i in range(len(infant))])

        infant = rel_data('infant', infant)
        random = rel_data('random', random)
        wearout = rel_data('wareout', wearout)
        combined = rel_data('combined', combined)



        return infant, random, wearout, combined, none

"""