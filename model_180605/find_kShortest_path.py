#!/usr/bin/python
# -*- coding: utf-8 -*-

#@author: Yijing Kong
#@create_time: 6 June,2018
#@email: yijingkong623@gmail.com

import xml.dom.minidom 
from Queue import PriorityQueue 
import xlwt as xlwt

'''
Graph类:
数据成员:
		无
函数成员:
		readGraphXmlFile():读取网络拓扑度xml文件
		readDataCenterXmlFile():读取每个数字代表的结点对应的数据中心的名称
'''
class Graph():
    def readGraphXmlFile(self, file):
        xmldoc = xml.dom.minidom.parse(file)

        Vertices = xmldoc.getElementsByTagName("Vertex");
        V = [];
        for vertex in Vertices:
            attr = vertex.attributes;
            vid = int(attr["vertexId"].value);
            V.append(vid);

        Edges = xmldoc.getElementsByTagName("Edge");
        E = [];
        for edge in Edges:            
            attr = edge.attributes;
            tail = int(attr["tail"].value);
            head = int(attr["head"].value);
            weight = int(attr["weighted"].value)
            E.append([tail, head, weight]);

        return (V, E);

    def readDataCenterXmlFile(self, file):
        xmldoc = xml.dom.minidom.parse(file)
     
        dataCenters = xmldoc.getElementsByTagName("DataCenter");
        D = [];
        for dataCenter in dataCenters:
            attr = dataCenter.attributes;
            dcid = str(attr["dataCenterId"].value);
            D.append(dcid);

        return D;

    class __Vertex:
        def __init__(self,vertexId,x,y,label):
            self.vertexId = vertexId

    class __Edge:
        def __init__(self,v1,v2,weight=0):
            self.v1 = v1

            self.weight = weight

        def __lt__(self,other):
        	return self.weight < other.weight 

'''
Dijkstra函数: 计算网络拓扑中任意两个结点之间的最短路径			
'''

def Dijkstra(graph,src):
    # 判断图是否为空，如果为空直接退出
    if graph is None:
        return None
    used_visit_list = [False for i in range(len(graph))]
    distance = {}
    for v in range(0, len(graph)):
        distance[v] = float('inf')

    path={src:{src:[]}}  # 记录源结点到每个结点的路径

    que = PriorityQueue()
    distance[src] = 0
    que.put((0, src, src))

    while not que.empty():
        nowdistance, nowId, preId = que.get()
        if used_visit_list[nowId]:
            continue
        if(nowId != src):
            path[src][nowId]=[i for i in path[src][preId]]
            path[src][nowId].append(preId)
        used_visit_list[nowId] = True
        for v in range(0, len(graph)):
            if (not used_visit_list[v]) and distance[nowId] + graph[nowId][v] < distance[v]:
                distance[v] = distance[nowId] + graph[nowId][v]
                que.put((distance[v], v, nowId))
    for v in path[src]:
        if used_visit_list[v]:
            path[src][v].append(v)
    return distance,path

# 邻接矩阵赋值
def set_node_map(node_map, node, node_list):
    for x, y, val in node_list:
        node_map[x][y] =  val
    for i in range(len(node_map)):
    	node_map[i][i] = 0

def write_to_excel(node_map):
    book = xlwt.Workbook(encoding = 'utf-8', style_compression = 0)
    sheet = book.add_sheet('adjMatrix',cell_overwrite_ok = True)
    for i in range(1,14):
        for j in range(1,14):
            sheet.write(i,j,str(node_map[i-1][j-1]))

    book.save('/Users/peggy/Documents/研究生阶段事宜/MOSEK/Document/邻接矩阵.xlsx')

def main():
	# 从xml文件中读图
    graph = Graph();
    V = []
    E = []
    D = []
    (V, E) = graph.readGraphXmlFile("graph.xml");
    # D = graph.readDataCenterXmlFile("dataCenter.xml")

    node = V;  
    # 带权重的边表  
    node_list = E;
    # 每个结点对应的data center的编号
    # addressString = D;   
    
    # 13*13的邻接矩阵初始化，矩阵中的每个元素都为0 
    infinite = float('inf')
    node_map = [[infinite for val in range(len(node))] for val in range(len(node))];    
    # 邻接矩阵  
    set_node_map(node_map, node, node_list);
    write_to_excel(node_map)
    
    for i in range(0,13):
        from_node = node[i];
        distance,path = Dijkstra(node_map, from_node)
        print distance 
    #print path
    
	
    # print(dijkstrapath.pathString(addressString)); 

if __name__ == '__main__':
	main()