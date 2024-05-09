import pandas as pd
import matplotlib.pyplot as plt
import time
import openpyxl


class Evaluation:
    def latency(self, i, x, y, latency, numberofNodes, numberofFaults):
        a = len(latency)
        latency = sum(latency)
        ave_latency = (latency / a)

        #print("The average latency is %0.9f" % ave_latency)

        #x[i] = numberofFaults/numberofNodes
        #x[i] = str(i)
        x[i] = i
        y[i] = ave_latency
        return x, y

    def latency_plot(self, y, x, rel_name):
        #print(y)
        #print(x)
        data = pd.DataFrame(y, x)
        filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + rel_name + '-latency-data.xlsx'
        data.to_excel(filename)

        # 데이터만 뽑을떼는 여기도 주석처리
        print(data)
        plt.plot(data, 'r-o')
        plt.xlabel("number of nodes")
        plt.ylabel("latency-average")
        plt.show()

    def bps(self, i, x, y, bps, numberofNodes, numberofFaults):
        a = len(bps)
        bps = sum(bps)
        ave_bps = (bps / a)
        #print("The average bps is %0.9f" % ave_bps)

        #x[i] = numberofFaults / numberofNodes
        x[i] = str(i)
        y[i] = ave_bps
        return x, y

    def bps_plot(self, y, x, rel_name):
        data = pd.DataFrame(y, x)
        filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + rel_name + '_bps-data.xlsx'

        data.to_excel(filename)

        # 데이터만 뽑을떼는 여기도 주석처리
        #plt.plot(data, 'r-o')
        #plt.xlabel("number of nodes")
        #plt.ylabel("bps-average")
        #plt.show()

    def security(self, i, x, y, security, numberofNodes, numberofFaults):
        a = len(security)
        security = sum(security)
        ave_security = (security / a)
        #print("The security is %0.9f" %ave_security)

        #x[i]= numberofFualts
        x[i] = str(i)
        y[i]= ave_security
        return x, y

    def security_plot(self, y, x, rel_name):
        data = pd.DataFrame(y,x)
        filename = 'data/' + time.strftime('%y%m%d-%H%M%S', time.localtime(time.time())) + '-' + rel_name + '-security-data.xlsx'

        data.to_excel(filename)

        # 데이터만 뽑을떼는 여기도 주석처리
        #plt.plot(data, 'r-o')
        #plt.xlabel("Number fo Fualt nodes")
        #plt.ylabel("Consensus Success Rate")
        #plt.show()
