#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from __future__ import print_function
from __future__ import division
from mosek.fusion import *
import random

import copy
import time
import pandas
from mosek_model.mosek_api import *
from Graph.kShortestPath import *
from genRequest import *


class CSchedule:

    def __init__(self):
        # self.SLOTNUM = int(slotnum)  # 150mins #1slot= 5mins  24h = 288slots
        # self.reqNUM = int(reqnum)
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.rejectReqs2 = 0
        self.acceptReqs2 = 0
        self.rejectReqs3 = 0
        self.acceptReqs3 = 0
        self.rejectReqs4 = 0
        self.acceptReqs4 = 0
        self.linkCapacity = 24000  # 16000000

        self.LINK_DICT = {}  # (src-,sink)-link
        self.LINK_LIST = []  # linkid-link
        self.NODE_DICT = {}
        self.MAXTIMESLOTNUM = 300

    def loadPathNodes(self):
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

        return self.topo

if __name__ == '__main__':
    m = CSchedule()
    m.loadPathLinks()
    m.loadPathNodes()
    topo = m.geneTopo()

    # nx.draw(self.topo)
    # plt.show()
    # print("aaa")
    # src=6
    # sink=1

    flow_value, flow_dict = nx.maximum_flow(topo, 2, 1)
    # print("ch", src, sink, rSize, flow_value)
    # print("en", flow_dict)
    # 这一步是将嵌套的字典变成了二维矩阵
    flow_matrix = pandas.DataFrame(flow_dict).T.fillna(0)
    # freq = open("request.txt", "r")
    # line = freq.readline()
    # line = line.split()
    # list = [int(line[1]), int(line[2])]
    # print(list)

    # a = [[[[0 for n in range(7)] for k in range(2)] for j in range(2)] for i in range(2)]
    # b = [[0 for n in range(7)] for i in range(8)]
    # c = [[[[0 for n in range(7)] for k in range(2)] for j in range(2)] for i in range(2)]
    #
    # for i in range(2):
    #     for j in range(2):
    #         for k in range(2):
    #             for n in range(7):
    #                 a[i][j][k][n] = random.randint(1, 5)
    #
    # for i in range(2):
    #     for j in range(2):
    #         for k in range(2):
    #             for n in range(7):
    #                 b[i*2*2+j*2+k][n] = a[i][j][k][n]
    #
    # for i in range(2):
    #     for j in range(2):
    #         for k in range(2):
    #             for n in range(7):
    #                 c[i][j][k][n] = random.randint(1, 5)
    #
    # sum_1 = 0
    # sum_2 = 0
    # for i in range(2):
    #     for j in range(2):
    #         for k in range(2):
    #             for n in range(7):
    #                 sum_1 = sum_1 + a[i][j][k][n] * c[i][j][k][n]
    #                 sum_2 = sum_2 + b[i*2*2+j*2+k][n] * c[i][j][k][n]
    #
    # print(sum_1)
    # print(sum_2)
    #
    # print(a[0][0][1][5])
    # print(b[1][5])

    # a = [3,2,1]
    # b = [1,2,3]
    #
    # if (sorted(a) == sorted(b)):
    #     print(1)
    # else:
    #     print(0)

