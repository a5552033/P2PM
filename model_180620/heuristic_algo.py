#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import copy
import math
import random
import numpy as np
from kshortestpath import *


class CSchedule:
    def __init__(self, arriratio):
        self.reqArrivalRatio = arriratio
        self.SLOTNUM = 288  # 150 #1slot= 5mins  24h = 288slots
        self.MAXTIMESLOTNUM = 300
        self.reqNUM = 0
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 16000000 # 16000000
        self.highpriotraffic_upper = 0.15
        self.highpriotraffic_lower = 0.05
        self.deadlinexpo = 0.18  # 0.083 #0.083  ###end time slot according with exppenntioonal  distributioon，0.083=1/1hour=1/12slots
        self.throughputexpo = 1.0 / 20000000  # 1.0/20000000#  600000##20Gbps, throughput according with exppenntioonal  distributioon
        self.loadscalingfactor = 1
        self.maxtransferpereq = 1  # 6
        self.Maxint32 = 2147483647  # the maximum size
        self.maxsinkNum = 4

    def loadPath(self):
        f = open("linkonpath.txt", "r")
        line = f.readline()
        line = line.split()
        self.NODENUM = int(line[0])
        self.LINKNUM = int(line[1])
        self.PATHNUM = int(line[2])
        # this variate presents c_e_t, and 16Gps/link
        self.LinkCaperSlot = [[self.linkCapacity for col in range(self.SLOTNUM)] for row in range(self.LINKNUM)]

        # 实际网络中，要预留出一部分的带宽
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                interact = random.uniform(self.highpriotraffic_lower, self.highpriotraffic_upper)
                interact = 1 - interact
                self.LinkCaperSlot[linkid][slotid] *= interact

        # this variate presents
        self.PathList = [[[[] for num in range(self.PATHNUM)] for col in range(self.NODENUM)] for row in
                         range(self.NODENUM)]
        line = f.readline()
        pathid = 0
        while line:
            line = line.split()
            srcID = int(line[0]) - 1
            sinkID = int(line[1]) - 1

            for i in range(len(line) - 2):
                self.PathList[srcID][sinkID][pathid % self.PATHNUM].append(int(line[i + 2]) - 1)
            line = f.readline()
            pathid += 1

        f.close()

    def SRCSemiFlexiable(self):
        print("\nstart Processing...")

        freq = open("request.txt", "w")

        self.totalSize = 0
        m_throughput = 0
        m_acceptRatio = 0.0

        self.reqperSlot = [0 for slot in range(self.SLOTNUM)]
        linkLoadSlot = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        # linkLoadSlot2 = [ [0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        # LinkCaperSlot的每个元素的单位是bps
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)
        # LinkResCaperSlot2 = copy.deepcopy(self.LinkCaperSlot)

        judgeVariate = True  # type: bool

        tcur = 0
        while tcur < self.SLOTNUM:
            # print "SLOTNUM, slot time:", self.SLOTNUM, tcur
            for slotid in range(self.reqArrivalRatio):
                arrivalslot = int(random.expovariate(1.0 / self.reqArrivalRatio))
                if (tcur + arrivalslot) < self.SLOTNUM:
                    self.reqperSlot[tcur + arrivalslot] += self.maxtransferpereq

            # self.reqNUM += self.reqperSlot[tcur]

            m_reqcount = 0  # type: int
            freq.writelines("%d" % self.reqperSlot[tcur])
            freq.writelines("\n")
            # process the requests arrive in each slot
            # while m_reqcount < self.reqperSlot[tcur]:
            while m_reqcount < self.reqperSlot[tcur]:

                # print "reqperSlot, m_reqcount", self.reqperSlot[tcur], m_reqcount
                rsrc = random.randint(0, self.NODENUM - 1)
                rsink = []
                new_src = [rsrc]

                # 60%-75% node num as destnation dc
                sinkNum = random.randint(int(self.NODENUM * 0.6), int(self.NODENUM * 0.75))
                # sinkNum = self.maxsinkNum
                while len(rsink) < sinkNum:
                    newsink = random.randint(0, self.NODENUM - 1)
                    if newsink != rsrc and newsink not in rsink:
                        rsink.append(newsink)
                        # maybesrc.append(newsink)

                rthroughput = int(random.expovariate(self.throughputexpo))  # expotentional distribution 20Gbps

                # tcur = 0
                r_start = tcur
                r_end = self.SLOTNUM - 1
                if r_start == (self.SLOTNUM - 1):
                    r_end = self.SLOTNUM - 1
                else:
                    r_end = self.SLOTNUM
                    while r_end >= self.SLOTNUM:
                        r_end = math.ceil(r_start + random.expovariate(self.deadlinexpo))  # expotentional distribution，1/1hour=1/12slots

                # rSize的单位是bytes, 换算成bit*8
                rSize = int(rthroughput * (r_end - r_start + 1))
                rSize *= self.loadscalingfactor
                if rSize > self.Maxint32:
                    rSize = self.Maxint32

                rSize *= 8

                # print(rSize)

                rPathNum = self.PATHNUM
                rSlotNum = int(r_end - r_start + 1)
                # rSlotNum = self.SLOTNUM
                # print(rSlotNum)

                freq.seek(0, 2)
                freq.writelines("%d %d %d %d %d " % (rsrc + 1, r_start, r_end, rSize, len(rsink)))
                for dst in range(len(rsink)):
                    freq.writelines("%d " % (rsink[dst] + 1))
                freq.writelines("\n")

                # self.totalSize += rSize
                m_reqcount += 1
                self.reqNUM += 1

                new_sink = rsink
                minTimeCost = 0
                lastMinTimeCost = 0
                while len(new_sink) > 0:
                    numoftimeSlotfromSRCtoDST = [[0 for d in range(len(new_sink))] for s in range(len(new_src))]
                    pathCaptcur = [[[[0.0 for p in range(rPathNum)] for t in range(rSlotNum - lastMinTimeCost)] for d in range(len(new_sink))] for s in range(len(new_src))]

                    h = 1  # 辅助变量

                    # 此for循环的作用是得到矩阵T和在t时刻，从源结点src到目的结点dst的第k条路径上需要占用的资源
                    for s in range(len(new_src)):
                        src = new_src[s]
                        for d in range(len(new_sink)):
                            sink = new_sink[d]
                            tempSize_2 = 0.0
                            for t in range(rSlotNum - lastMinTimeCost):
                                # pathidSize = []
                                for p in range(rPathNum):
                                    linkCostSetontcur = []
                                    for linkindex in range(len(self.PathList[src][sink][p])):
                                        linkid = self.PathList[src][sink][p][linkindex]
                                        # print(r_start, minTimeCost)
                                        linkCostSetontcur.append(LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost])

                                    tempSize = 0.0
                                    tempSize += int(min(linkCostSetontcur))

                                    pathCaptcur[s][d][t][p] = tempSize
                                    tempSize_2 += tempSize

                                h = 2
                                # print(tempSize_2)
                                if (tempSize_2 * 300 * (t+1)) >= rSize and t <= rSlotNum - lastMinTimeCost - 1:
                                    numoftimeSlotfromSRCtoDST[s][d] = lastMinTimeCost + t + 1
                                    break

                                elif (tempSize_2 * 300 * (t+1)) < rSize and t == rSlotNum - lastMinTimeCost - 1:
                                    numoftimeSlotfromSRCtoDST[s][d] = self.MAXTIMESLOTNUM

                    # 此模块求矩阵T中最小元素及其在矩阵T中的横纵坐标
                    tempMat = np.array(numoftimeSlotfromSRCtoDST)
                    # print(tempMat)
                    # 初始化时，因为只有一个源结点，跳转
                    if len(tempMat) == 1:
                        tempList = []
                        for i in range(len(tempMat[0])):
                            tempList.append(tempMat[0][i])
                        minTimeCost = min(tempList)
                        m_min = 0
                        n_min = tempList.index(minTimeCost)

                    else:
                        raw, column = tempMat.shape
                        m_min, n_min = divmod(np.argmin(tempMat), column)
                        minTimeCost = tempMat[m_min][n_min]

                    sinkReadyMovetosrcList = new_sink[n_min]
                    srctoSinkReadytoMove = new_src[m_min]
                    # tcur = minTimeCost+r_start
                    # print(" %d %d %d" % (tcur, sinkReadyMovetosrcList, srctoSinkReadytoMove))

                    # 如果最小的时间消耗都是无穷大的，那此request要被拒绝
                    if minTimeCost < self.MAXTIMESLOTNUM:
                        totalSize_2 = 0
                        # update c_e_t
                        for t in range(minTimeCost - lastMinTimeCost):
                            # 如果只在一个时隙内就完成传输
                            if (minTimeCost - lastMinTimeCost) == 1:
                                totalSize = 0
                                for p in range(rPathNum):
                                    totalSize += pathCaptcur[m_min][n_min][t][p]

                                for p in range(rPathNum):
                                    ratio = pathCaptcur[m_min][n_min][t][p] / totalSize
                                    partCostperPath = int(rSize / 300 * ratio)
                                    for linkindex in range(len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                        linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][linkindex]
                                        # partCostperLink = partCostperPath/len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])

                                        LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] -= partCostperPath
                                        if LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] <= 0:
                                            LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] = 0
                            else:
                                if t < (minTimeCost - lastMinTimeCost - 1):
                                    for p in range(rPathNum):
                                        for linkindex in range(len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                            linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][linkindex]
                                            linkCostSetontcur = [LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost]]
                                            LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] -= min(linkCostSetontcur)

                                        totalSize_2 += pathCaptcur[m_min][n_min][t][p]
                                        # print(pathCaptcur[m_min][n_min][t][p])
                                        # print(rSize)
                                else:
                                    remainSize = rSize - (totalSize_2 * 300 *(minTimeCost - lastMinTimeCost - 1))
                                    if totalSize_2 == 0:
                                        totalSize = 0
                                        for p in range(rPathNum):
                                            totalSize += pathCaptcur[m_min][n_min][t][p]

                                        for p in range(rPathNum):
                                            ratio = pathCaptcur[m_min][n_min][t][p] / totalSize
                                            partCostperPath = int(rSize / 300 * ratio)
                                            for linkindex in range(len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                                linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][linkindex]
                                                LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] -= partCostperPath
                                                if LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] < 0:
                                                    LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] = 0
                                    else:
                                        totalSize = 0
                                        for p in range(rPathNum):
                                            totalSize += pathCaptcur[m_min][n_min][t][p]

                                        for p in range(rPathNum):
                                            ratio = pathCaptcur[m_min][n_min][t][p] / totalSize
                                            costperLink = remainSize / 300 * ratio
                                            for linkindex in range(len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                                linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][linkindex]
                                                LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] -= costperLink
                                                if LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] <= 0:
                                                    LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost] = 0

                    else:
                        self.rejectReqs += 1
                        print("The %d request is rejected because the resource is used." % self.reqNUM)
                        judgeVariate = False
                        break

                    # 如果new_sink里面有相同的元素，就删除排在前面的那一个
                    new_sink.remove(sinkReadyMovetosrcList)
                    new_src.append(sinkReadyMovetosrcList)

                    if (minTimeCost >= rSlotNum) and (len(new_sink) > 0):
                        print("The %d request is rejected because of time out!" % self.reqNUM)
                        self.rejectReqs += 1
                        judgeVariate = False
                        break
                    else:
                        # print(minTimeCost)
                        lastMinTimeCost = minTimeCost
                        judgeVariate = True

                if judgeVariate:
                    self.acceptReqs += 1
                    print("The %d request is accepted!" % self.reqNUM)

            # print(tcur)
            tcur += 1

        freq.close()
        print(self.reqNUM, self.acceptReqs, self.rejectReqs)


arriratio = 2

if __name__ == "__main__":
    # print "start..."
    # mgraph = CGraph()
    # mgraph.outputKshortestPath()
    mschedule = CSchedule(arriratio)
    mschedule.loadPath()
    mschedule.SRCSemiFlexiable()
    # test()
    print("end!!!")
