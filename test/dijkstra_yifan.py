#!/usr/bin/python
# -*- coding: utf-8 -*-

# dijkstra算法实现，有向图和路由的源点作为函数的输入，最短路径最为输出
def dijkstra(graph,src):
    # 判断图是否为空，如果为空直接退出
    from Queue import PriorityQueue
    if graph is None:
        return None
    visted = [False for i in range(len(graph))]
    dist = {}
    for v in range(0, len(graph)):
        dist[v] = 10000

    path={src:{src:[]}}  # 记录源节点到每个节点的路径

    que = PriorityQueue()
    dist[src] = 0
    que.put((0, src, src))

    while not que.empty():
        nowDist, nowId, preId = que.get()
        if visted[nowId]:
            continue
        if(nowId != src):
            path[src][nowId]=[i for i in path[src][preId]]
            path[src][nowId].append(preId)
        visted[nowId] = True
        for v in range(0, len(graph)):
            if (not visted[v]) and dist[nowId] + graph[nowId][v] < dist[v]:
                dist[v] = dist[nowId] + graph[nowId][v]
                que.put((dist[v], v, nowId))
    for v in path[src]:
        if visted[v]:
            path[src][v].append(v)
    return dist,path

if __name__ == '__main__':
    graph_list = [[0, 200, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 200, 10000, 10000], [10000, 0, 10000, 10000, 300, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [10000, 10000, 0, 150, 10000, 10000, 200, 10000, 150, 10000, 10000, 10000, 10000], [300, 10000, 10000, 0, 10000, 10000, 10000, 10000, 10000, 300, 10000, 10000, 10000], [10000, 10000, 10000, 10000, 0, 200, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [10000, 10000, 10000, 10000, 10000, 0, 10000, 200, 10000, 10000, 10000, 10000, 10000], [10000, 10000, 10000, 10000, 10000, 10000, 0, 10000, 10000, 10000, 10000, 10000, 10000], [10000, 10000, 10000, 10000, 10000, 10000, 10000, 0, 10000, 10000, 10000, 10000, 10000], [10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 0, 10000, 10000, 10000, 10000], [10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 0, 150, 10000, 10000], [10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 0, 100, 10000], [10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 0, 300], [10000, 10000, 10000, 10000, 10000, 200, 10000, 10000, 10000, 10000, 10000, 10000, 0]]

    distance,path= dijkstra(graph_list, 0)  # 查找从源点0开始带其他节点的最短路径
    print(distance,path)