#     def MIPOffline(self):
#
#         self.loadPath()
#
#         # start_time = time.clock()
#         # self.totalSize = 0
#         print("\nstart MIPOffline...")
#         freq = open("request.txt", "r")
#         fl = open("./result/acceptedratio_offline.txt", "w")
#         fl.close()
#
#         LinkResCaperSlot4 = copy.deepcopy(self.LinkCaperSlot)
#
#         # 生成常数survival_i_t，二维矩阵，取值0或1
#         self.survivalTimeperReq = [[0 for slot in range(self.SLOTNUM)] for r in range(self.reqNUM)]
#         # 生成常数fsize_i, 每个request的fsize
#         self.fsize = [0 for r in range(self.reqNUM)]
#         # 生成常数M_i，每个request的目的数据中心的数目
#         self.dstNumperReq = [0 for r in range(self.reqNUM)]
#         # 生成常数src_i_u和dst_i_u，二维矩阵，取值0或1
#         self.srcperReq = [[0 for node in range(self.NODENUM)] for r in range(self.reqNUM)]
#         self.dstperReq = [[0 for node in range(self.NODENUM)] for r in range(self.reqNUM)]
#
#         tcur = 0
#         reqcount = 0
#         Linkonpath = [[[[0.0 for p in range(self.PATHNUM)] for v in range(self.NODENUM)] for u in range(self.NODENUM)]
#                       for e in range(self.LINKNUM)]
#         # print(Linkonpath)
#         # while tcur < self.SLOTNUM:
#         line = freq.readline()
#         line = line.split()
#         # reqperSlotcur = int(line[0])
#         # m_reqcount = 0
#         while m_reqcount < reqperSlotcur:
#             line = freq.readline()
#             line = line.split()
#             rsrc = int(line[0]) - 1
#             # print(line, reqperSlotcur)
#             r_start = int(line[1])
#             r_end = int(line[2])
#             rSize = int(line[3]) * 8
#             sinkNum = int(line[4])
#             rsink = []
#             maybesrc = [rsrc]
#
#             m_reqcount += 1
#
#             self.fsize[reqcount] = rSize
#             self.dstNumperReq[reqcount] = sinkNum
#             for t in range(self.SLOTNUM):
#                 if (t >= r_start and t <= r_end):
#                     self.survivalTimeperReq[reqcount][t] = 1
#                 else:
#                     self.survivalTimeperReq[reqcount][t] = 0
#
#             for d in range(sinkNum):
#                 rsink.append(int(line[d + 5]) - 1)
#                 maybesrc.append(int(line[d + 5]) - 1)
#             for node in range(self.NODENUM):
#                 if node == rsrc:
#                     self.srcperReq[reqcount][node] = 1
#                 elif node in rsink:
#                     self.dstperReq[reqcount][node] = 1
#                 else:
#                     self.srcperReq[reqcount][node] = 0
#                     self.dstperReq[reqcount][node] = 0
#
#             # 生成常数I
#             for u in range(self.NODENUM):
#                 if u in maybesrc:
#                     print(maybesrc, rsink)
#                     for v in range(self.NODENUM):
#                         if v in rsink and u != v:
#                             for p in range(self.PATHNUM):
#                                 for linkindex in range(len(self.PathList[u][v][p])):
#                                     linkid = self.PathList[u][v][p][linkindex]
#                                     # print(linkid, u, v, p)
#                                     # print(self.PathList)
#                                     # print(self.LINKNUM, self.NODENUM, self.PATHNUM)
#                                     # print(linkid, u, v, p)
#                                     Linkonpath[linkid][u][v][p] = 1.0
#             reqcount += 1
#         #     tcur += 1
#         # freq.close()
#
#         # print(Linkonpath)
#
#         #######################acceptance-Maximize#################################### #
#         # limit the data source of a receiver to be no more than 1
#
#         start_time = time.clock()
#         self.acceptReqs3, solu_y, solu_status = offlineMIPmodel(self.reqNUM, self.NODENUM, self.SLOTNUM, self.PATHNUM,
#                                                                 self.LINKNUM,
#                                                                 self.srcperReq, self.dstperReq,
#                                                                 self.dstNumperReq,
#                                                                 self.fsize, self.survivalTimeperReq,
#                                                                 Linkonpath, LinkResCaperSlot4)
#         end_time = time.clock()
#         fl = open("./result/acceptedratio_offline.txt", "a")
#         fl.writelines("%d %d %.2f%% %f" % (
#             self.reqNUM, self.acceptReqs4, ((self.acceptReqs4 / self.reqNUM) * 100),
#             (end_time - start_time)))
#         # print(self.acceptReqs / self.reqNUM)
#         fl.writelines("\n")
#         fl.close()
#
#         def testMosek():
#             with Model("test") as M:
#                 x = M.variable('X', [2, 2], Domain.greaterThan(0.0))
#                 # y = M.variable('Y', [srcnum,ss destnum, pathnum, slotnum], Domain.greaterThan(0.0))
#
#                 for i in range(2):
#                     x1 = 0
#                     for j in range(2):
#                         x1 = Expr.add(x1, x.index(i, j))
#                     M.constraint(x1, Domain.equalsTo(2))
#
#                 for j in range(2):
#                     x2 = 0
#                     for i in range(2):
#                         x2 = Expr.add(x2, x.index(i, j))
#                     M.constraint(x2, Domain.equalsTo(3))
#
#                 M.objective("completed_dest", ObjectiveSense.Maximize, Expr.sum(x))
#
#                 M.solve()
#                 res_obj = 0
#                 res_x = 0
#                 res_feasible = False
#                 acceptable = [
#                     ProblemStatus.PrimalAndDualFeasible,
#                     ProblemStatus.PrimalFeasible,
#                     ProblemStatus.DualFeasible]
#
#                 if M.getProblemStatus(SolutionType.Default) in acceptable:
#                     # print "feasible"
#                     res_feasible = True
#
#                 if res_feasible == False:
#                     # print "nonfeasible: flexible source!"
#                     # print M.getPrimalSolutionStatus()
#                     # print M.getProblemStatus(SolutionType.Default)
#                     return res_obj, res_x, res_feasible
#
#                 res_x = x.level()
#                 z_sum = [0.0 for d in range(destnum)]
#                 for d in range(destnum):
#                     res_obj += res_x[d]
#                 return res_obj, res_x, res_feasible
#
#
#
#
# if __name__ == "__main__":
#     # print("start...")
#     # 读取request的总数
#     # f = open("allReqNum.txt", "r")
#     # line = f.readline()
#     # line = line.split()
#     # reqNUM = int(line[0])
#     # f.close()
#     # mschedule = CSchedule(reqnum=reqNUM)
#     # mschedule.loadPath()
#     #
#     # # 在线模型运行
#     # # mschedule.MIPOnline()
#     # # # 启发式算法运行
#     # # mschedule.SRCSemiFlexiable()
#     # # 离线模型运行
#     # mschedule.MIPOffline()
#     with Model("test") as M:
#         x = M.variable('X', [2, 2], Domain.greaterThan(0.0))
#         # y = M.variable('Y', [srcnum,ss destnum, pathnum, slotnum], Domain.greaterThan(0.0))
#
#         # for i in range(2):
#         #     x1 = 0
#         #     for j in range(2):
#         #         x1 = Expr.add(x1, x.index(i, j))
#         #     M.constraint(x1, Domain.equalsTo(2))
#         #
#         # for j in range(2):
#         #     x2 = 0
#         #     for i in range(2):
#         #         x2 = Expr.add(x2, x.index(i, j))
#         #     M.constraint(x2, Domain.equalsTo(2))
#         M.constraint(Expr.add(x.index(0, 1), x.index(0, 0)), Domain.equalsTo(2))
#         M.constraint(Expr.add(x.index(0, 1), x.index(1, 1)), Domain.equalsTo(2))
#
#         M.objective("completed_dest", ObjectiveSense.Maximize, Expr.sum(x))
#
#         M.solve()
#         res_obj = 0
#         res_x = 0
#         res_feasible = False
#         acceptable = [
#             ProblemStatus.PrimalAndDualFeasible,
#             ProblemStatus.PrimalFeasible,
#             ProblemStatus.DualFeasible]
#
#         if M.getProblemStatus(SolutionType.Default) in acceptable:
#             # print "feasible"
#             res_feasible = True
#
#         if res_feasible == False:
#             # print "nonfeasible: flexible source!"
#             # print M.getPrimalSolutionStatus()
#             # print M.getProblemStatus(SolutionType.Default)
#             print(res_obj, res_x, res_feasible)
#
#         else:
#             res_x = x.level()
#             z_sum = [0.0 for d in range(4)]
#             for d in range(4):
#                 res_obj += res_x[d]
#             print(res_obj, res_x, res_feasible)
#
#     # print("end!!!")
#     # freq.close()

