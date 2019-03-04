#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
import copy
import math
import random
import numpy as np
from Graph.kShortestPath import *


class Request:
    """docstring for Request"""

    def __init__(self, arriratio):
        self.reqArrivalRatio = arriratio
        self.SLOTNUM = 20 #12 slot=1h
        # self.linkCapacity = 10000
        self.deadlinexpo = 0.083 #0.5h=30min=6*5min/perslot, deadlinexpro=1/6=0.167, 0.083,
        self.throughputexpo = 1.0 / 20000  # 1.0/2000000
        self.highpriotraffic_upper = 0.15
        self.highpriotraffic_lower = 0.05
        self.maxtransferpereq = 1  # 6 # 1
        self.loadscalingfactor = 0.1
        self.maxsinkNum = 11
        self.reqnumratio = 0.1
        self.Maxint32 = 2147483647  # the maximum size

    def loadPath(self):
        f = open("./Graph/linkonpath.txt", "r")
        line = f.readline()
        line = line.split()
        self.NODENUM = int(line[0])
        self.LINKNUM = int(line[1])
        self.PATHNUM = int(line[2])
        # this variate presents c_e_t, and 16Gps/link
        # self.LinkCaperSlot = [[self.linkCapacity for col in range(self.SLOTNUM)] for row in range(self.LINKNUM)]

        # 实际网络中，要预留出一部分的带宽
        # for linkid in range(self.LINKNUM):
        #     for slotid in range(self.SLOTNUM):
        #         interact = random.uniform(self.highpriotraffic_lower, self.highpriotraffic_upper)
        #         interact = 1 - interact
        #         self.LinkCaperSlot[linkid][slotid] *= interact

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

    def genRequest(self):
        #print("\nstart generate request...")
        
        freq = open("request_h.txt", "w")

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
                #sinkNum = random.randint(1, self.maxsinkNum)
                # 60%-75% node num as destnation dc
                sinkNum = int((self.NODENUM-1) * self.reqnumratio)
                #sinkNum = random.randint(int(self.NODENUM * 0.4), int(self.NODENUM * 0.6))
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

                rPathNum = self.PATHNUM
                rSlotNum = int(r_end - r_start + 1)
                freq.seek(0, 2)
                # freq = open("request.txt","a")
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
    print ("generating requests...")
    #mgraph = CGraph()
    #mgraph.outputKshortestPath()
    mrequest = Request(arriratio)
    mrequest.loadPath()
    mrequest.genRequest()
    # test()
    print ("end request generation")
