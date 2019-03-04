#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

if __name__ == '__main__':

    t = 0
    run_num=1
    os.system("python ./Graph/kShortestPath.py")
    while t < run_num:
        
        os.system("python ./genRequest.py")
        os.system("python ./schedule.py")

        t += 1
        
        os.system("cp -r ./result ./%d" % t)
        os.system("cp request_h.txt ./%d" % t)
        os.system("cp allReqNum.txt ./%d" % t)
        
        '''
        dir_name = "result"+ str(t)
        #os.mkdir(dir_name)
        shutil.copytree("./result", dir_name)
        shutil.copy("request_h.txt", dir_name)
        shutil.copy("allReqNum.txt", dir_name)
        '''



