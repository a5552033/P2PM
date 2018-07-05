#!/usr/bin/env python 
# -*- coding: utf-8 -*-
from mipmodel import *
from kshortestpath import *
import time
import os
import copy
import random
import operator
import math

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

    def __init__(self, arriratio):
        self.reqArrivalRatio = arriratio
        self.SLOTNUM = 30 #150 #1slot= 5mins  24h = 288slots
        self.reqNUM = 0
        self.outperformedReqs = 0
        self.rejectReqs = 0
        self.acceptReqs = 0
        self.linkCapacity = 16000000   #16000000
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
        self.NODENUM = int(line[0])
        self.LINKNUM = int(line[1])
        self.PATHNUM = int(line[2])    
        self.LinkCaperSlot = [[self.linkCapacity for col in range(self.SLOTNUM)] for row in range(self.LINKNUM)]
        '''
        for linkid in range(self.LINKNUM):
            for slotid in range(self.SLOTNUM):
                interact = random.uniform(self.highpriotraffic_lower, self.highpriotraffic_upper)
                interact = 1 - interact
                self.LinkCaperSlot[linkid][slotid] *= interact
        '''
        self.PathList = [[[[] for num in range(self.PATHNUM)] for col in range(self.NODENUM)] for row in range(self.NODENUM)]
        line = f.readline()
        pathid = 0
        while line:
            line = line.split()
            srcID = int(line[0])-1
            sinkID = int(line[1])-1

            for i in range (len(line)-2):
        	   self.PathList[srcID][sinkID][pathid%self.PATHNUM].append(int(line[i+2])-1)
            line = f.readline()
            pathid += 1
        f.close()


    def MIPOnline(self):
        accept_mp2p = 0
        self.loadPath()
        excute_computing = False  ##False: generate data and donot excute computation
        fallresult = open("allresults.txt", "a")
        fallresult.writelines("arrival ratio: %d\n" %self.reqArrivalRatio)

        start_time = time.clock()
        self.totalSize = 0
        print "\nstart MIPOnline"
        freq = open("request.txt","w")
        #freq.close()
        m_throughput = 0
        m_acceptRatio = 0.0      

        self.reqperSlot = [0 for slot in range(self.SLOTNUM)]
        linkLoadSlot = [ [0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        linkLoadSlot2 = [ [0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)
        LinkResCaperSlot2 = copy.deepcopy(self.LinkCaperSlot)
        tcur = 0
        while tcur < self.SLOTNUM:
            #print "SLOTNUM, slot time:", self.SLOTNUM, tcur
            for slotid in range(self.reqArrivalRatio):
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
                    if newsink != rsrc  and newsink not in rsink:
                        rsink.append(newsink)
                        maybesrc.append(newsink)

                rthroughput = int(random.expovariate(self.throughputexpo)) #expotentional distribution 20Gbps
                rstart = tcur
                if rstart == (self.SLOTNUM-1):
                    rend = self.SLOTNUM-1
                else:
                    rend = self.SLOTNUM
                    while rend >= self.SLOTNUM:
                        rend = math.ceil(rstart + random.expovariate(self.deadlinexpo)) #expotentional distribution，1/1hour=1/12slots

                rSize = int(rthroughput*(rend-rstart+1))
                rSize = self.loadscalingfactor*rSize
                if rSize > self.Maxint32:
                    rSize = self.Maxint32

                rPathNum = self.PATHNUM
                rSlotNum = int(rend - rstart + 1)
                freq.seek(0,2)
                #freq = open("request.txt","a")
                freq.writelines("%d %d %d %d %d " % (rsrc+1, rstart, rend, rSize, len(rsink)))
                for dest in range(len(rsink)):
                    freq.writelines("%d " %  (rsink[dest]+1))
                freq.writelines("\n")
                self.totalSize += rSize
                m_reqcount += 1
                self.reqNUM += 1

                onesrcLinkonpath = [ [[ 0.0 for p in range(rPathNum)] for d in range(sinkNum)] for e in range(self.LINKNUM)]
                src = maybesrc[0]
                for d in range(sinkNum):
                    sink = rsink[d]
                    for p in range(rPathNum):
                        for linkindex in range(len(self.PathList[src][sink][p])):
                            linkid = self.PathList[src][sink][p][linkindex]
                            onesrcLinkonpath[linkid][d][p] = 1.0

                Linkonpath = [ [ [[ 0.0 for p in range(rPathNum)] for d in range(sinkNum)] for s in range(sinkNum+1) ] for e in range(self.LINKNUM)]
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
                        reslinktimecap[e][t] = LinkResCaperSlot[e][t+rstart]
                        reslinktimecap2[e][t] = LinkResCaperSlot2[e][t+rstart]

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
                                        LinkResCaperSlot[linkid][t+rstart] -= solu_y[(s*sinkNum+d)*rPathNum*rSlotNum+p*rSlotNum+t]
                                        linkLoadSlot[linkid][t+rstart] += solu_y[(s*sinkNum+d)*rPathNum*rSlotNum+p*rSlotNum+t]
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
                                    LinkResCaperSlot2[linkid][t+rstart] -= solu_yy[d*rPathNum*rSlotNum+p*rSlotNum+t]
                                    linkLoadSlot2[linkid][t+rstart] += solu_yy[d*rPathNum*rSlotNum+p*rSlotNum+t]
                                    
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



    def AccelerationAlg(self):
        #request.txt
        #request_format:(rsrc+1, rstart, rend, rSize, len(rsink),(rsink[dest]+1))
        #load request
        request_List=[]
        reqfile = open("request.txt","r")
        reqline = reqfile.readline()
        reqid = 0
        destlist = []
        while reqline:
            reqline = reqline.split()
            src = int(reqline[0])-1
            tstart = int(reqline[1])-1
            tend = int(reqline[2])-1
            size = int(reqline[3])
            destnum = int(reqline[4])
            for i in range(destnum):
                destlist.append(int(reqline[5+i])-1)
            req_instance = CRequest(reqid, src, destlist, tstart, tend, size)
            destlist =[]
            request_List.append(req_instance)
            reqline = reqfile.readline()
            reqid += 1
        reqfile.close()
        print "requestnum ", len(request_List)

        #begin process
        rPathNum = self.PATHNUM
        linknum = self.LINKNUM
        linkLoadSlot = [ [0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        linkLoadSlot2 = [ [0 for slot in range(self.SLOTNUM)] for link in range(self.LINKNUM)]
        LinkResCaperSlot = copy.deepcopy(self.LinkCaperSlot)
        tcur = 0
        req_pos = 0
        acceptance_alg2 = 0
        
        while tcur < self.SLOTNUM:
            ##every time add requests start from tcur to the processing requet list
            processing_reqlist = []
            while req_pos < len(request_List) and request_List[req_pos].tstart == tcur:
                #print "tcur, req_pos", tcur, req_pos
                processing_reqlist.append(request_List[req_pos])
                req_pos +=1
            tcur+=1
            #processing the requests in the request lists
            if len(processing_reqlist) == 0:
                continue
            print "\n tcur, requestnum", tcur, len(processing_reqlist)
            for req_instance in processing_reqlist:
                reqid = req_instance.reqid
                #print "reqid", reqid
                src = req_instance.src
                destlist = []
                destlist = req_instance.sinklist
                start_time = req_instance.tstart
                deadline = req_instance.tend
                fsize = req_instance.size
                sinkNum = len(destlist)

                linkonpath = [ [ [[ 0.0 for p in range(rPathNum)] for d in range(sinkNum)] for s in range(sinkNum+1) ] for e in range(self.LINKNUM)]
                for d in range(sinkNum):
                    sink = destlist[d]
                    if src == sink: continue
                    for p in range(rPathNum):
                        for linkindex in range(len(self.PathList[src][sink][p])):
                            linkid = self.PathList[src][sink][p][linkindex]
                            linkonpath[linkid][0][d][p] = 1.0
                for s in range(sinkNum):
                    src = destlist[d]
                    for d in range(sinkNum):
                        sink = destlist[d]
                        if src == sink: continue
                        for p in range(rPathNum):
                            for linkindex in range(len(self.PathList[src][sink][p])):
                                linkid = self.PathList[src][sink][p][linkindex]
                                linkonpath[linkid][s+1][d][p] = 1.0
                
                rSlotNum = deadline - start_time + 1
                reslinktimecap = [ [0.0 for t in range(rSlotNum)] for e in range(self.LINKNUM) ]
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        reslinktimecap[e][t] = LinkResCaperSlot[e][t+start_time]
                
                #print "solve problem: size, destnum, srcnum, slotnum ", fsize, sinkNum, sinkNum+1, rSlotNum
                #kMax = min(4, rSlotNum)
                #time_interval = (deadline-start_time+1)/kMax
                time_interval = min(2, rSlotNum)
                kMax = int(math.ceil(rSlotNum/time_interval))
                #print kMax
                time_series = [time_interval for i in range(kMax)]
                time_series[kMax-1] = deadline - start_time + 1 - time_interval*(kMax-1)
                assignedsrcfordest = [[0 for d in range(sinkNum)] for s in range(sinkNum+1)] #maintain the states of assigned srcs for every dest
                sourcelist = [] #maintian the id of sites that can be served as source 
                sourcelist.append(0) #push the original source into this list, id =0, numbered from 0 to sinknum+1
                remainratio = [1.0 for j in range(sinkNum)] #at the start, remain ratio is initalized to 1.0
                #print "kmax, timelist", kMax, time_series
                kcur = 0
                #print "remainratio, sourcelist", remainratio, sourcelist
                while sum(remainratio) > 0.0001 and kcur < kMax:
                    #generate data for each solving
                    slotnum = time_series[kcur]
                    #print "kcur, slotnum", kcur, slotnum
                    linktimecap = [ [0.0 for t in range(slotnum)] for e in range(self.LINKNUM) ]
                    for e in range(self.LINKNUM):
                        for t in range(slotnum):
                            linktimecap[e][t] = reslinktimecap[e][kcur*time_interval+t]   
                    #run the linear programming to maximize the throughput
                    solu_w, solu_y, solu_z, solu_feasible = maxThroughputmodel(rPathNum,linknum, sinkNum, fsize, slotnum, linkonpath, linktimecap, remainratio, assignedsrcfordest, sourcelist) 
                    #update assignedsrcfordest, sourcelist, remainratio, reslintimecap
                    if solu_feasible == False:
                        kcur += 1
                        continue
                    for d in range(sinkNum):
                        remainratio[d] -= round(solu_w[d],2)
                        remainratio[d] = round(remainratio[d],2)
                        if remainratio[d] < 0.0001:
                            sourcelist.append(d+1)
                    sourcelist = list(set(sourcelist))
                    
                    for s in range(sinkNum+1):
                        for d in range(sinkNum):
                            if solu_z[s*sinkNum+d] == 1 and solu_w[d] > 0:
                                #print "solu_z, solu_w", solu_z[s*sinkNum+d], solu_w[d]
                                assignedsrcfordest[s][d] = 1
                    #print "assignsrc for dest", assignedsrcfordest
                    #print "remainratio, sourcelist", remainratio, sourcelist
                       
                    for s in range(sinkNum+1):
                        for d in range(sinkNum):
                            k = s*sinkNum + d
                            for p in range(rPathNum):
                                for t in range(slotnum):
                                    for e in range(self.LINKNUM):
                                        linktimecap[e][t]-=linkonpath[e][s][d][p]*solu_y[k*rPathNum*slotnum+p*slotnum+t]
    
                    for e in range(self.LINKNUM):
                        for t in range(slotnum):
                            reslinktimecap[e][kcur*time_interval+t] = linktimecap[e][t]     

                    kcur += 1
                #check if the deadline is satisfied
                if sum(remainratio) < 0.00001:
                    #print "meet the deadline!"
                    acceptance_alg2 += 1
                #if sum(remainratio) > 0.00001:
                #    print "miss the deadline!"
                    #print "remainratio", remainratio
                #update LinkResCaperSlot according to reslinktimecap
                for e in range(self.LINKNUM):
                    for t in range(rSlotNum):
                        LinkResCaperSlot[e][t+start_time] = reslinktimecap[e][t]
        print "alg2-acceptance:", acceptance_alg2
                

arriratio = 2

if __name__ == "__main__":
    #print "start..."
    mgraph = CGraph()
    #mgraph.outputKshortestPath()
    mschedule = CSchedule(arriratio)
    mschedule.loadPath()
    #mschedule.MIPOnline()
    mschedule.AccelerationAlg()
    #test()
    print "end!!!"