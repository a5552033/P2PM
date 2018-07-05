#!/usr/bin/env python 
# encoding: utf-8


from __future__ import print_function
from __future__ import division
import copy
import math
import random
import time
from mosek_api import *

'''
CSchedule类
数据成员:
        reqArrivalRatio: 在某个时间段内request的到达率
        SLOTNUM: 将某个时间段分割成多少个时隙，现在一个时隙5mins
        reqNUM: 某个时间段内到达的request的数目
        outperformedReqs: ？
        rejectReqs: 某个时间段内拒绝的request数目
        acceptReqs: 某个时间段内接受的request数目
        linkCapacity: 每条链路上的容量，单位是bps
        highpriotraffic_upper:
        highpriotraffic_lower: 
        deadlinexpo: 越小deadline越大
        throughputexpo: 越大，每个timeslot吞吐量越大
        loadscalingfactor: =1
        maxtransferpereq: =1
        Maxint32: 32位二进制对应的最大十进制整数
        maxsinkNum: 每个request对应最大的sink数目
成员函数:
        loadPath(): 
        Optimization(): mosek构建优化模型，目的是判断reques是否可被接受

'''


class CSchedule:

    def __init__(self):
        self.SLOTNUM = 288  # 150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = 0
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 1600000  # 16000000
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
        self.loadPath()

        # time.clock()产生当前request的开始时间
        start_time = time.clock()
        self.totalSize = 0
        print("\nstart MIPOnline")
        freq = open("request.txt", "r")
        # freq.close()

        # self.request: 表示在第i个时隙到达的request
        # self.reqperSlot = [0 for slot in range(self.SLOTNUM)]
        # linkLoadSlot: 表示在第i条边上在j时隙上remain volumn
        linkLoadSlot2 = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        LinkResCaperSlot2 = copy.deepcopy(self.LinkCaperSlot)

        # tcur: 当前的slot time
        tcur = 0
        while tcur < self.SLOTNUM:
            # print "SLOTNUM, slot time:", self.SLOTNUM, tcur
            # ?
            line = freq.readline()
            reqperSlotcur = int(line)
            # self.reqNUM += self.reqperSlot[tcur]
            m_reqcount = 0
            # process the requests arrive in each slot
            while m_reqcount < reqperSlotcur:
                # print "reqperSlot, m_reqcount", self.reqperSlot[tcur], m_reqcount
                self.coeffPositive = True
                line = freq.readline()
                line = line.split()
                rsrc = int(line[0]) - 1
                r_start = int(line[1])
                r_end = int(line[2])
                rSize = int(line[3])
                sinkNum = int(line[4])
                rsink = []
                maybesrc = [rsrc]
                # sinkNum = random.randint(1, self.maxsinkNum)
                # 60%-75% node num as destnation dc
                while len(rsink) < sinkNum:
                    maybesrc.append(int(line[5 + len(rsink)]) - 1)
                    rsink.append(int(line[5 + len(rsink)]) - 1)

                rPathNum = self.PATHNUM
                rSlotNum = int(r_end - r_start + 1)
                self.totalSize += rSize
                m_reqcount += 1
                self.reqNUM += 1

                onesrcLinkonpath = [[[0.0 for p in range(rPathNum)] for d in range(sinkNum)] for e in
                                    range(self.LINKNUM)]
                src = maybesrc[0]
                for d in range(sinkNum):
                    sink = rsink[d]
                    for p in range(rPathNum):
                        for linkindex in range(len(self.PathList[src][sink][p])):
                            linkid = self.PathList[src][sink][p][linkindex]
                            onesrcLinkonpath[linkid][d][p] = 1.0

                reslinktimecap2 = [[0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM)]
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        reslinktimecap2[e][t] = LinkResCaperSlot2[e][t + r_start]

                #################acceptance-Maximize####################################
                competedest2, solu_xx, solu_ww, solu_yy, solu2_feasible = fixsrcMIPmodel(rPathNum, self.LINKNUM,
                                                                                         sinkNum, rSlotNum, rSize,
                                                                                         onesrcLinkonpath,
                                                                                         reslinktimecap2)
                # update,outperformed includes fraction completion
                if solu2_feasible == False or abs(competedest2 - sinkNum) > 0.1:
                    self.rejectReqs += 1
                    # print("The %d request is rejected" % self.reqNUM)
                if (solu2_feasible == True) and (abs(competedest2 - sinkNum) < 0.1):
                    self.acceptReqs += 1
                    # print("The %d request is accepted" % self.reqNUM)
                    # accept_mp2p += 1
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

                fl = open("acceptedratio_a.txt", "a")
                fl.writelines("%d %d %d %.2f%%" % (
                self.reqNUM, self.acceptReqs, self.rejectReqs, ((self.acceptReqs / self.reqNUM) * 100)))
                # print(self.acceptReqs / self.reqNUM)
                fl.writelines("\n")
                fl.close()
            tcur += 1

        freq.close()


if __name__ == "__main__":
    # print "start..."
    mschedule = CSchedule()
    mschedule.loadPath()
    mschedule.MIPOnline()
    # mschedule.AccelerationAlg()
    # test()
    print("end!!!")
