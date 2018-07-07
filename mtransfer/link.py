#!/usr/bin/env python 
# -*- coding: utf-8 -*-
class CLink:
    def __init__(self, src, sink, linkid, weight):
        self.src = src 
        self.sink = sink
        self.id=linkid
        self.weight = weight

    def getId(self):
        return self.id
