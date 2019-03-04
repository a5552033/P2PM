#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import division
import copy
import time
import pandas
from mosek_model.lpmodel import *
from Graph.kShortestPath import *
from genTraffic import *
import os
import csv


class CSchedule:
    def __init__(self):
        self.linkCapacity = 240000

    def loadPath(self):
        f = open("./Graph/linkonpath.txt", "r")
        line = f.readline()
        line = line.split()
        # 第一行读取整个网络拓扑的属性：依次为网络中的结点数，边数和 k-shortest-path的k值
        self.NODENUM = int(line[0])
        self.LINKNUM = int(line[1])
        self.PATHNUM = int(line[2])
        # 每个时隙每条链路上的容量或者带宽初始化为self.linkCapacity = 16000000
        self.LinkCaperLink = [self.linkCapacity for e in range(self.LINKNUM)]
        # 指示函数初始化，4维
        self.PathList = [[[[] for p in range(self.PATHNUM)] for n in range(self.NODENUM)] for n in range(self.NODENUM)]

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

    def LPOffline(self):
        self.loadPath()
        print("\nstart LPOffline...")
        f = open("routing-rusult.txt", "w")
        f.close()

        freq = open("traffic.txt", "r")

        trafficnum = self.NODENUM * (self.NODENUM - 1)
        src = [0 for k in range(trafficnum)]
        dst = [0 for k in range(trafficnum)]
        fsize = [0 for k in range(trafficnum)]
        linkonpath = [[[[0.0 for e in range(self.LINKNUM)] for p in range(self.PATHNUM)] for v in range(self.NODENUM)]
                      for u in range(self.NODENUM)]
        PathLen = [[[0.0 for p in range(self.PATHNUM)] for v in range(self.NODENUM)] for s in range(self.NODENUM)]

        # 第i个需求的source和destination
        for k in range(trafficnum):
            line = freq.readline()
            line = line.split()
            src[k] = int(line[0])-1
            dst[k] = int(line[1])-1
            fsize[k] = int(line[2])

        freq.close()

        # 生成常数I
        for u in range(self.NODENUM):
            for v in range(self.NODENUM):
                if u != v:
                    for p in range(self.PATHNUM):
                        for linkindex in range(len(self.PathList[u][v][p])):
                            linkid = self.PathList[u][v][p][linkindex]
                            # print(linkid, u, v, p)
                            # print(self.PathList)
                            # print(self.LINKNUM, self.NODENUM, self.PATHNUM)
                            # print(linkid, u, v, p)
                            linkonpath[u][v][p][linkid] = 1.0
                            PathLen[u][v][p] += 1

        # begin processing
        routing = LPmodel(trafficnum, self.PATHNUM, self.LINKNUM, src, dst, fsize, linkonpath, self.LinkCaperLink, PathLen)

        print(routing)

        f = open("routing-rusult.txt", "a")
        for k in range(trafficnum):
            f.writelines("%d\t" % (k + 1))
            for linkindex in range(len(self.PathList[src[k]][dst[k]][routing[k]])):
                linkid = self.PathList[src[k]][dst[k]][routing[k]][linkindex]
                f.writelines("%d\t" % (int(linkid)+1))
            f.writelines("\n")

        f.close()


if __name__ == '__main__':
    print("start...")
    mschedule = CSchedule()
    mschedule.loadPath()
    mschedule.LPOffline()

