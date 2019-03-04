#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from genRequest import *
from Graph.kShortestPath import *

if __name__ == '__main__':

    destnum = 0.5
    run_num = 1
    os.system("python ./Graph/kShortestPath.py")
    while destnum <= 0.5:

        print ("generating requests...")
        mrequest = Request(destnum)
        mrequest.genRequest()
        print ("end request generation")

        print ("generating trees...")
        mgraph = CGraph()
        mgraph.outputSteinertree()
        print ("end tree generation...")
        
        os.system("python ./schedule.py")
        
        os.system("cp -r ./result ./%.1f" % destnum)
        os.system("cp request_h.txt ./%.1f" % destnum)
        os.system("cp allReqNum.txt ./%.1f" % destnum)
        destnum += 0.1
        
        '''
        dir_name = "result"+ str(t)
        #os.mkdir(dir_name)
        shutil.copytree("./result", dir_name)
        shutil.copy("request_h.txt", dir_name)
        shutil.copy("allReqNum.txt", dir_name)
        '''



