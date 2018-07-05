#!/usr/bin/python
# -*- coding: utf-8 -*-

import xml.dom.minidom 

# class Graph():
#     def readCostXmlFile(self, file):
#         xmldoc = xml.dom.minidom.parse(file)

#         Timeslots = xmldoc.getElementsByTagName("Timeslot")
#         T = []
#         for timeslot in Timeslots:
#             attr = timeslot.attributes
#             tid = int(attr["timeslotId"].value)
#             T.append(tid)

#         Edges = xmldoc.getElementsByTagName("Edge")
#         E = []
#         for edge in Edges:            
#             attr = edge.attributes;
#             number = int(attr["number"].value)
#             weight = int(attr["weighted"].value)
#             E.append([number, weight])

#         return (T, E)

# def set_node_map(node_map, time, edge_list):
#     for t in time:
#         for edge,val in edge_list:
#             node_map[edge][t] = val

# def main():
#     graph = Graph();
#     T = []
#     E = []
#     (T, E) = graph.readCostXmlFile("costOfEdge_Time.xml");

#     time = T;  
#     # 带权重的边表  
#     edge_list = E;
#     # print edge_list
#     # 每个结点对应的data center的编号
#     # addressString = D;   
    
#     # 13*13的邻接矩阵初始化，矩阵中的每个元素都为0 
#     node_map = [[0 for val in range(len(time))] for val in range(len(edge_list))];    
#     # 邻接矩阵  
#     set_node_map(node_map, time, edge_list);
#     print node_map

def main():
    m = [[1,2,3],[1,2,3],[1,2,3]]
    list_1 = [0,2]
    list_2 = [0,2]
    for i in list_1:
        for j in list_2:
            print m[i][j]

if __name__ == '__main__':
    main()