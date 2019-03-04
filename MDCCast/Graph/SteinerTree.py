#!/usr/bin/env python
# encoding: utf-8
import networkx as nx
from Graph.node import *
from Graph.link import *
import sys
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms import approximation as algo


class CGraph:

    def __init__(self):
        self.LINK_DICT = {}  # (src-,sink)-link
        self.LINK_LIST = []  # linkid-link
        self.NODE_DICT = {}
        self.NUMLINK = 0
        self.NODENUM = 0
        self.cutoff = 10  # simplepath length<=cutoff
        self.treeNum = 5
        self.loadNodes()
        self.loadLinks()
        self.generateTopo()

    def loadNodes(self):
        f = open("./Graph/nodes.txt", "r")
        # f = open("nodes.txt", "r")
        line = f.readline()
        while line:
            line = line.split("\t")
            nodeID = int(line[0])
            # NODE_LIST.append(CNode(nodeID))
            # self.NODE_DICT = {}
            self.NODE_DICT[nodeID] = CNode(nodeID)
            line = f.readline()

        self.NODENUM = len(self.NODE_DICT)
        f.close()

    def loadLinks(self):
        f = open("./Graph/links.txt", "r")
        # f = open("links.txt", "r")
        line = f.readline()
        while line:
            edge = str(line).split()
            src = int(edge[0])
            sink = int(edge[1])
            # 这个weighted和容量还是不一样的，这里是用来求最短路的
            weight= int(edge[2])
            linkid= int(edge[3])
            if src not in self.LINK_DICT.keys():
                self.LINK_DICT[src] = {}
            if sink not in self.LINK_DICT[src].keys():
                self.LINK_DICT[src][sink] = None

            self.LINK_DICT[src][sink] = CLink(src, sink, linkid, weight)
            self.LINK_LIST.append(CLink(src, sink, linkid, weight))
            self.NUMLINK += 1
            line = f.readline()
        f.close()

    def generateTopo(self):
        self.topo = nx.DiGraph()
        for node in self.NODE_DICT:
            self.topo.add_node(node)

        for src in self.LINK_DICT:
            for sink in self.LINK_DICT[src]:
                self.topo.add_edges_from([(src, sink)])
                self.topo.add_edge(src, sink, weight=self.LINK_DICT[src][sink].weight)

    def outputSteinerTree(self):
        self.numSubpath = 0
        f = open("./Graph/treeAllReq.txt", "w")
        # f = open("treeAllReq.txt", "w")
        f.writelines("%d %d %d\n" % (self.NODENUM, self.NUMLINK, self.treeNum))
        # terminal_nodes = [1, 2, 3, 4, 5]
        # tree = nx.Graph()
        # tree = algo.steiner_tree(self.topo, terminal_nodes)
        print(self.topo.number_of_edges())
        f.close()


if __name__ == "__main__":
    print("generating Steiner Tree...")
    mgraph = CGraph()
    mgraph.outputSteinerTree()
    print ("end Steiner Tree generation")
    # print mgraph.NODENUM
