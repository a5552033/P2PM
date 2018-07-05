#!/usr/bin/env python
# encoding: utf-8

from mosek_api import *
from kShortestPath import *
import time
import copy
import random

'''
CSchedule类
数据成员:
        reqArrivalRatio: 在某个时间段内request的到达率
        SLOTNUM: 将某个时间段分割成多少个时隙，现在一个时隙5mins
        reqNUM: 某个时间段内到达的request的数目
        outperformedReqs: ？
        rejectReqs: 某个时间段内拒绝的request数目
        acceptReqs: 某个时间段内接受的request数目
        linkCapacity: 
        highpriotraffic_upper:
        highpriotraffic_lower: 
        deadlinexpo:
        throughputexpo:
        loadscalingfactor: 
        maxtransferpereq: 
        Maxint32: 
        maxsinkNum: 
成员函数:
        loadPath(): 
        Optimization(): mosek构建优化模型，目的是判断reques是否可被接受

'''


class CSchedule:

    def __init__(self, arriratio):
        self.reqArrivalRatio = arriratio
        self.SLOTNUM = 5  # 150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = 0
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 160000000  # 16000000
        self.highpriotraffic_upper = 0.15
        self.highpriotraffic_lower = 0.05
        self.deadlinexpo = 0.18  # 0.083 #0.083  ###end time slot according with exppenntioonal  distributioon，0.083=1/1hour=1/12slots
        self.throughputexpo = 1.0 / 20000000  # 1.0/20000000#  600000##20Gps, throughput according with exppenntioonal  distributioon
        self.loadscalingfactor = 1
        self.maxtransferpereq = 1  # 6
        self.Maxint32 = 2147483647  # the maximum size
        self.maxsinkNum = 4

    def loadPath(self):
        f = open("linkonpath.txt", "r")
        line = f.readline()
        line = line.split()
        # 第一行读取整个网络拓扑的属性：依次为网络中的结点数，边数和 k-shortest-path的k值
        self.NODENUM = int(line[0])
        self.LINKNUM = int(line[1])
        self.PATHNUM = int(line[2])
        # 每个时隙每条链路上的容量或者带宽初始化为self.linkCapacity = 16000000
        self.LinkCaperSlot = [[self.linkCapacity for col in range(self.SLOTNUM)] for row in range(self.LINKNUM)]
        # 指示函数初始化，4维
        self.PathList = [[[[] for num in range(self.PATHNUM)] for col in range(self.NODENUM)] for row in
                         range(self.NODENUM)]

        line = f.readline()
        pathid = 0
        while line:
            line = line.split()
            srcID = int(line[0]) - 1
            sinkID = int(line[1]) - 1

            # for循环的作用在于将结点“srcID”到结点“sinkID”的第pathid%self.PATHNUM条路上存在编号为line[i+2])-1的边
            for i in range(len(line) - 2):
                self.PathList[srcID][sinkID][pathid % self.PATHNUM].append(int(line[i + 2]) - 1)
            line = f.readline()
            pathid += 1
        f.close()

    def MIPOnline(self):
        accept_mp2p = 0
        self.loadPath()
        self.totalSize = 0

        print ("\nstart MIPOnline")
        freq = open("request.txt", "w")

        linkLoadSlot2 = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        # ？
        LinkResCaperSlot2 = copy.deepcopy(self.LinkCaperSlot)

        m_reqcount = 0
        # process the requests arrive in each slot
        while m_reqcount < 1:
            sinkNum = 1
            while sinkNum < self.NODENUM:
                self.coeffPositive = True

                rsrc = 0
                rsink = []
                maybesrc = [rsrc]

                while len(rsink) < sinkNum:
                    newsink = random.randint(0, self.NODENUM - 1)
                    if newsink != rsrc and newsink not in rsink:
                        rsink.append(newsink)
                        maybesrc.append(newsink)

                rthroughput = int(random.expovariate(self.throughputexpo))  # expotentional distribution 20Gbps

                r_start = 0
                r_end = self.SLOTNUM

                rSize = int(rthroughput * (r_end - r_start + 1))
                rSize = self.loadscalingfactor * rSize
                if rSize > self.Maxint32:
                    rSize = self.Maxint32

                rPathNum = self.PATHNUM
                rSlotNum = int(r_end - r_start)
                # rSlotNum = int(r_end - r_start + 1)
                freq.seek(0, 2)
                # freq = open("request.txt","a")
                freq.writelines("%d %d %d %d %d " % (rsrc + 1, r_start, r_end, rSize, len(rsink)))
                for dest in range(len(rsink)):
                    freq.writelines("%d " % (rsink[dest] + 1))

                self.totalSize += rSize
                m_reqcount += 1

                onesrcLinkonpath = [[[0.0 for p in range(rPathNum)] for d in range(sinkNum)] for e in
                                    range(self.LINKNUM)]
                src = maybesrc[0]
                for d in range(sinkNum):
                    sink = rsink[d]
                    for p in range(rPathNum):
                        for linkindex in range(len(self.PathList[src][sink][p])):
                            linkid = self.PathList[src][sink][p][linkindex]
                            onesrcLinkonpath[linkid][d][p] = 1.0

                Linkonpath = [[[[0.0 for p in range(rPathNum)] for d in range(sinkNum)] for s in range(sinkNum + 1)] for
                              e in range(self.LINKNUM)]
                for s in range(sinkNum + 1):
                    src = maybesrc[s]
                    for d in range(sinkNum):
                        sink = rsink[d]
                        if src == sink:
                            continue
                        for p in range(rPathNum):
                            for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                Linkonpath[linkid][s][d][p] = 1.0

                reslinktimecap2 = [[0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM)]
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        reslinktimecap2[e][t] = LinkResCaperSlot2[e][t + r_start]

                #################acceptance-Maximize####################################
                # limit the data source of a receiver to be no more than 1
                start_time_clock = time.clock()
                competedest2, solu_xx, solu_ww, solu_yy, solu2_feasible = fixsrcMIPmodel(rPathNum, self.LINKNUM,
                                                                                         sinkNum, rSlotNum, rSize,
                                                                                         onesrcLinkonpath,
                                                                                         reslinktimecap2)
                end_time_clock = time.clock()

                # update,outperformed includes fraction completion
                if (solu2_feasible == True) and (abs(competedest2 - sinkNum) < 0.1):
                    accept_mp2p += 1
                    src = maybesrc[0]
                    for d in range(sinkNum):
                        sink = rsink[d]
                        for p in range(rPathNum):
                            for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                for t in range(rSlotNum):
                                    # print len(solu_yy), d, p, t
                                    LinkResCaperSlot2[linkid][t + r_start] -= solu_yy[
                                        d * rPathNum * rSlotNum + p * rSlotNum + t]
                                    linkLoadSlot2[linkid][t + r_start] += solu_yy[
                                        d * rPathNum * rSlotNum + p * rSlotNum + t]

                elapsed_time_clock = end_time_clock - start_time_clock
                freq.writelines("%f" % elapsed_time_clock)
                freq.writelines("\n")

                fprint = open("print_2.txt", "w")
                fprint.writelines("deadline = %d have been computed" % sinkNum)
                fprint.close()

                sinkNum += 1

        freq.close()


arriratio = 2

if __name__ == "__main__":
    print "start..."
    mschedule = CSchedule(arriratio)
    mschedule.loadPath()
    mschedule.MIPOnline()
    # mschedule.AccelerationAlg()
    # test()
    print("end!!!")
