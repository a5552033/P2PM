#!/usr/bin/env python
# encoding: utf-8
import networkx as nx
from node import *
from link import *
import random
import copy


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


class CGraph:

    def __init__(self):
        self.LINK_DICT = {}  # (src-,sink)-link
        self.LINK_LIST = []  # linkid-link
        self.NODE_DICT = {}
        self.NUMLINK = 0
        self.NODENUM = 0
        self.cutoff = 10  # simplepath length<=cutoff
        self.treenum = 4
        self.pathNum = 5
        self.loadNodes()
        self.loadLinks()
        self.generateTopo()

    def loadNodes(self):
        f = open("./Graph/nodes.txt", "r")
        #f = open("nodes.txt", "r")
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
        #f = open("links.txt", "r")
        line = f.readline()
        while line:
            edge = str(line).split("\t")
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
        self.topo = nx.Graph()
        for node in self.NODE_DICT:
            self.topo.add_node(node)
        for src in self.LINK_DICT:
            for sink in self.LINK_DICT[src]:
                self.topo.add_edges_from([(src, sink)])
                self.topo.add_edge(src, sink, weight=self.LINK_DICT[src][sink].weight)
    
    
    def DFS(self, topo, check_node, dstlist):
        if self.dstfound == dstlist:
            return True
        adjnode_list = list(topo.neighbors(check_node))
        adjnode_list = sorted(iter(adjnode_list), key=lambda k: random.random())
        adjvisited = True
        parent_node = check_node
        for nxt_node in adjnode_list:
            if self.visited[nxt_node-1] == False:
                adjvisited = False
                #print "add links(check_node, nxt_node)",check_node, nxt_node
                #linkid = self.LINK_DICT[check_node][nxt_node].id
                treefile = open("./Graph/trees.txt", "a")
                #treefile.writelines("%d " % (linkid))
                treefile.writelines("%d  %d  " % (check_node, nxt_node))
                treefile.close()
                check_node = nxt_node
                self.visited[nxt_node-1] = True
                if (check_node) in dstlist:
                    self.dstfound.append(check_node)
                if self.DFS(topo, check_node, dstlist):
                    return True
                if self.DFS(topo, check_node, dstlist) == False:
                    check_node = parent_node
        if adjvisited == True:
            #print "all neibor has been fixed!"
            return False
        return False

            
    def steinerTree(self, topo, src, destlist, treenum_initial, treenum_final):
        #print "src, destlist", src, destlist
        clearfile = open("./Graph/trees.txt", "w")
        clearfile.close()
        k = 0
        while k < treenum_initial:
            self.visited = [False for n in range(topo.number_of_nodes())]
            self.dstfound = []
            check_node = src
            self.visited[check_node-1] = True
            
            #print "\nfinding tree: ", k
            self.DFS(topo, check_node, destlist)
            treefile = open("./Graph/trees.txt", "a")
            treefile.writelines("\n")
            treefile.close()
            k+=1
        
        tree_list = []
        treefile = open("./Graph/trees.txt", "r")  
        treeline = treefile.readline()
        treeline = treeline.split()
        istree = True    
        while treeline:
            i=0
            g = nx.DiGraph()
            while i < (len(treeline)-1):
                pre_node = int(treeline[i])
                nxt_node = int(treeline[i+1])
                g.add_node(pre_node)
                g.add_node(nxt_node)
                g.add_edge(pre_node,nxt_node)
                if nxt_node == src:
                    print "bug, src, dst", src, destlist, treeline
                i+=2
            istree = True
            for v in destlist:
                if v not in g.nodes() or src not in g.nodes() or g.out_degree(src) == 0:
                    istree = False
                    #print "\nBug, the ogrinal tree!"
                    #print "tree not include dest node", v
                    #print "tree", treeline
            for (s, d) in g.edges():
                if d == src:
                    print "bug!! src has a income link!"
            if istree==True:
                tree_list.append(g)
            treeline = treefile.readline()
            treeline = treeline.split()
            
        treefile.close()
        #cut not neccesary links
        treecut_list = []
        for tree in tree_list:
            #if tree.out_degree(src) == 0:
                #print "before update"
                #print "bug, src degree!", tree.out_degree(v)
                #print tree.nodes()
            new_t, updated = self.updateTree(tree, destlist, src)
            for v in destlist:
                if v not in new_t.nodes():
                    print "bug, new_t.nodes", new_t.nodes()
                    print "dest", destlist
            if src not in new_t.nodes():
                print "bug, new_t.nodes", new_t.nodes()
                print "src", src
            treecut_list.append(new_t)
            #print "new_t", new_t.nodes(), new_t.edges()
        for check_tree in treecut_list:
            for cmp_tree in treecut_list:
                if check_tree != cmp_tree and check_tree.edges() == cmp_tree.edges():
                    #print check_tree.edges(), cmp_tree.edges()
                    treecut_list.remove(cmp_tree)

        #write compact trees to file
        treefile = open("./Graph/treeAllReq.txt", "a")
        treefile2 = open("./Graph/treeAllReqnode.txt", "a")
        t_count = 0
        enough_tree = False
        while t_count < treenum_final and enough_tree == False:
            for t in treecut_list:
                t_count +=1
                for (s, d) in t.edges():
                    #if d == src:
                    #    print "bug, src has a income link!"
                    linkid = self.LINK_DICT[s][d].id
                    treefile.writelines("%d " %linkid)
                    treefile2.writelines("%d %d " %(s, d))
                treefile.writelines("\n")
                treefile2.writelines("\n")
                if t_count >= treenum_final:
                    enough_tree = True
                    break
        treefile.close()
        treefile2.writelines("\n")
                    
    def updateTree(self, tree, destlist, src):
        updated = False
        updated_tree = copy.deepcopy(tree)
        #print "src.degree before remove", tree.out_degree(src)
        for v in tree.nodes():
            #if v == src and tree.out_degree(v) == 0:
                #print "bug, src degree!", tree.out_degree(v)
                #print tree.nodes()
            if v != src and v not in destlist and tree.out_degree(v) == 0:
                parent = tree._pred[v].keys()
                updated_tree.remove_edge(parent[0], v)
                updated_tree.remove_node(v)
                updated = True
        if updated == True:
            new_tree = copy.deepcopy(updated_tree)
            updated_tree, updated = self.updateTree(new_tree, destlist, src)
        return updated_tree, updated

    def outputSteinertree(self):
        treefile = open("./Graph/trees.txt", "w")
        treefile.close()
        treefile2 = open("./Graph/treeAllReq.txt", "w")
        treefile2.writelines("%d  %d  %d\n" %(len(self.NODE_DICT), len(self.LINK_LIST), self.treenum))
        treefile2.close()
        treefile3 = open("./Graph/treeAllReqnode.txt", "w")
        treefile3.writelines("%d  %d  %d\n" %(len(self.NODE_DICT), len(self.LINK_LIST), self.treenum))
        treefile3.close()

        reqfile = open("request_h.txt", "r")
        reqline = reqfile.readline()
        destlist = []
        while reqline:
            reqline = reqline.split()
            reqperSlotcur = int(reqline[0])
            while reqperSlotcur > 0:
                reqline = reqfile.readline()
                reqline = reqline.split()
                src = int(reqline[0])
                destnum = int(reqline[4])
                for i in range(destnum):
                    destlist.append(int(reqline[5 + i])) 
                self.steinerTree(self.topo, src, destlist, self.treenum+3, self.treenum)
                destlist = []
                reqperSlotcur -= 1
            reqline = reqfile.readline()
        reqfile.close()
            

    def outputKshortestPath(self):
        self.numSubpath=0
        f = open("./Graph/linkonpath.txt", "w")
        fn = open("./Graph/nodeonpath.txt", "w")
        f.writelines("%d %d %d\n" % (self.NODENUM,self.NUMLINK,self.pathNum))
        pathcount = 0
        for src in self.NODE_DICT:
            for sink in self.NODE_DICT:
                if src != sink:
                    pathcount = 0
                    m_pathcount = [0 for i in range(self.cutoff+1)]
                    for path in nx.all_shortest_paths(self.topo, source=src, target=sink):
                        f.writelines("%d %d " % (src, sink))
                        pathcount += 1
                        m_pathcount[len(path)-1] += 1
                        self.numSubpath += 1
                        pre=0
                        fn.writelines("%d " % path[pre])
                        while pre < len(path)-1:
                            cur=pre+1
                            if path[pre] in self.LINK_DICT and path[cur] in self.LINK_DICT[path[pre]]:
                                f.writelines("%d " % self.LINK_DICT[path[pre]][path[cur]].id)
                                fn.writelines("%d " % path[cur])
                            else:
                                f.writelines("%d " % self.LINK_DICT[path[cur]][path[pre]].id)
                            pre=pre+1
                        f.writelines("\n")
                        fn.writelines("\n")
                        if pathcount >= self.pathNum:
                            break

                    if pathcount < self.pathNum:
                        for path in nx.all_simple_paths(self.topo, source=src, target=sink, cutoff = self.cutoff):
                            f.writelines("%d %d " % (src, sink))
                            pathcount += 1
                            m_pathcount[len(path)-1] += 1
                            self.numSubpath += 1
                            pre=0
                            fn.writelines("%d " % path[pre])
                            while pre < len(path)-1:
                                cur=pre+1
                                if path[pre] in self.LINK_DICT and path[cur] in self.LINK_DICT[path[pre]]:
                                    f.writelines("%d " % self.LINK_DICT[path[pre]][path[cur]].id)
                                    fn.writelines("%d " % path[cur])
                                else:
                                    f.writelines("%d " % self.LINK_DICT[path[cur]][path[pre]].id)
                                pre=pre+1
                            f.writelines("\n")
                            fn.writelines("\n")
                            if pathcount >= self.pathNum:
                                break
        f.close()
        fn.close()

if __name__ == "__main__":
    print "generating k paths..." 
    mgraph = CGraph()
    print "k=", mgraph.pathNum
    mgraph.outputKshortestPath()
    print "end path generation"
    #print mgraph.NODENUM
