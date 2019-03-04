#!/usr/bin/env python 
# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import division
import copy
import time
import pandas
from mosek_model.mosek_api import *
from Graph.kShortestPath import *
from genRequest import *
import xlrd
import xlwt
import os
import csv


class CRequest:
    def __init__(self, reqid, src, sinklist, tstart, tend, size):
        self.reqid = reqid
        self.src = src
        self.sinklist = sinklist
        self.tstart = tstart
        self.tend = tend
        self.size = size
        self.sentsize = 0
        self.remainsize = size


class CSchedule:

    def __init__(self, reqnum, slotnum):
        self.SLOTNUM = int(slotnum)  # 150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = int(reqnum)
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.rejectReqs2 = 0
        self.acceptReqs2 = 0
        self.rejectReqs3 = 0
        self.acceptReqs3 = 0
        self.rejectReqs4 = 0
        self.acceptReqs4 = 0
        self.rejectReqs5 = 0
        self.acceptReqs5 = 0
        self.linkCapacity = 24000  # 16000000

        self.LINK_DICT = {}  # (src-,sink)-link
        self.LINK_LIST = []  # linkid-link
        self.NODE_DICT = {}
        self.MAXTIMESLOTNUM = 300

    def loadPath(self):
        f = open("./Graph/linkonpath.txt", "r")
        fn = open("./Graph/nodeonpath.txt", "r")
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
        self.PathList_node = [[[[] for num in range(self.PATHNUM)] for col in range(self.NODENUM)] for row in
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

        line2 = fn.readline()
        pathid_node = 0
        while line2:
            line2 = line2.split()
            srcID = int(line2[0]) - 1
            sinkID = int(line2[len(line2) - 1]) - 1

            for i in range(len(line2) - 2):
                self.PathList_node[srcID][sinkID][pathid_node % self.PATHNUM].append(int(line2[i + 1]) - 1)
            line2 = fn.readline()
            pathid_node += 1

        f.close()
        fn.close()

    # 为了生成每个人request涉及到的节点和边组成的子网络拓扑
    def loadPathNodes(self):
        self.NODE_DICT = {}
        f = open("./Graph/reqNodes.txt", "r")
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
        self.LINK_DICT = {}  # (src-,sink)-link
        self.LINK_LIST = []  # linkid-link

        f = open("./Graph/reqLinks.txt", "r")
        line = f.readline()
        # edge = edge.split()
        # print(edge[2])
        # print(line)
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
        self.topo = nx.DiGraph()
        for node in self.NODE_DICT:
            self.topo.add_node(node)

        for src in self.LINK_DICT:
            for sink in self.LINK_DICT[src]:
                self.topo.add_edges_from([(src, sink)])
                self.topo.add_edge(src, sink, capacity=self.LINK_DICT[src][sink].weight)

    '''
    在MIPOnline函数中将algo_flexible和algo_fixed写在一起了，因为参数重复较多，且两种算法相似度较高。
    algo_fixed和algo_flexible的区别在于在预测某一个request的时候源数据中心是只有一个还是所有已经完成数据传输的数据中心均可为传输源 
    '''

    def MIPOnline(self):
        self.loadPath()

        # time.clock()产生当前request的开始时间
        # start_time = time.clock()
        # self.totalSize = 0
        print("\nstart MIPOnline...")
        freq = open("request_h.txt", "r")
        # 进行此操作的目的是为了将即将写入数据的txt文件中的内容清空
        fl = open("./result/acceptedratio_flexible.txt", "w")
        fl.close()
        fl2 = open("./result/acceptedratio_fixed.txt", "w")
        fl2.close()
        # freq.close()

        # self.request: 表示在第i个时隙到达的request
        # self.reqperSlot = [0 for slot in range(self.SLOTNUM)]
        # LinkResCaperSlot: 表示在第i条边上在j时隙上remain volumn
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)
        LinkResCaperSlot2 = copy.deepcopy(self.LinkCaperSlot)
        linkLoadSlot = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        linkLoadSlot2 = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        total_fsize = 0.0
        total_fsize2 = 0.0

        # tcur: 当前的slot time
        tcur = 0
        #while tcur < self.SLOTNUM:
        while tcur < 20:
            # print "SLOTNUM, slot time:", self.SLOTNUM, tcur
            line = freq.readline()
            line = line.split()
            reqperSlotcur = int(line[0])
            # self.reqNUM += self.reqperSlot[tcur]
            m_reqcount = 0
            # process the requests arrive in each slot
            while m_reqcount < reqperSlotcur:
                # print "reqperSlot, m_reqcount", self.reqperSlot[tcur], m_reqcount
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
                # self.totalSize += rSize
                m_reqcount += 1
                # self.reqNUM += 1

                onesrcLinkonpath = [[[0.0 for e in range(self.LINKNUM)] for p in range(rPathNum)] for d in
                                    range(sinkNum)]
                onesrcPathLen = [[0.0 for p in range(rPathNum)] for d in range(sinkNum)]
                src = maybesrc[0]
                for d in range(sinkNum):
                    sink = rsink[d]
                    for p in range(rPathNum):
                        onesrcPathLen[d][p] = len(self.PathList[src][sink][p])
                        for linkindex in range(len(self.PathList[src][sink][p])):
                            linkid = self.PathList[src][sink][p][linkindex]
                            onesrcLinkonpath[d][p][linkid] = 1.0
                            

                Linkonpath = [[[[0.0 for e in range(self.LINKNUM)] for p in range(rPathNum)] for d in range(sinkNum)]
                              for s in range(sinkNum + 1)]
                PathLen = [[[0.0 for p in range(rPathNum)] for d in range(sinkNum)] for s in range(sinkNum + 1)]
                for s in range(sinkNum + 1):
                    src = maybesrc[s]
                    for d in range(sinkNum):
                        sink = rsink[d]
                        if src == sink:
                            continue
                        for p in range(rPathNum):
                            PathLen[s][d][p] = len(self.PathList[src][sink][p])
                            for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                Linkonpath[s][d][p][linkid] = 1.0

                #h = 1
                reslinktimecap = [[0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM)]
                reslinktimecap2 = [[0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM)]
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        reslinktimecap[e][t] = LinkResCaperSlot[e][t + r_start]
                        reslinktimecap2[e][t] = LinkResCaperSlot2[e][t + r_start]

                # ################acceptance-Maximize#################################### #
                start_time = time.clock()
                competedest, solu_x, solu_w, solu_y, solu_feasible = flexiblesrcMIPmodel(rPathNum, self.LINKNUM,
                                                                                         sinkNum, rSlotNum, (rSize * 8),
                                                                                         Linkonpath, reslinktimecap,
                                                                                         PathLen)
                # print(competedest, solu_x, solu_w, solu_y, solu_feasible)
                end_time = time.clock()

                start_time_2 = time.clock()
                competedest2, solu_xx, solu_ww, solu_yy, solu2_feasible = fixsrcMIPmodel(rPathNum, self.LINKNUM,
                                                                                         sinkNum, rSlotNum, rSize * 8,
                                                                                         onesrcLinkonpath,
                                                                                         reslinktimecap2, onesrcPathLen)
                end_time_2 = time.clock()
                # update,outperformed includes fraction completion

                if solu_feasible == False or abs(competedest - sinkNum) > 0.1:
                    self.rejectReqs += 1
                if (solu_feasible == True) and (abs(competedest - sinkNum) < 0.1):
                    self.acceptReqs += 1
                    total_fsize += rSize * 8
                    for s in range(sinkNum + 1):
                        src = maybesrc[s]
                        for d in range(sinkNum):
                            sink = rsink[d]
                            for p in range(rPathNum):
                                for linkindex in range(len(self.PathList[src][sink][p])):
                                    linkid = self.PathList[src][sink][p][linkindex]
                                    for t in range(rSlotNum):
                                        LinkResCaperSlot[linkid][t + r_start] -= solu_y[
                                            (s * sinkNum + d) * rPathNum * rSlotNum + p * rSlotNum + t]
                                        linkLoadSlot[linkid][t + r_start] += solu_y[
                                            (s * sinkNum + d) * rPathNum * rSlotNum + p * rSlotNum + t]

                if solu2_feasible == False or abs(competedest2 - sinkNum) > 0.1:
                    self.rejectReqs2 += 1
                if (solu2_feasible == True) and (abs(competedest2 - sinkNum) < 0.1):
                    self.acceptReqs2 += 1
                    total_fsize2 += rSize * 8
                    src = maybesrc[0]
                    for d in range(sinkNum):
                        sink = rsink[d]
                        for p in range(rPathNum):
                            for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                for t in range(rSlotNum):
                                    LinkResCaperSlot2[linkid][t + r_start] -= solu_yy[
                                        d * rPathNum * rSlotNum + p * rSlotNum + t]
                                    linkLoadSlot2[linkid][t + r_start] += solu_yy[
                                        d * rPathNum * rSlotNum + p * rSlotNum + t]

                fl = open("./result/acceptedratio_flexible.txt", "a")
                fl.writelines("%d %d %.2f%% %f" % (
                    self.acceptReqs, self.rejectReqs, ((self.acceptReqs / (self.acceptReqs + self.rejectReqs)) * 100),
                    (end_time - start_time)))
                # print(self.acceptReqs / self.reqNUM)
                fl.writelines("\n")
                fl.close()

                fl2 = open("./result/acceptedratio_fixed.txt", "a")
                fl2.writelines("%d %d %.2f%% %f" % (
                    self.acceptReqs2, self.rejectReqs2,
                    ((self.acceptReqs2 / (self.acceptReqs2 + self.rejectReqs2)) * 100),
                    (end_time_2 - start_time_2)))
                # print(self.acceptReqs / self.reqNUM)
                fl2.writelines("\n")
                fl2.close()

            tcur += 1

        p2mp_netUtilization = 0.0
        # a = 0
        p2mp_throughput = 0.0
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                p2mp_netUtilization += 1.0 * linkLoadSlot[linkid][slotid] / self.LinkCaperSlot[linkid][slotid]
                # a += linkLoadSlot[linkid][slotid]
        # print(a)
        p2mp_netUtilization *= 100
        p2mp_netUtilization /= self.LINKNUM
        p2mp_netUtilization /= self.SLOTNUM
        p2mp_throughput = total_fsize / self.SLOTNUM

        mp2p_netUtilization = 0.0
        mp2p_throughput = 0.0
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                mp2p_netUtilization += 1.0 * linkLoadSlot2[linkid][slotid] / self.LinkCaperSlot[linkid][slotid]
        mp2p_netUtilization *= 100
        mp2p_netUtilization /= self.LINKNUM
        mp2p_netUtilization /= self.SLOTNUM
        mp2p_throughput = total_fsize2 / self.SLOTNUM
        # elapsed_time = (time.clock() - start_time)

        freq.close()

        return p2mp_netUtilization, mp2p_netUtilization, p2mp_throughput, mp2p_throughput

    '''
    启发式模型
    '''

    def SRCSemiFlexiable(self):
        print("\nstart heuristic algorithm...")

        freq = open("request_h.txt", "r")
        fl = open("./result/acceptedratio_h.txt", "w")
        fl.close()

        self.totalSize = 0

        linkLoadSlot3 = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        linkLoadSlot3_temp = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        # LinkCaperSlot3的每个元素的单位是bps
        LinkResCaperSlot3 = copy.deepcopy(self.LinkCaperSlot)
        # LinkResCaperSlot3的中间变量，由于代码的逻辑，只有当前request被接受时才能将此变量的值赋值于LinkResCaperSlot3
        LinkResCaperSlot3_temp = copy.deepcopy(self.LinkCaperSlot)
        total_fsize3 = 0.0
        judgeVariate = True  # type: bool

        tcur = 0
        while tcur < self.SLOTNUM:
            line = freq.readline()
            line = line.split()
            reqperSlotcur = int(line[0])
            m_reqcount = 0  # type: int

            while m_reqcount < reqperSlotcur:
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

                while len(rsink) < sinkNum:
                    rsink.append(int(line[5 + len(rsink)]) - 1)

                rPathNum = self.PATHNUM
                rSlotNum = r_end - r_start + 1

                m_reqcount += 1

                new_sink = rsink
                minTimeCost = 0
                timeAsrc = [0]

                LinkResCaperSlot3_temp = copy.deepcopy(LinkResCaperSlot3)
                linkLoadSlot3_temp = copy.deepcopy(linkLoadSlot3)

                start_time = time.clock()

                while len(new_sink) > 0:
                    numoftimeSlotfromSRCtoDST = [[0 for d in range(len(new_sink))] for s in range(len(new_src))]
                    linkCostcur = [
                        [[[0 for l in range(self.LINKNUM)] for t in range(rSlotNum)] for d in range(len(new_sink))] for
                        s in range(len(new_src))]

                    # 此for循环的作用是得到矩阵T和在t时刻，从源结点src到目的结点dst的第k条路径上需要占用的资源
                    for s in range(len(new_src)):
                        src = new_src[s]
                        for d in range(len(new_sink)):
                            sink = new_sink[d]
                            tempSize_2 = 0.0
                            # 开始构造拓扑
                            file_node = open("./Graph/reqNodes.txt", "w")
                            file_node_path = open("./Graph/reqNodes_path.txt", "w")
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

                            '''
                            某一个数据中心在最后一个时隙的下一个时隙作为源数据中心，那么这个数据中心就没有作为源数据中心的机会
                            '''
                            if timeAsrc[s] == rSlotNum:
                                numoftimeSlotfromSRCtoDST[s][d] = self.MAXTIMESLOTNUM

                            else:
                                '''
                                其他情况
                                '''
                                for t in range(rSlotNum - timeAsrc[s]):
                                    file_node_path = open("./Graph/reqNodes_path.txt", "r")
                                    file_link = open("./Graph/reqLinks.txt", "w")
                                    linklist = []
                                    for p in range(rPathNum):
                                        line = file_node_path.readline()
                                        line = str(line).split("\t")
                                        for linkindex in range(len(self.PathList[src][sink][p])):
                                            linkid = self.PathList[src][sink][p][linkindex]
                                            if linkid not in linklist:
                                                linklist.append(linkid)
                                                linkWeight = LinkResCaperSlot3_temp[linkid][t + r_start + timeAsrc[s]]
                                                file_link.writelines("%d\t" "%d\t" "%d\t" "%d\t" % (
                                                    int(line[linkindex]), int(line[linkindex + 1]), int(linkWeight),
                                                    linkid))
                                                file_link.writelines("\n")
                                    file_link.close()
                                    file_node_path.close()

                                    self.loadPathLinks()
                                    self.loadPathNodes()
                                    self.geneTopo()

                                    flow_value, flow_dict = nx.maximum_flow(self.topo, src, sink)
                                    # 这一步是将嵌套的字典变成了二维矩阵
                                    flow_matrix = pandas.DataFrame(flow_dict).T.fillna(0)

                                    linkValue = {}
                                    linklist = []
                                    file_link = open("./Graph/reqLinks.txt", "r")
                                    line = file_link.readline()
                                    while line:
                                        edge = str(line).split("\t")
                                        source = int(edge[0])
                                        target = int(edge[1])
                                        linknumber = int(edge[3])
                                        linkCostcur[s][d][t + timeAsrc[s]][linknumber] = flow_matrix[target][source]
                                        if flow_matrix[target][source] > 0:
                                            linkValue[linknumber] = flow_matrix[target][source]
                                            linklist.append(linknumber)
                                        line = file_link.readline()
                                    file_link.close()

                                    tempSize_2 += flow_value
                                    # print(flow_value)

                                    # print(tempSize_2)
                                    if tempSize_2 >= rSize:
                                        numoftimeSlotfromSRCtoDST[s][d] = timeAsrc[s] + t + 1
                                        ratio = (rSize - tempSize_2 + flow_value) / flow_value
                                        # print(ratio)
                                        for l in range(len(linklist)):
                                            linkCostcur[s][d][t + timeAsrc[s]][int(linklist[l])] = linkValue[
                                                                                                       linklist[
                                                                                                           l]] * ratio
                                        break

                                    elif tempSize_2 < rSize and t == rSlotNum - timeAsrc[s] - 1:
                                        numoftimeSlotfromSRCtoDST[s][d] = self.MAXTIMESLOTNUM
                                        # print("aaa")

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

                    # 如果最小的时间消耗都是无穷大的，那此request要被拒绝

                    if minTimeCost <= rSlotNum:
                        # update c_e_t
                        for t in range(minTimeCost - timeAsrc[m_min]):
                            # 此处无论如何都要循环所有的links
                            for linkindex in range(self.LINKNUM):
                                LinkResCaperSlot3_temp[linkindex][t + r_start + timeAsrc[m_min]] -= \
                                    linkCostcur[m_min][n_min][t + timeAsrc[m_min]][linkindex]
                                linkLoadSlot3_temp[linkindex][t + r_start + timeAsrc[m_min]] += \
                                    linkCostcur[m_min][n_min][t + timeAsrc[m_min]][linkindex]

                                if LinkResCaperSlot3_temp[linkindex][t + r_start + timeAsrc[m_min]] < 0:
                                    print("Error: link does not have enough capacity！！")
                                    return
                                if linkCostcur[m_min][n_min][t + timeAsrc[m_min]][linkindex] < 0:
                                    return
                    else:
                        self.rejectReqs3 += 1
                        judgeVariate = False
                        break

                    # 如果new_sink里面有相同的元素，就删除排在前面的那一个
                    new_sink.remove(sinkReadyMovetosrcList)

                    new_src.append(sinkReadyMovetosrcList)

                    if (minTimeCost > rSlotNum) and (len(new_sink) > 0):
                        self.rejectReqs3 += 1
                        judgeVariate = False
                        break
                    else:
                        timeAsrc.append(minTimeCost)
                        judgeVariate = True

                if judgeVariate:
                    self.acceptReqs3 += 1
                    total_fsize3 += rSize
                    LinkResCaperSlot3 = copy.deepcopy(LinkResCaperSlot3_temp)
                    linkLoadSlot3 = copy.deepcopy(linkLoadSlot3_temp)

                end_time = time.clock()

                fl = open("./result/acceptedratio_h.txt", "a")
                fl.writelines("%d %d %.2f%% %f" % (
                    self.acceptReqs3, self.rejectReqs3,
                    ((self.acceptReqs3 / (self.acceptReqs3 + self.rejectReqs3)) * 100),
                    (end_time - start_time)))
                fl.writelines("\n")
                fl.close()
            tcur += 1

        heuristic_netUtilization = 0.0
        # a = 0
        heuristic_throughput = 0.0
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                heuristic_netUtilization += 1.0 * linkLoadSlot3[linkid][slotid] / self.LinkCaperSlot[linkid][slotid]
                # a += linkLoadSlot3[linkid][slotid]
        # print(a)
        heuristic_netUtilization *= 100
        heuristic_netUtilization /= self.LINKNUM
        heuristic_netUtilization /= self.SLOTNUM
        heuristic_throughput = total_fsize3 / self.SLOTNUM

        freq.close()
        return heuristic_netUtilization, heuristic_throughput

    '''
    离线模型
    '''

    def MIPOffline(self):

        self.loadPath()

        # start_time = time.clock()
        # self.totalSize = 0
        print("\nstart MIPOffline...")
        freq = open("request_h.txt", "r")
        fl = open("./result/acceptedratio_offline.txt", "w")
        fl.close()

        LinkResCaperSlot4 = copy.deepcopy(self.LinkCaperSlot)
        linkLoadSlot4 = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]

        # 生成常数survival_i_t，二维矩阵，取值0或1
        survivalTimeperReq = [[0 for slot in range(self.SLOTNUM)] for r in range(self.reqNUM)]
        # 生成常数fsize_i, 每个request的fsize
        fsize = [0 for r in range(self.reqNUM)]
        # 生成常数M_i，每个request的目的数据中心的数目
        dstNumperReq = [0 for r in range(self.reqNUM)]
        # 生成常数src_i_u和dst_i_u，二维矩阵，取值0或1
        srcperReq = [[0 for node in range(self.NODENUM)] for r in range(self.reqNUM)]
        dstperReq = [[0 for node in range(self.NODENUM)] for r in range(self.reqNUM)]

        tcur = 0
        reqcount = 0
        Linkonpath = [[[[0.0 for e in range(self.LINKNUM)] for p in range(self.PATHNUM)] for v in range(self.NODENUM)]
                      for u in range(self.NODENUM)]
        PathLen = [[[0.0 for p in range(self.PATHNUM)] for v in range(self.NODENUM)] for s in range(self.NODENUM)]
        # print(Linkonpath)
        while tcur < self.SLOTNUM:
            line = freq.readline()
            line = line.split()
            reqperSlotcur = int(line[0])
            m_reqcount = 0
            while m_reqcount < reqperSlotcur:
                line = freq.readline()
                line = line.split()
                rsrc = int(line[0]) - 1
                # print(line, reqperSlotcur)
                r_start = int(line[1])
                r_end = int(line[2])
                rSize = int(line[3]) * 8
                sinkNum = int(line[4])
                rsink = []
                maybesrc = [rsrc]

                m_reqcount += 1

                fsize[reqcount] = rSize
                dstNumperReq[reqcount] = sinkNum
                for t in range(self.SLOTNUM):
                    if (t >= r_start and t <= r_end):
                        survivalTimeperReq[reqcount][t] = 1
                    else:
                        survivalTimeperReq[reqcount][t] = 0

                for d in range(sinkNum):
                    rsink.append(int(line[d + 5]) - 1)
                    maybesrc.append(int(line[d + 5]) - 1)
                for node in range(self.NODENUM):
                    if node == rsrc:
                        srcperReq[reqcount][node] = 1
                    elif node in rsink:
                        dstperReq[reqcount][node] = 1
                    else:
                        srcperReq[reqcount][node] = 0
                        dstperReq[reqcount][node] = 0

                # 生成常数I
                for u in range(self.NODENUM):
                    if u in maybesrc:
                        # 1print(maybesrc, rsink)
                        for v in range(self.NODENUM):
                            if v in rsink and u != v:
                                for p in range(self.PATHNUM):
                                    for linkindex in range(len(self.PathList[u][v][p])):
                                        linkid = self.PathList[u][v][p][linkindex]
                                        # print(linkid, u, v, p)
                                        # print(self.PathList)
                                        # print(self.LINKNUM, self.NODENUM, self.PATHNUM)
                                        # print(linkid, u, v, p)
                                        Linkonpath[u][v][p][linkid] = 1.0
                                        PathLen[u][v][p] += 1
                reqcount += 1
            tcur += 1
        freq.close()

        # print(Linkonpath)

        # ######################acceptance-Maximize#################################### #
        # limit the data source of a receiver to be no more than 1

        start_time = time.clock()
        self.acceptReqs4, total_fsize4, solu_r, solu4_x, solu4_w, solu4_y, solu4_feasible = \
            offlineMIPmodel(self.reqNUM, self.NODENUM, self.SLOTNUM, self.PATHNUM,
                            self.LINKNUM,
                            srcperReq, dstperReq,
                            dstNumperReq,
                            fsize, survivalTimeperReq,
                            Linkonpath, LinkResCaperSlot4, PathLen)
        end_time = time.clock()
        # print(solu_x)

        if (solu4_feasible == True):
            for i in range(self.reqNUM):
                for u in range(self.NODENUM):
                    for v in range(self.NODENUM):
                        for p in range(self.PATHNUM):
                            for linkindex in range(len(self.PathList[u][v][p])):
                                linkid = self.PathList[u][v][p][linkindex]
                                for t in range(self.SLOTNUM):
                                    linkLoadSlot4[linkid][t] += solu4_y[
                                        (i * self.NODENUM * self.NODENUM + u * self.NODENUM + v) * self.PATHNUM * self.SLOTNUM + p * self.SLOTNUM + t]

        fl = open("./result/acceptedratio_offline.txt", "a")
        fl.writelines("%d %d %.2f%% %f" % (
            self.reqNUM, self.acceptReqs4, ((self.acceptReqs4 / self.reqNUM) * 100),
            (end_time - start_time)))
        # print(self.acceptReqs / self.reqNUM)
        fl.writelines("\n")
        fl.close()

        offline_netUtilization = 0.0
        # a = 0.0
        offline_throughput = 0.0
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                offline_netUtilization += 1.0 * linkLoadSlot4[linkid][slotid] / self.LinkCaperSlot[linkid][slotid]
                # a += linkLoadSlot4[linkid][slotid]
        # print(a)
        offline_netUtilization *= 100
        offline_netUtilization /= self.LINKNUM
        offline_netUtilization /= self.SLOTNUM
        offline_throughput = total_fsize4 / self.SLOTNUM

        return offline_netUtilization, offline_throughput

    '''
    加速模型
    '''
    def AccelerationAlg(self):
        # request.txt
        # request_format:(rsrc+1, rstart, rend, rSize, len(rsink),(rsink[dest]+1))
        # load request
        #print("run the accelerate algorithm...")
        fl = open("./result/acceptedratio_age.txt", "w")
        fl.close()
        print("\nstart Acceleration Algorithm...")
        request_List = []
        reqfile = open("request_h.txt", "r")
        reqline = reqfile.readline()
        reqid = 0
        destlist = []
        while reqline:
            # 每个时隙到达的request的数目
            reqline = reqline.split()
            reqperSlotcur = int(reqline[0])
            #print ("reqperSlotcur", reqperSlotcur)
            while reqperSlotcur > 0:
                reqline = reqfile.readline()
                reqline = reqline.split()
                src = int(reqline[0]) - 1
                tstart = int(reqline[1])
                tend = int(reqline[2])
                size = int(reqline[3])
                destnum = int(reqline[4])
                for i in range(destnum):
                    destlist.append(int(reqline[5 + i]) - 1)
                req_instance = CRequest(reqid, src, destlist, tstart, tend, size)
                destlist = []
                request_List.append(req_instance)
                reqperSlotcur -= 1
                reqid += 1
            reqline = reqfile.readline()
        reqfile.close()
        #print("requestnum ", len(request_List))

        # begin process
        rPathNum = self.PATHNUM
        linknum = self.LINKNUM
        linkLoadSlot = [[0 for t in range(self.SLOTNUM)] for l in range(self.LINKNUM)]
        linkLoadSlot2 = [[0 for t in range(self.SLOTNUM)] for l in range(self.LINKNUM)]
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)
        tcur = 0
        req_pos = 0
        # acceptance_alg2 = 0

        #while tcur < self.SLOTNUM:
        while tcur < 20:
            ##every time processes requests that start from tcur
            processing_reqlist = []
            #print("req_pos, len(request_List),request_List[req_pos].tstart, tcur", req_pos, len(request_List),request_List[req_pos].tstart, tcur)
            while req_pos < len(request_List) and request_List[req_pos].tstart == tcur:
                #print("tcur, req_pos, tstart", tcur, req_pos, request_List[req_pos].tstart)
                processing_reqlist.append(request_List[req_pos])
                req_pos += 1
            tcur += 1
            # processing the requests in the request lists
            #print("\n tcur, requestnum", tcur, len(processing_reqlist))
            if len(processing_reqlist) == 0:
                continue
            for req_instance in processing_reqlist:
                #print("\n")
                reqid = req_instance.reqid
                src = req_instance.src
                destlist = []
                destlist = req_instance.sinklist
                start_time = req_instance.tstart
                deadline = req_instance.tend
                fsize = req_instance.size
                sinkNum = len(destlist)

                Linkonpath = [[[[0.0 for e in range(self.LINKNUM)] for p in range(rPathNum)] for d in range(sinkNum)]
                              for s in range(sinkNum + 1)]
                PathLen = [[[0.0 for p in range(rPathNum)] for d in range(sinkNum)] for s in range(sinkNum + 1)]
                for d in range(sinkNum):
                    sink = destlist[d]
                    if src == sink:
                        continue
                    for p in range(rPathNum):
                        PathLen[0][d][p] = len(self.PathList[src][sink][p])
                        for linkindex in range(len(self.PathList[src][sink][p])):
                            linkid = self.PathList[src][sink][p][linkindex]
                            Linkonpath[0][d][p][linkid] = 1.0
                            
                for s in range(sinkNum):
                    src = destlist[s]
                    for d in range(sinkNum):
                        sink = destlist[d]
                        if src == sink:
                            continue
                        for p in range(rPathNum):
                            PathLen[s + 1][d][p] = len(self.PathList[src][sink][p])
                            for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                Linkonpath[s + 1][d][p][linkid] = 1.0

                rSlotNum = deadline - start_time + 1
                reslinktimecap = [[0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM)]
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        reslinktimecap[e][t] = LinkResCaperSlot[e][t + start_time]

                # print "solve problem: size, destnum, srcnum, slotnum ", fsize, sinkNum, sinkNum+1, rSlotNum
                # kMax = min(4, rSlotNum)
                # time_interval = (deadline-start_time+1)/kMax
                time_interval = min(2, rSlotNum)
                kMax = int(math.ceil(rSlotNum / time_interval))
                # print kMax
                time_series = [time_interval for i in range(kMax)]
                time_series[kMax - 1] = deadline - start_time + 1 - time_interval * (kMax - 1)
                assignedsrcfordest = [[0 for d in range(sinkNum)] for s in
                                      range(sinkNum + 1)]  # maintain the states of assigned srcs for every dest
                sourcelist = []  # maintian the id of sites that can be served as source
                sourcelist.append(0)  # push the original source into this list, id =0, numbered from 0 to sinknum+1
                remainratio = [1.0 for j in range(sinkNum)]  # at the start, remain ratio is initalized to 1.0
                # print "kmax, timelist", kMax, time_series
                kcur = 0
                # print "remainratio, sourcelist", remainratio, sourcelist
                while sum(remainratio) > 0.00001 and kcur < kMax:
                    # generate data for each solving
                    #print("kcur, remainratio", kcur, sum(remainratio))
                    slotnum = time_series[kcur]
                    # print "kcur, slotnum", kcur, slotnum
                    linktimecap = [[0.0 for t in range(slotnum)] for e in range(self.LINKNUM)]
                    for e in range(self.LINKNUM):
                        for t in range(slotnum):
                            linktimecap[e][t] = reslinktimecap[e][kcur * time_interval + t]
                            # run the linear programming to maximize the throughput
                    # print("remainratio", remainratio)
                    start_time_solu = time.clock()
                    solu_w, solu_y, solu_z, solu_feasible = maxThroughputmodel(rPathNum, linknum, sinkNum, (fsize*8),
                                                                               slotnum, Linkonpath, linktimecap,
                                                                               remainratio, assignedsrcfordest,
                                                                               sourcelist, PathLen)
                    end_time_solu = time.clock()
                    # update assignedsrcfordest, sourcelist, remainratio, reslintimecap
                    if solu_feasible == False:
                        kcur += 1
                        continue
                    for d in range(sinkNum):
                        remainratio[d] -= round(solu_w[d], 2)
                        remainratio[d] = round(remainratio[d], 2)
                        if remainratio[d] < 0.00001:
                            sourcelist.append(d + 1)
                    sourcelist = list(set(sourcelist))

                    for s in range(sinkNum + 1):
                        for d in range(sinkNum):
                            if solu_z[s * sinkNum + d] == 1 and solu_w[d] > 0:
                                #print("d, transferred_size", d, solu_w[d])
                                assignedsrcfordest[s][d] = 1
                    #print ("assignsrc for dest", assignedsrcfordest)
                    #print ("remainratio, sourcelist", remainratio, sourcelist)

                    for s in range(sinkNum + 1):
                        for d in range(sinkNum):
                            k = s * sinkNum + d
                            for p in range(rPathNum):
                                for t in range(slotnum):
                                    for e in range(self.LINKNUM):
                                        linktimecap[e][t] -= Linkonpath[s][d][p][e] * solu_y[
                                            k * rPathNum * slotnum + p * slotnum + t]

                    for e in range(self.LINKNUM):
                        for t in range(slotnum):
                            reslinktimecap[e][kcur * time_interval + t] = linktimecap[e][t]
                    #print("reslinktimecap", reslinktimecap)

                    kcur += 1
                # check if the deadline is satisfied
                if sum(remainratio) < 0.00001:
                    #print("remainratio", sum(remainratio))
                    #print("meet the deadline!")
                    # acceptance_alg2 += 1
                    self.acceptReqs5 += 1
                if sum(remainratio) > 0.00001:
                    self.rejectReqs5 += 1
                    #print("miss the deadline!")
                # print("remainratio", remainratio)
                # update LinkResCaperSlot according to reslinktimecap
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        LinkResCaperSlot[e][t + start_time] = reslinktimecap[e][t]

            fl = open("./result/acceptedratio_age.txt", "a")
            fl.writelines("%d %d %.2f%% %f" % (
                self.acceptReqs5, self.rejectReqs5, ((self.acceptReqs5 / (self.acceptReqs5 + self.rejectReqs5)) * 100),
                (end_time_solu - start_time_solu)))
            # print(self.acceptReqs / self.reqNUM)
            fl.writelines("\n")
            fl.close()
        # print("alg2-acceptance:", acceptance_alg2)
        
