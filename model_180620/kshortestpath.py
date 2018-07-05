# coding=utf-8
import networkx as nx
from node import *
from link import *


class CGraph:

    def __init__(self):
        self.topo = nx.Graph()
        self.numSubpath = 0
        self.NODE_DICT = {}
        self.LINK_DICT = {}  # (src-,sink)-link
        self.LINK_LIST = []  # linkid-link
        self.NUMLINK = 0
        self.NODENUM = 0
        self.cutoff = 5  # simplepath length<=cutoff
        self.pathNum = 5
        self.loadNodes()
        self.loadLinks()
        self.generateTopo()

    def loadNodes(self):
        """
        load the information of nodes from txt
        """
        f = open("nodes.txt", "r")
        line = f.readline()
        while line:
            line = line.split("\t")
            nodeID = int(line[0])
            # NODE_LIST.append(CNode(nodeID))
            self.NODE_DICT[nodeID] = CNode(nodeID)
            line = f.readline()

        self.NODENUM = len(self.NODE_DICT)
        f.close()

    def loadLinks(self):
        """
        load the information of links from txt
        """
        f = open("links.txt", "r")
        line = f.readline()
        while line:
            edge = str(line).split("\t")
            src = int(edge[0])
            sink = int(edge[1])
            weight = int(edge[2])
            linkid = int(edge[3])
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
        """
        use the library named networkx to generate topology
        """
        for node in self.NODE_DICT:
            self.topo.add_node(node)

        for src in self.LINK_DICT:
            for sink in self.LINK_DICT[src]:
                self.topo.add_edges_from([(src, sink)])
                self.topo.add_edge(src, sink, weight=self.LINK_DICT[src][sink].weight)

    def outputKshortestPath(self):
        """
        compute the k-shortest-path
        """
        f = open("linkonpath.txt", "w")
        fn = open("nodeonpath.txt", "w")
        f.writelines("%d %d %d\n" % (self.NODENUM, self.NUMLINK, self.pathNum))
        for src in self.NODE_DICT:
            for sink in self.NODE_DICT:
                if src != sink:
                    pathcount = 0
                    m_pathcount = [0 for i in range(self.cutoff + 1)]
                    for path in nx.all_shortest_paths(self.topo, source=src, target=sink):
                        f.writelines("%d %d " % (src, sink))
                        pathcount += 1
                        m_pathcount[len(path) - 1] += 1
                        self.numSubpath += 1
                        pre = 0
                        fn.writelines("%d " % path[pre])
                        while pre < len(path) - 1:
                            cur = pre + 1
                            if path[pre] in self.LINK_DICT and path[cur] in self.LINK_DICT[path[pre]]:
                                f.writelines("%d " % self.LINK_DICT[path[pre]][path[cur]].id)
                                fn.writelines("%d " % path[cur])
                            else:
                                f.writelines("%d " % self.LINK_DICT[path[cur]][path[pre]].id)
                            pre += 1
                        f.writelines("\n")
                        fn.writelines("\n")
                        if pathcount >= self.pathNum:
                            break

                    if pathcount < self.pathNum:
                        for path in nx.all_simple_paths(self.topo, source=src, target=sink, cutoff=self.cutoff):
                            f.writelines("%d %d " % (src, sink))
                            pathcount += 1
                            m_pathcount[len(path) - 1] += 1
                            self.numSubpath += 1
                            pre = 0
                            fn.writelines("%d " % path[pre])
                            while pre < len(path) - 1:
                                cur = pre + 1
                                if path[pre] in self.LINK_DICT and path[cur] in self.LINK_DICT[path[pre]]:
                                    f.writelines("%d " % self.LINK_DICT[path[pre]][path[cur]].id)
                                    fn.writelines("%d " % path[cur])
                                else:
                                    f.writelines("%d " % self.LINK_DICT[path[cur]][path[pre]].id)
                                pre += 1
                            f.writelines("\n")
                            fn.writelines("\n")
                            if pathcount >= self.pathNum:
                                break
        f.close()
        fn.close()
