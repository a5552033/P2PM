#!/usr/bin/env python
# -*- coding:UTF-8 -*-
import networkx as nx

if __name__ == '__main__':
    # 清空txt文件中原来的数值
    fnode = open("nodes.txt", "w")
    fnode.close()
    fedge = open("edges.txt", "w")
    fedge.close()

    # 从gml文件里读取数据
    H = nx.read_gml('graph.gml', label='id')
    fnode = open("nodes.txt", "a")
    fedge = open("edges.txt", "a")

    # nodes.txt
    for n in range(len(H.nodes())):
        fnode.writelines("%d\n" % (int((list(H.nodes))[n])+1))

    # edges.txt
    print(H.edges())
    i = 0
    for s, d in (H.edges()):
        i += 1
        if (s == 80 and d == 81) or (s == 42 and d == 143):
            fedge.writelines("%d\t" "%d\t" "%d\t" "%d" % (s+1, d+1, 2, i))
            fedge.writelines("\n")
        else:
            fedge.writelines("%d\t" "%d\t" "%d\t" "%d" % (s + 1, d + 1, 1, i))
            fedge.writelines("\n")

    fnode.close()
    fedge.close()