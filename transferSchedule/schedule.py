#!/usr/bin/env python 
# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import division

from schedule_algorithms import *
        
if __name__ == "__main__":
    print("start...")
    f = open("allReqNum.txt", "r")
    line = f.readline()
    line = line.split()
    reqNUM = int(line[0])
    line = f.readline()
    line = line.split()
    slotnum = int(line[0])
    f.close()

    '''
    f1 = open('netUtilization.csv', mode='a')
    writer1 = csv.writer(f1)
    f2 = open('throughput.csv', mode='a')
    writer2 = csv.writer(f2)
    f3 = open('acceptedratio.csv', mode='a')
    writer3 = csv.writer(f3)
    '''

    mschedule = CSchedule(reqnum=reqNUM, slotnum=slotnum)
    mschedule.loadPath()

    # 在线模型运行
    #flexiblesrc_netUtilization, fixederc_netUtilization, flexiblesrc_throughput, fixedsrc_throughput = 
    #the fixed src model
    #mschedule.MP2Pfixsrc()

    #the flexible src model
    #mschedule.Optflexisrc()

    #flexiblesrc_acceptedratio = mschedule.acceptReqs/reqNUM
    #fixederc_acceptedratio = mschedule.acceptReqs2/reqNUM
    
    
    # 启发式模型
    #heuristic_netUtilization, heuristic_throughput = 
    # mschedule.Quicktransfer()
    #heuristic_acceptedratio = mschedule.acceptReqs3 / reqNUM

    # print(heuristic_netUtilization)
    # 离线模型
    #offline_netUtilization = 0
    #offline_throughput = 0
    #offline_acceptedratio = 0
    #offline_netUtilization, offline_throughput = mschedule.MIPOffline()
    #offline_acceptedratio = mschedule.acceptReqs4/reqNUM
    
    #mschedule.AccelerationAlg()

    mschedule.MDCCastOnline()
    
    #alg2_acceptedratio = mschedule.acceptReqs5 / reqNUM

    '''
    # 网络利用率
    netUtilization = [flexiblesrc_netUtilization, fixederc_netUtilization, heuristic_netUtilization, offline_netUtilization]
    # 吞吐量单位 bit/slot
    throughput = [flexiblesrc_throughput, fixedsrc_throughput, heuristic_throughput, offline_throughput]
    # 接纳率
    acceptedratio = [flexiblesrc_acceptedratio, fixederc_acceptedratio, heuristic_acceptedratio, offline_acceptedratio]
    writer1.writerow(netUtilization)
    writer2.writerow(throughput)
    writer3.writerow(acceptedratio)
    '''

    #f1.close()
    #f2.close()
    #f3.close()

    print("end!!!")
