#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
import copy
import math
import random
import numpy as np
from Graph.SteinerTree import *

'''
generate request暂时不可用
'''

class Request:
    """docstring for Request"""

    def __init__(self, arriratio):
        self.reqArrivalRatio = arriratio
        self.SLOTNUM = 20  # 20 slot = 20 *5s = 100s
        # self.linkCapacity = 10000
        self.deadlinexpo = 0.167  # 0.5h=30min=6*5min/perslot, deadlinexpro=1/6=0.167, 0.083,
        self.throughputexpo = 1.0 / 200  # 1.0/2000000
        self.highpriotraffic_upper = 0.15
        self.highpriotraffic_lower = 0.05
        self.maxtransferpereq = 1  # 6 # 1
        self.loadscalingfactor = 0.3
        self.maxsinkNum = 11
        self.reqnumratio = 0.4
        self.Maxint32 = 2147483647  # the maximum size

    def loadGraph(self):
        f = open("./Graph/treeAllReq.txt", "r")
        line = f.readline()
        line = line.split()
        self.NODENUM = int(line[0])
        self.LINKNUM = int(line[1])
        f.close()

    def genRequest(self):
        # print("\nstart generate request...")

        freq = open("request.txt", "w")

        self.reqperSlot = [0 for slot in range(self.SLOTNUM)]

        tcur = 0
        numOfAllReq = 0

        while tcur < self.SLOTNUM:
            for slotid in range(self.reqArrivalRatio):
                # 服从泊松分布，到达率是0.5
                arrivalslot = int(random.expovariate(1.0 / self.reqArrivalRatio))
                if (tcur + arrivalslot) < self.SLOTNUM:
                    self.reqperSlot[tcur + arrivalslot] += self.maxtransferpereq

            m_reqcount = 0
            # process the requests arrive in each slot
            freq.writelines("%d\n" % self.reqperSlot[tcur])

            numOfAllReq += self.reqperSlot[tcur]

            # freq.writelines("\n")
            while m_reqcount < self.reqperSlot[tcur]:
                # print "reqperSlot, m_reqcount", self.reqperSlot[tcur], m_reqcount
                rsrc = random.randint(0, self.NODENUM - 1)
                rsink = []
                maybesrc = []
                maybesrc.append(rsrc)
                # sinkNum = random.randint(1, self.maxsinkNum)
                # 60%-75% node num as destnation dc
                sinkNum = int((self.NODENUM - 1) * self.reqnumratio)
                # sinkNum = random.randint(int(self.NODENUM * 0.4), int(self.NODENUM * 0.6))
                while len(rsink) < sinkNum:
                    newsink = random.randint(0, self.NODENUM - 1)
                    if newsink != rsrc and newsink not in rsink:
                        rsink.append(newsink)
                        maybesrc.append(newsink)

                rthroughput = int(random.expovariate(self.throughputexpo))  # expotentional distribution 20Gbps
                r_start = tcur
                if r_start == (self.SLOTNUM - 1):
                    r_end = self.SLOTNUM - 1
                else:
                    r_end = self.SLOTNUM
                    while r_end >= self.SLOTNUM:
                        r_end = math.ceil(r_start + random.expovariate(
                            self.deadlinexpo))  # expotentional distribution，1/1hour=1/12slots

                rSize = int(rthroughput * (r_end - r_start + 1))
                rSize = self.loadscalingfactor * rSize
                if rSize > self.Maxint32:
                    rSize = self.Maxint32

                rSlotNum = int(r_end - r_start + 1)
                freq.seek(0, 2)
                # 单位：rSlotnum的单位是5s，rSize的单位是bytes，之后flow_rate是b/(5s)
                freq.writelines("%d %d %d %d %d " % (rsrc + 1, r_start, r_end, rSize, len(rsink)))
                for dest in range(len(rsink)):
                    freq.writelines("%d " % (rsink[dest] + 1))
                freq.writelines("\n")
                m_reqcount += 1

            tcur += 1

        freq.close()
        f = open("allReqNum.txt", "w")
        f.writelines("%d\n" % numOfAllReq)
        f.writelines("%d\n" % self.SLOTNUM)
        f.close()


arriratio = 1

if __name__ == "__main__":
    print("generating requests...")
    mgraph = CGraph()
    # mgraph.outputSteinerTree()
    mrequest = Request(arriratio)
    mrequest.loadGraph()
    mrequest.genRequest()
    # test()
    print("end requests generation!")
