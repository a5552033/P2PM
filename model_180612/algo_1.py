#!/usr/bin/env python 
# encoding: utf-8

import copy
import math
import random
import time
from kShortestPath import *
from mosek_api import *

'''
CRequest类
数据成员:
        reqId: 每个到达的request的编号
        src: t_1时刻的transfer source
        sinklist: 当前request的destination data centers
        size: 从源结点到目的结点传输数据的总容量
        tstart: 当前Request的到达时刻
        tend: 当前Request的结束时刻
        sentsize: ?
        remainsize: ?
'''
class CRequest:
    def __init__(self, reqId, src, sinklist, tstart, tend, size):
        self.reqId = reqId
        self.src = src
        self.sinklist = sinklist
        self.tstart = tstart
        self.tend = tend
        self.size = size
        self.sentsize = 0
        self.remainsize = size

'''
CSchedule类
数据成员:
        reqArrivalRatio: 在某个时间段内request的到达率
        SLOTNUM: 将某个时间段分割成多少个时隙，现在一个时隙5mins
        reqNUM: 某个时间段内到达的request的数目
        outperformedReqs: ？
        rejectReqs: 某个时间段内拒绝的request数目
        acceptReqs: 某个时间段内接受的request数目
        linkCapacity: 
        highpriotraffic_upper:
        highpriotraffic_lower: 
        deadlinexpo:
        throughputexpo:
        loadscalingfactor: 
        maxtransferpereq: 
        Maxint32: 
        maxsinkNum: 
成员函数:
        loadPath(): 
        Optimization(): mosek构建优化模型，目的是判断reques是否可被接受

'''
class CSchedule:

    def __init__(self,arriratio):
        self.reqArrivalRatio = arriratio
        self.SLOTNUM = 288 #150mins #1slot= 5mins  24h = 288slots
        self.reqNUM = 0
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 160000000   #16000000
        self.highpriotraffic_upper = 0.15
        self.highpriotraffic_lower = 0.05
        self.deadlinexpo = 0.18#0.083 #0.083  ###end time slot according with exppenntioonal  distributioon，0.083=1/1hour=1/12slots
        self.throughputexpo = 1.0/20000000#1.0/20000000#  600000##20Gps, throughput according with exppenntioonal  distributioon
        self.loadscalingfactor = 1
        self.maxtransferpereq = 1#6
        self.Maxint32 = 2147483647  #the maximum size
        self.maxsinkNum = 4

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
        self.PathList = [[[[] for num in range(self.PATHNUM)] for col in range(self.NODENUM)] for row in range(self.NODENUM)]
        
        line = f.readline()
        pathid = 0
        while line:
            line = line.split()
            srcID = int(line[0])-1
            sinkID = int(line[1])-1

            # for循环的作用在于将结点“srcID”到结点“sinkID”的第pathid%self.PATHNUM条路上存在编号为line[i+2])-1的边
            for i in range(len(line)-2):
                self.PathList[srcID][sinkID][pathid%self.PATHNUM].append(int(line[i+2])-1)
            line = f.readline()
            pathid += 1
        f.close()

    def MIPOnline(self):
        accept_mp2p = 0
        self.loadPath()
        excute_computing = False  #False: generate data and donot excute computation
        fallresult = open("allresults.txt", "a")
        fallresult.writelines("arrival ratio: %d\n" %self.reqArrivalRatio)

        # time.clock()产生当前request的开始时间
        start_time = time.clock()
        self.totalSize = 0
        print "\nstart MIPOnline"
        freq = open("request.txt", "w")
        #freq.close()

        # self.request: 表示在第i个时隙到达的request
        self.reqperSlot = [0 for slot in range(self.SLOTNUM)]
        # linkLoadSlot: 表示在第i条边上在j时隙上remain volumn
        linkLoadSlot = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        linkLoadSlot2 = [[0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        # ？
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)
        LinkResCaperSlot2 = copy.deepcopy(self.LinkCaperSlot)

        # tcur: 当前的slot time
        tcur = 0
        while tcur < self.SLOTNUM:
            #print "SLOTNUM, slot time:", self.SLOTNUM, tcur
            # ?
            for slotid in range(self.reqArrivalRatio):
                # 服从泊松分布，到达率是0.5
                arrivalslot = int(random.expovariate(1.0/self.reqArrivalRatio))
                if (tcur+arrivalslot) < self.SLOTNUM:
                    self.reqperSlot[tcur+arrivalslot] += self.maxtransferpereq
            
            #self.reqNUM += self.reqperSlot[tcur]
            m_reqcount = 0
            #process the requests arrive in each slot
            while m_reqcount < self.reqperSlot[tcur]:
                #print "reqperSlot, m_reqcount", self.reqperSlot[tcur], m_reqcount
                self.coeffPositive = True
                rsrc = random.randint(0, self.NODENUM-1)
                rsink = []
                maybesrc = []
                maybesrc.append(rsrc)
                #sinkNum = random.randint(1, self.maxsinkNum)
                #60%-75% node num as destnation dc
                sinkNum = random.randint(int(self.NODENUM*0.6), int(self.NODENUM*0.75))
                while len(rsink) < sinkNum:
                    newsink =random.randint(0, self.NODENUM-1)
                    if newsink != rsrc and newsink not in rsink:
                        rsink.append(newsink)
                        maybesrc.append(newsink)

                rthroughput = int(random.expovariate(self.throughputexpo)) #expotentional distribution 20Gbps
                r_start = tcur
                if r_start == (self.SLOTNUM-1):
                    r_end = self.SLOTNUM-1
                else:
                    r_end = self.SLOTNUM
                    while r_end >= self.SLOTNUM:
                        r_end = math.ceil(r_start + random.expovariate(self.deadlinexpo)) #expotentional distribution，1/1hour=1/12slots

                rSize = int(rthroughput*(r_end-r_start+1))
                rSize = self.loadscalingfactor*rSize
                if rSize > self.Maxint32:
                    rSize = self.Maxint32

                rPathNum = self.PATHNUM
                rSlotNum = int(r_end - r_start + 1)
                freq.seek(0,2)
                #freq = open("request.txt","a")
                freq.writelines("%d %d %d %d %d " % (rsrc+1, r_start, r_end, rSize, len(rsink)))
                for dest in range(len(rsink)):
                    freq.writelines("%d " %  (rsink[dest]+1))
                freq.writelines("\n")
                self.totalSize += rSize
                m_reqcount += 1
                self.reqNUM += 1

                onesrcLinkonpath = [[[ 0.0 for p in range(rPathNum)] for d in range(sinkNum)] for e in range(self.LINKNUM)]
                src = maybesrc[0]
                for d in range(sinkNum):
                    sink = rsink[d]
                    for p in range(rPathNum):
                        for linkindex in range(len(self.PathList[src][sink][p])):
                            linkid = self.PathList[src][sink][p][linkindex]
                            onesrcLinkonpath[linkid][d][p] = 1.0

                Linkonpath = [[[[ 0.0 for p in range(rPathNum)] for d in range(sinkNum)] for s in range(sinkNum+1) ] for e in range(self.LINKNUM)]
                for s in range(sinkNum+1):
                    src = maybesrc[s]
                    for d in range(sinkNum):
                        sink = rsink[d]
                        if src == sink: continue
                        for p in range(rPathNum):
                             for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                Linkonpath[linkid][s][d][p] = 1.0

                reslinktimecap = [ [0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM) ]
                reslinktimecap2 = [ [0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM) ]
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        reslinktimecap[e][t] = LinkResCaperSlot[e][t+r_start]
                        reslinktimecap2[e][t] = LinkResCaperSlot2[e][t+r_start]

                #################acceptance-Maximize####################################
                #print Linkonpath[e]
                #limit the data source of a receiver to be no more than 1
                srcUB = 1
                #while srcUB <(sinkNum+1):
                competedest, solu_x, solu_w, solu_y, solu_feasible = flexiblesrcMIPmodel(rPathNum, self.LINKNUM, sinkNum, rSlotNum, rSize, Linkonpath, reslinktimecap, srcUB)
                #srcUB += 1
                #if solu_feasible == False:
                #    break
                competedest2, solu_xx, solu_ww, solu_yy, solu2_feasible = fixsrcMIPmodel(rPathNum, self.LINKNUM, sinkNum, rSlotNum, rSize, onesrcLinkonpath, reslinktimecap2)
                #update,outperformed includes fraction completion
                if (competedest - competedest2) > 0.1:
                    self.outperformedReqs += 1
                    #print "competedest,w", competedest, solu_w
                    #print "competedest2,ww", competedest2, solu_ww
                if solu_feasible == False or abs(competedest - sinkNum) > 0.1:
                    self.rejectReqs += 1
                if (solu_feasible == True) and (abs(competedest - sinkNum) < 0.1):
                    self.acceptReqs += 1
                    for s in range(sinkNum+1):
                        src = maybesrc[s]
                        for d in range(sinkNum):
                            sink = rsink[d]
                            for p in range(rPathNum):
                                for linkindex in range(len(self.PathList[src][sink][p])):
                                    linkid = self.PathList[src][sink][p][linkindex]
                                    for t in range(rSlotNum):
                                        LinkResCaperSlot[linkid][t+r_start] -= solu_y[(s*sinkNum+d)*rPathNum*rSlotNum+p*rSlotNum+t]
                                        linkLoadSlot[linkid][t+r_start] += solu_y[(s*sinkNum+d)*rPathNum*rSlotNum+p*rSlotNum+t]
                if (solu2_feasible == True) and (abs(competedest2 - sinkNum) < 0.1):
                    accept_mp2p += 1
                    src = maybesrc[0]
                    for d in range(sinkNum):
                        sink = rsink[d]
                        for p in range(rPathNum):
                            for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                for t in range(rSlotNum):
                                    #print len(solu_yy), d, p, t
                                    LinkResCaperSlot2[linkid][t+r_start] -= solu_yy[d*rPathNum*rSlotNum+p*rSlotNum+t]
                                    linkLoadSlot2[linkid][t+r_start] += solu_yy[d*rPathNum*rSlotNum+p*rSlotNum+t]
                                    
            tcur += 1
        p2mp_netUtilization = 0.0
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                p2mp_netUtilization += 1.0*linkLoadSlot[linkid][slotid]/self.LinkCaperSlot[linkid][slotid]
        p2mp_netUtilization *= 100
        p2mp_netUtilization /= self.LINKNUM
        p2mp_netUtilization /= self.SLOTNUM

        mp2p_netUtilization = 0.0
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                mp2p_netUtilization += 1.0*linkLoadSlot2[linkid][slotid]/self.LinkCaperSlot[linkid][slotid]
        mp2p_netUtilization *= 100
        mp2p_netUtilization /= self.LINKNUM
        mp2p_netUtilization /= self.SLOTNUM
        elapsed_time = (time.clock() - start_time)
 
        print "total reqs, flexiblesrc-acceptance:", self.reqNUM, self.acceptReqs
        print "amoeba-acceptance:", accept_mp2p
        print "rejection, outperformedReqs:", self.rejectReqs, self.outperformedReqs
        print "net_utilization: mone, mp2p:", p2mp_netUtilization, mp2p_netUtilization
        freq.close()
                

arriratio = 2

if __name__ == "__main__":
    #print "start..."
    mgraph = CGraph()
    #mgraph.outputKshortestPath()
    mschedule = CSchedule(arriratio)
    mschedule.loadPath()
    mschedule.MIPOnline()
    # mschedule.AccelerationAlg()
    #test()
    print "end!!!"