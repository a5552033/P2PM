#!/usr/bin/env python 
# encoding: utf-8


from __future__ import print_function
from __future__ import division
import copy
import math
import random
import time
from kShortestPath import *
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

    def __init__(self):
        self.SLOTNUM = 288 #150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = 0
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 10000000   #16000000
        self.loadscalingfactor = 1
        self.Maxint32 = 2147483647  #the maximum size

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
        linkLoadSlot = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)

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

                Linkonpath = [[[[0.0 for p in range(rPathNum)] for d in range(sinkNum)] for s in range(sinkNum+1) ] for e in range(self.LINKNUM)]
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

                reslinktimecap = [[0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM)]
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        reslinktimecap[e][t] = LinkResCaperSlot[e][t+r_start]

                # ################acceptance-Maximize#################################### #
                start_time = time.clock()

                competedest, solu_x, solu_w, solu_y, solu_feasible = flexiblesrcMIPmodel(rPathNum, self.LINKNUM, sinkNum, rSlotNum, rSize, Linkonpath, reslinktimecap)

                end_time = time.clock()
                # update,outperformed includes fraction completion

                if solu_feasible == False or abs(competedest - sinkNum) > 0.1:
                    self.rejectReqs += 1
                if (solu_feasible == True) and (abs(competedest - sinkNum) < 0.1):
                    self.acceptReqs += 1
                    for s in range(sinkNum+1):
                        src = maybesrc[s]
                        for d in range(sinkNum):
                            sink = rsink[d]
                            for p in range(rPathNum):
                                for linkindex in range(len(self.PathList[src][sink][p])):
                                    linkid = self.PathList[src][sink][p][linkindex]
                                    for t in range(rSlotNum):
                                        LinkResCaperSlot[linkid][t+r_start] -= solu_y[(s*sinkNum+d)*rPathNum*rSlotNum+p*rSlotNum+t]
                                        linkLoadSlot[linkid][t+r_start] += solu_y[(s*sinkNum+d)*rPathNum*rSlotNum+p*rSlotNum+t]

                fl = open("acceptedratio_flexible.txt", "a")
                fl.writelines("%d %d %d %.2f%% %f" % (self.reqNUM, self.acceptReqs, self.rejectReqs, ((self.acceptReqs / self.reqNUM) * 100), (end_time - start_time)))
                # print(self.acceptReqs / self.reqNUM)
                fl.writelines("\n")
                fl.close()

            tcur += 1

        freq.close()


if __name__ == "__main__":
    #print "start..."
    mschedule = CSchedule()
    mschedule.loadPath()
    mschedule.MIPOnline()
    print("end!!!")
