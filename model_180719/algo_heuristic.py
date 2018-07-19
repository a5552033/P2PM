#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
import networkx as nx
import matplotlib.pyplot as plt
import pandas
from node import *
from link import *
import copy
import math
import random
import time
import numpy as np
from kShortestPath import *
from genRequest import *


class CSchedule:
    def __init__(self):
        self.SLOTNUM = 288  # 150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = 0
        self.LINK_DICT = {}  # (src-,sink)-link
        self.LINK_LIST = []  # linkid-link
        self.NODE_DICT = {}
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 100000  # 16000000
        self.loadscalingfactor = 1
        self.MAXTIMESLOTNUM = 300

    def loadPath(self):
        f = open("linkonpath.txt", "r")
        fn = open("nodeonpath.txt", "r")
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
        self.PathList_node = [[[[] for num in range(self.PATHNUM)] for col in range(self.NODENUM)] for row in range(self.NODENUM)]

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

        line2 = fn.readline()
        pathid_node = 0
        while line2:
            line2 = line2.split()
            srcID = int(line2[0]) - 1
            sinkID = int(line2[len(line2)-1])-1

            for i in range(len(line2) - 2):
                self.PathList_node[srcID][sinkID][pathid_node % self.PATHNUM].append(int(line2[i + 1]) - 1)
            line2 = fn.readline()
            pathid_node += 1

        f.close()
        fn.close()

    def loadPathNodes(self):
        f = open("reqNodes.txt", "r")
        line = f.readline()
        while line:
            line = line.split("\t")
            nodeID = int(line[0])
            # NODE_LIST.append(CNode(nodeID))
            # self.NODE_DICT = {}
            self.NODE_DICT[nodeID] = CNode(nodeID)
            line = f.readline()

        f.close()

    def loadPathLinks(self):
        f = open("reqLinks.txt", "r")
        line = f.readline()
        # edge = edge.split()
        # print(edge[2])
        while line:
            edge = str(line).split("\t")
            src = int(edge[0])
            sink = int(edge[1])
            weight = int(edge[2])
            linkid = int(edge[3])
            if src not in self.LINK_DICT.keys():
                self.LINK_DICT[src] = {}
            if sink not in self.LINK_DICT[src].keys():
                self.LINK_DICT[src][sink] = None

            self.LINK_DICT[src][sink] = CLink(src, sink, linkid, weight)
            self.LINK_LIST.append(CLink(src, sink, linkid, weight))
            line = f.readline()
        f.close()

    def geneTopo(self):
        self.topo = nx.Graph()
        for node in self.NODE_DICT:
            self.topo.add_node(node)

        for src in self.LINK_DICT:
            for sink in self.LINK_DICT[src]:
                self.topo.add_edges_from([(src, sink)])
                self.topo.add_edge(src, sink, capacity=self.LINK_DICT[src][sink].weight)

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
        while tcur < (self.SLOTNUM -1):
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
                timeAsrc = [0]

                start_time = time.clock()

                while len(new_sink) > 0:
                    numoftimeSlotfromSRCtoDST = [[0 for d in range(len(new_sink))] for s in range(len(new_src))]
                    # pathCaptcur = [[[[0.0 for p in range(rPathNum)] for t in range(rSlotNum)] for d in range(len(new_sink))] for s in range(len(new_src))]
                    linkCostcur = [[[[0.0 for l in range(self.LINKNUM)] for t in range(rSlotNum)] for d in range(len(new_sink))] for s in range(len(new_src))]

                    h = 1  # debug辅助变量

                    # 此for循环的作用是得到矩阵T和在t时刻，从源结点src到目的结点dst的第k条路径上需要占用的资源
                    for s in range(len(new_src)):
                        src = new_src[s]
                        for d in range(len(new_sink)):
                            sink = new_sink[d]
                            tempSize_2 = 0.0
                            # 开始构造拓扑
                            file_node = open("reqNodes.txt", "w")
                            file_node_path = open("reqNodes_path.txt", "w")
                            # pathidSize = []
                            nodelist = [src, sink]
                            file_node.writelines("%d\n" "%d\n" % (src, sink))
                            for p in range(rPathNum):
                                file_node_path.writelines("%d" % src)
                                file_node_path.writelines("\t")
                                for nodeindex in range(len(self.PathList_node[src][sink][p])):
                                    nodeid = self.PathList_node[src][sink][p][nodeindex]
                                    file_node_path.writelines("%d" % nodeid)
                                    file_node_path.writelines("\t")
                                    if nodeid not in nodelist:
                                        nodelist.append(nodeid)
                                        file_node.writelines("%d" % nodeid)
                                        file_node.writelines("\n")

                                file_node_path.writelines("%d" % sink)
                                file_node_path.writelines("\n")
                            file_node.close()
                            file_node_path.close()

                            for t in range(rSlotNum - timeAsrc[s]):
                                # tempSize_3 = 0.0
                                file_node_path = open("reqNodes_path.txt", "r")
                                file_link = open("reqLinks.txt", "w")
                                linklist = []
                                for p in range(rPathNum):
                                    line = file_node_path.readline()
                                    line = str(line).split("\t")
                                    for linkindex in range(len(self.PathList[src][sink][p])):
                                        linkid = self.PathList[src][sink][p][linkindex]
                                        if linkid not in linklist:
                                            linklist.append(linkid)
                                            linkWeight = LinkResCaperSlot[linkid][t + r_start + timeAsrc[s]]
                                            file_link.writelines("%d\t" "%d\t" "%d\t" "%d\t" % (int(line[linkindex]), int(line[linkindex + 1]), int(linkWeight), linkid))
                                            file_link.writelines("\n")
                                file_link.close()
                                file_node_path.close()

                                self.loadPathLinks()
                                self.loadPathNodes()
                                self.geneTopo()

                                # nx.draw(self.topo)
                                # plt.show()
                                # print("aaa")

                                flow_value, flow_dict = nx.maximum_flow(self.topo, src, sink)
                                # 这一步是将嵌套的字典变成了二维矩阵
                                flow_matrix = pandas.DataFrame(flow_dict).T.fillna(0)
                                # print(flow_matrix)

                                # time.sleep(1)

                                file_link = open("reqLinks.txt", "r")
                                line = file_link.readline()
                                while line:
                                    edge = str(line).split("\t")
                                    source = int(edge[0])
                                    target = int(edge[1])
                                    linknumber = int(edge[3])
                                    linkCostcur[s][d][t + timeAsrc[s]][linknumber] = flow_matrix[source][target]
                                    line = file_link.readline()
                                file_link.close()

                                # tempSize = int(min(linkCostSetontcur))

                                # pathCaptcur[s][d][t + timeAsrc[s]][p] = tempSize
                                # tempSize_3 += flow_value

                                tempSize_2 += flow_value * 300

                                h = 2
                                # print(tempSize_2)
                                if tempSize_2 >= rSize and t <= rSlotNum - timeAsrc[s] - 1:
                                    numoftimeSlotfromSRCtoDST[s][d] = timeAsrc[s] + t + 1
                                    break

                                elif tempSize_2 < rSize and t == rSlotNum - timeAsrc[s] - 1:
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
                        for t in range(minTimeCost - timeAsrc[m_min]):
                            print(minTimeCost)
                            # 如果只在一个时隙内就完成传输
                            #if (minTimeCost - timeAsrc[m_min]) == 1:
                                # totalSize = 0
                                # 此处无论如何都要循环所有的links
                            for linkindex in range(len(linkCostcur[m_min][n_min][t + timeAsrc[m_min]])):
                                LinkResCaperSlot[linkindex][t + r_start + timeAsrc[m_min]] -= linkCostcur[m_min][n_min][t + timeAsrc[m_min]][linkindex]
                                # if linkCostcur[m_min][n_min][t + timeAsrc[m_min]][linkindex] != 0:
                                #     print(t + r_start + timeAsrc[m_min], linkindex)

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
                        # print(self.reqNUM, rSlotNum)
                        self.rejectReqs += 1
                        judgeVariate = False
                        break
                    else:
                        # print(minTimeCost)
                        timeAsrc.append(minTimeCost)
                        judgeVariate = True

                if judgeVariate:
                    self.acceptReqs += 1
                    print("The %d request is accepted! " % self.reqNUM)
                end_time = time.clock()
                # fl = open("acceptedratio_h.txt", "a")
                # fl.writelines("%d %d %d %.2f%% %f" % (self.reqNUM, self.acceptReqs, self.rejectReqs, ((self.acceptReqs / self.reqNUM) * 100), (end_time - start_time)))
                # # print(self.acceptReqs / self.reqNUM)
                # fl.writelines("\n")
                # fl.close()
            # print(tcur)
            tcur += 1

        freq.close()

        fl = open("acceptedratio_h.txt", "w")
        fl.writelines("%d %d %d %.2f%%" % (self.reqNUM, self.acceptReqs, self.rejectReqs, ((self.acceptReqs / self.reqNUM) * 100)))
        # print(self.acceptReqs / self.reqNUM)
        fl.writelines("\n")
        fl.close()


if __name__ == "__main__":
    # print "start..."
    mschedule = CSchedule()
    mschedule.loadPath()
    mschedule.SRCSemiFlexiable()
    # test()
    print("end!!!")
