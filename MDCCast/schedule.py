#!/usr/bin/env python 
# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import division
import time
from mosek_model.mosek_api import *
from genRequest import *


class CSchedule:

    def __init__(self, reqnum, slotnum):
        self.SLOTNUM = int(slotnum)  # 150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = int(reqnum)
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 15  # 16000000, 单位是MB/S，fsize的单位也是MB, 所以用再进行bytes与bits之间的转换

    def loadTree(self):
        f = open("./Graph/treeAllReq.txt", "r")
        line = f.readline()
        line = line.split()
        self.NODENUM = int(line[0])
        self.LINKNUM = int(line[1])
        self.TREENUM = int(line[2])
        # this variate presents c_e_t, and 16Gps/link
        self.LinkCaperSlot = [self.linkCapacity for row in range(self.LINKNUM)]

        # 实际网络中，要预留出一部分的带宽
        # for linkid in range(self.LINKNUM):
        #     for slotid in range(self.SLOTNUM):
        #         interact = random.uniform(self.highpriotraffic_lower, self.highpriotraffic_upper)
        #         interact = 1 - interact
        #         self.LinkCaperSlot[linkid][slotid] *= interact

        # self.linontree是所有requests的情况
        self.linkontree = [[[0 for e in range(self.LINKNUM)] for t in range(self.TREENUM)] for i in range(self.reqNUM)]
        for i in range(self.reqNUM):
            for t in range(self.TREENUM):
                line = f.readline()
                line = line.split()
                for num in line:
                    self.linkontree[i][t][int(num) - 1] = 1

        f.close()

    def MDCCastOnline(self):
        self.loadTree()
        # print(self.linkontree)

        # time.clock()产生当前request的开始时间
        # start_time = time.clock()
        # self.totalSize = 0
        print("\nstart MDCCastOnline...")
        freq = open("request.txt", "r")
        # 进行此操作的目的是为了将即将写入数据的txt文件中的内容清空
        fl = open("./result/acceptedratio_stein_tree.txt", "w")
        fl.close()

        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)

        tcur = 0
        reqnum_tcur = 0
        # 此处的处理时间是对所有request的处理时间
        start_time = time.clock()
        # 在线处理，每次同时处理同一时隙内所有到达的request
        while tcur < self.SLOTNUM:
            # print "SLOTNUM, slot time:", self.SLOTNUM, tcur
            line = freq.readline()
            line = line.split()
            reqperSlotcur = int(line[0])
            # print(reqperSlotcur)
            reqnum_tcur += reqperSlotcur
            # process the requests arrive in each slot

            rSlotnumperReq = [0 for r in range(reqperSlotcur)]
            fsizeperReq = [0 for r in range(reqperSlotcur)]
            reqcount = 0
            #
            # print(Linkonpath)
            while reqcount < reqperSlotcur:
                line = freq.readline()
                line = line.split()
                rsrc = int(line[0]) - 1
                # print(line, reqperSlotcur)
                r_start = int(line[1])
                r_end = int(line[2])
                rSlotnum = int(r_end - r_start + 1)
                rSize = int(line[3])
                sinkNum = int(line[4])

                fsizeperReq[reqcount] = rSize
                rSlotnumperReq[reqcount] = rSlotnum

                reqcount += 1
            # 如果该时隙没有的request到达，就直接到下一时隙
            if reqperSlotcur != 0:
                # 中间变量，用于临时存储上一次迭代的结果： (x(t))^k
                temp_flow_rate = [[0.0 for t in range(self.TREENUM)] for i in range(reqperSlotcur)]
                # 目标函数中的W
                W = [[1.0 for t in range(self.TREENUM)] for i in range(reqperSlotcur)]
                # 此处的linkontree只取self.linkontree中本时隙内包含的requests的部分
                linkontree = self.linkontree[(reqnum_tcur-reqperSlotcur):reqnum_tcur]
                delta = 10 ** (-8)
                sparse_flag = False
                # status == invisible时，需要将优先级最低的request剔除。这个count用来计数：当前时隙共剔除几个requests
                count = 1

                # ################throughoutput-Maximize#################################### #
                while True:
                    solu_x, solu_feasible = steinertreeLPmodel(reqperSlotcur, self.TREENUM, self.LINKNUM, rSlotnumperReq,
                                                               fsizeperReq, linkontree, LinkResCaperSlot, W)

                    # status == invisible
                    if not solu_feasible:
                        reqperSlotcur -= count
                        # 剔除了，就是reject了
                        self.rejectReqs += 1
                        # self.loadTree()
                        # print(self.linkontree)
                        # 当前时隙所有request都被拒绝了
                        if reqperSlotcur == 0:
                            # print("All requests are rejected in NO %d timeslot!" % (tcur))
                            break
                        else:
                            '''
                            为了方便，现在是默认排在末尾的request优先级最低
                            '''
                            rSlotnumperReq = rSlotnumperReq[:reqperSlotcur]
                            fsizeperReq = fsizeperReq[:reqperSlotcur]
                            self.linkontree = linkontree[:reqperSlotcur]
                            W = W[:reqperSlotcur]
                            continue

                    # 如果status == true, 判断当前可行解是否是最优解
                    for i in range(reqperSlotcur):
                        for t in range(self.TREENUM):
                            # 所有的request对应的x都是最优解
                            if abs(temp_flow_rate[i][t] - solu_x[i * self.TREENUM + t]) <= delta:
                                sparse_flag = True
                            else:
                                sparse_flag = False
                                W[i][t] = 1 / (solu_x[i * self.TREENUM + t] + delta)
                                temp_flow_rate[i][t] = solu_x[i * self.TREENUM + t]

                    # 存在可行解但不是最优解
                    if (solu_feasible == True) and (sparse_flag == False):
                        continue
                    # 求的最优解，更新链路剩余容量
                    if (solu_feasible == True) and (sparse_flag == True):
                        for i in range(reqperSlotcur):
                            for t in range(self.TREENUM):
                                if solu_x[i * self.TREENUM + t] != 0:
                                    for e in range(self.LINKNUM):
                                        if linkontree[i][t][e] == 1:
                                            LinkResCaperSlot[e] -= solu_x[i * self.TREENUM + t]
                                            # 如果有链路的容量小于0, 那肯定是程序写错了:(
                                            if LinkResCaperSlot[e] < 0:
                                                print("Error!")
                                                return
                                    # print("第%d个request的第%d棵树的flow_rate为%.2f." % (i, t, solu_x[i * self.TREENUM + t]))
                        break

            tcur += 1
        end_time = time.clock()
        freq.close()

        fl = open("./result/acceptedratio_stein_tree.txt", "a")
        fl.writelines("%d %d %.2f%% %f" % (
            self.reqNUM-self.rejectReqs, self.rejectReqs, (((self.reqNUM-self.rejectReqs) / self.reqNUM) * 100),
            (end_time - start_time)))
        # print(self.acceptReqs / self.reqNUM)
        fl.writelines("\n")
        fl.close()


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

    mschedule = CSchedule(reqnum=reqNUM, slotnum=slotnum)
    mschedule.MDCCastOnline()

    print("end!!!")