if __name__ == "__main__":
    print("start...")
    # 读取request的总数，时隙数目
    f = open("allReqNum.txt", "r")
    line = f.readline()
    line = line.split()
    reqNUM = int(line[0])
    line = f.readline()
    line = line.split()
    slotnum = int(line[0])
    f.close()

    f1 = open('netUtilization.csv', mode='a')
    writer1 = csv.writer(f1)
    f2 = open('throughput.csv', mode='a')
    writer2 = csv.writer(f2)
    f3 = open('acceptedratio.csv', mode='a')
    writer3 = csv.writer(f3)

    mschedule = CSchedule(reqnum=reqNUM, slotnum=slotnum)
    mschedule.loadPath()

    # 在线模型运行
    # flexiblesrc_netUtilization, fixederc_netUtilization, flexiblesrc_throughput, fixedsrc_throughput = mschedule.MIPOnline()
    # flexiblesrc_acceptedratio = mschedule.acceptReqs/reqNUM
    # fixederc_acceptedratio = mschedule.acceptReqs2/reqNUM
    flexiblesrc_netUtilization, fixederc_netUtilization, flexiblesrc_throughput, fixedsrc_throughput = 0
    flexiblesrc_acceptedratio = 0
    fixederc_acceptedratio = 0
    
    
    # 启发式模型
    heuristic_netUtilization, heuristic_throughput = mschedule.SRCSemiFlexiable()
    heuristic_acceptedratio = mschedule.acceptReqs3 / reqNUM

    # print(heuristic_netUtilization)
    # 离线模型
    offline_netUtilization = 0
    offline_throughput = 0
    offline_acceptedratio = 0
    #offline_netUtilization, offline_throughput = mschedule.MIPOffline()
    #offline_acceptedratio = mschedule.acceptReqs4/reqNUM


    # 网络利用率
    netUtilization = [flexiblesrc_netUtilization, fixederc_netUtilization, heuristic_netUtilization, offline_netUtilization]
    # 吞吐量单位 bit/slot
    throughput = [flexiblesrc_throughput, fixedsrc_throughput, heuristic_throughput, offline_throughput]
    # 接纳率
    acceptedratio = [flexiblesrc_acceptedratio, fixederc_acceptedratio, heuristic_acceptedratio, offline_acceptedratio]

    writer1.writerow(netUtilization)
    writer2.writerow(throughput)
    writer3.writerow(acceptedratio)
    

    mschedule.AccelerationAlg()
    alg2_acceptedratio = mschedule.acceptReqs5 / reqNUM

    f1.close()
    f2.close()
    f3.close()

    print("end!!!")
