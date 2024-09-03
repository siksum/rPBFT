
from typing import List
import time
import pandas as pd
import matplotlib.pyplot as plt


class Simulator:
    def __init__(self) -> None:
        self.latency: List = []
        self.throughput: List = []
        self.security: List = []
    
    def latency(self, i, x, y, latency, numberofNodes, numberofFaults):
        a = len(latency)
        latency = sum(latency)
        ave_latency = (latency / a)

        x[i] = i
        y[i] = ave_latency
        return x, y
    
    def throughput(self, i, x, y, throughput, numberofNodes, numberofFaults):
        a = len(throughput)
        throughput = sum(throughput)
        ave_throughput = (throughput / a)

        x[i] = i
        y[i] = ave_throughput
        return x, y
    
    def security(self, i, x, y, security, numberofNodes, numberofFaults):
        a = len(security)
        security = sum(security)
        ave_security = (security / a)

        x[i] = i
        y[i] = ave_security
        return x, y
    
    def plot(self, y, x, rel_name):
        data = pd.DataFrame(y, x)
        filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + rel_name + '.xlsx'
        data.to_excel(filename)

        # print(data)
        plt.plot(data, 'r-o')
        plt.xlabel("number of nodes")
        plt.ylabel("latency-average")
        plt.show()