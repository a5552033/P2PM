#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
import random
from Graph.kShortestPath import CGraph


class Request:
    """docstring for Request"""

    def __init__(self):
        self.throughputexpo = 1.0 / 20000  # 1.0/2000000
        self.highpriotraffic_upper = 0.15
        self.highpriotraffic_lower = 0.05
        self.loadscalingfactor = 0.1
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

    def genTraffic(self):
        # print("\nstart generate request...")

        freq = open("traffic.txt", "w")

        for s in range(self.NODENUM):
            for d in range(self.NODENUM):
                if s != d:
                    rthroughput = int(random.expovariate(self.throughputexpo))  # expotentional distribution 20Gbps

                    rSize = int(rthroughput * 1)
                    rSize = self.loadscalingfactor * rSize
                    if rSize > self.Maxint32:
                        rSize = self.Maxint32

                    freq.writelines("%d %d %d " % (s+1, d+1, rSize))
                    freq.writelines("\n")
                else:
                    continue

        freq.close()


if __name__ == "__main__":
    print("generating traffic flow...")
    mgraph = CGraph()
    mgraph.outputKshortestPath()
    mrequest = Request()
    mrequest.loadPath()
    mrequest.genTraffic()
    # test()
    print("end traffic flow generation")
