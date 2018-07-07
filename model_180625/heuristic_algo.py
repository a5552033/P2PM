#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
import copy
import math
import random
import numpy as np
from kshortestpath import *
from genRequest import *


class CSchedule:
    def __init__(self):
        self.SLOTNUM = 288  # 150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = 0
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 1600000  # 16000000
        self.loadscalingfactor = 1
        self.maxtransferpereq = 1  # 6
        self.Maxint32 = 2147483647  # the maximum size
        self.maxsinkNum = 4
        self.MAXTIMESLOTNUM = 300

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

    def SRCSemiFlexiable(self):
        print("\nstart Processing...")

        freq = open("request.txt", "r")

        self.totalSize = 0

        linkLoadSlot = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        # linkLoadSlot2 = [ [0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        # LinkCaperSlot的每个元素的单位是bps
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)
        judgeVariate = True  # type: bool

        tcur = 0
        while tcur < self.SLOTNUM:
            # print "SLOTNUM, slot time:", self.SLOTNUM, tcur
            line = freq.readline()
            reqperSlotcur = int(line)
            # print(reqperSlotcur)
            m_reqcount = 0  # type: int
            # process the requests arrive in each slot
            # while m_reqcount < self.reqperSlot[tcur]:
            while m_reqcount < reqperSlotcur:
                # print "reqperSlot, m_reqcount", self.reqperSlot[tcur], m_reqcount
                line = freq.readline()
                line = line.split()
                rsrc = int(line[0]) - 1
                r_start = int(line[1])
                r_end = int(line[2])
                rSize = int(line[3])
                rSize *= 8
                sinkNum = int(line[4])
                rsink = []
                new_src = [rsrc]

                # sinkNum = self.maxsinkNum
                while len(rsink) < sinkNum:
                    rsink.append(int(line[5 + len(rsink)]) - 1)
                    # print(int(line[4+len(rsink)]))
                # print(rSize)

                rPathNum = self.PATHNUM
                # rSlotNum = self.SLOTNUM
                rSlotNum = r_end - r_start + 1
                # print(rSlotNum)

                # self.totalSize += rSize
                m_reqcount += 1
                self.reqNUM += 1

                new_sink = rsink
                minTimeCost = 0
                lastMinTimeCost = [0]

                while len(new_sink) > 0:
                    numoftimeSlotfromSRCtoDST = [[0 for d in range(len(new_sink))] for s in range(len(new_src))]
                    pathCaptcur = [[[[0.0 for p in range(rPathNum)] for t in range(rSlotNum)] for d in range(len(new_sink))] for s in range(len(new_src))]

                    h = 1  # debug辅助变量

                    # 此for循环的作用是得到矩阵T和在t时刻，从源结点src到目的结点dst的第k条路径上需要占用的资源
                    for s in range(len(new_src)):
                        src = new_src[s]
                        for d in range(len(new_sink)):
                            sink = new_sink[d]
                            tempSize_2 = 0.0
                            for t in range(rSlotNum - lastMinTimeCost[s]):
                                tempSize_3 = 0.0
                                # pathidSize = []
                                for p in range(rPathNum):
                                    linkCostSetontcur = []
                                    for linkindex in range(len(self.PathList[src][sink][p])):
                                        linkid = self.PathList[src][sink][p][linkindex]
                                        # print(r_start, minTimeCost)
                                        linkCostSetontcur.append(
                                            LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[s]])

                                    tempSize = 0.0
                                    tempSize += int(min(linkCostSetontcur))

                                    pathCaptcur[s][d][t + lastMinTimeCost[s]][p] = tempSize
                                    tempSize_3 += tempSize

                                tempSize_2 += tempSize_3 * 300

                                h = 2
                                # print(tempSize_2)
                                if tempSize_2 >= rSize and t <= rSlotNum - lastMinTimeCost[s] - 1:
                                    numoftimeSlotfromSRCtoDST[s][d] = lastMinTimeCost[s] + t + 1
                                    break

                                elif tempSize_2 < rSize and t == rSlotNum - lastMinTimeCost[s] - 1:
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
                        for t in range(minTimeCost - lastMinTimeCost[m_min]):
                            # 如果只在一个时隙内就完成传输
                            if (minTimeCost - lastMinTimeCost[m_min]) == 1:
                                totalSize = 0
                                for p in range(rPathNum):
                                    totalSize += pathCaptcur[m_min][n_min][t + lastMinTimeCost[m_min]][p]

                                for p in range(rPathNum):
                                    ratio = pathCaptcur[m_min][n_min][t + lastMinTimeCost[m_min]][p] / totalSize
                                    partCostperPath = int(rSize / 300 * ratio)
                                    for linkindex in range(
                                            len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                        linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][linkindex]
                                        # partCostperLink = partCostperPath/len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])

                                        LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] -= partCostperPath
                                        if LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] <= 0:
                                            LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] = 0
                            else:
                                if t < (minTimeCost - lastMinTimeCost[m_min] - 1):
                                    for p in range(rPathNum):
                                        for linkindex in range(
                                                len(self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                            linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][linkindex]
                                            linkCostSetontcur = [LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]]]
                                            LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] -= min(linkCostSetontcur)

                                        totalSize_2 += pathCaptcur[m_min][n_min][t + lastMinTimeCost[m_min]][p]
                                        # print(pathCaptcur[m_min][n_min][t][p])
                                        # print(rSize)
                                else:
                                    remainSize = rSize - (totalSize_2 * 300)
                                    if totalSize_2 == 0:
                                        totalSize = 0
                                        for p in range(rPathNum):
                                            totalSize += pathCaptcur[m_min][n_min][t + lastMinTimeCost[m_min]][p]

                                        for p in range(rPathNum):
                                            ratio = pathCaptcur[m_min][n_min][t + lastMinTimeCost[m_min]][p] / totalSize
                                            partCostperPath = int(rSize / 300 * ratio)
                                            for linkindex in range(len(
                                                    self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                                linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][
                                                    linkindex]
                                                LinkResCaperSlot[linkid][
                                                    t + r_start + lastMinTimeCost[m_min]] -= partCostperPath
                                                if LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] < 0:
                                                    LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] = 0
                                    else:
                                        totalSize = 0
                                        for p in range(rPathNum):
                                            totalSize += pathCaptcur[m_min][n_min][t + lastMinTimeCost[m_min]][p]

                                        for p in range(rPathNum):
                                            ratio = pathCaptcur[m_min][n_min][t + lastMinTimeCost[m_min]][p] / totalSize
                                            costperLink = remainSize / 300 * ratio
                                            for linkindex in range(len(
                                                    self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p])):
                                                linkid = self.PathList[srctoSinkReadytoMove][sinkReadyMovetosrcList][p][
                                                    linkindex]
                                                LinkResCaperSlot[linkid][
                                                    t + r_start + lastMinTimeCost[m_min]] -= costperLink
                                                if LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] <= 0:
                                                    LinkResCaperSlot[linkid][t + r_start + lastMinTimeCost[m_min]] = 0

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
                        lastMinTimeCost.append(minTimeCost)
                        judgeVariate = True

                if judgeVariate:
                    self.acceptReqs += 1
                    print("The %d request is accepted!" % self.reqNUM)

                fl = open("acceptedratio_h.txt", "a")
                fl.writelines("%d %d %d %.2f%%" % (
                self.reqNUM, self.acceptReqs, self.rejectReqs, ((self.acceptReqs / self.reqNUM) * 100)))
                # print(self.acceptReqs / self.reqNUM)
                fl.writelines("\n")
                fl.close()
            # print(tcur)
            tcur += 1

        freq.close()

        # fl = open("acceptedratio_h.txt", "w")
        # fl.writelines("%d %d %d %.2f%%" % (self.reqNUM, self.acceptReqs, self.rejectReqs, ((self.acceptReqs / self.reqNUM) * 100)))
        # # print(self.acceptReqs / self.reqNUM)
        # fl.writelines("\n")
        # fl.close()


if __name__ == "__main__":
    # print "start..."
    mschedule = CSchedule()
    mschedule.loadPath()
    mschedule.SRCSemiFlexiable()
    # test()
    print("end!!!")
