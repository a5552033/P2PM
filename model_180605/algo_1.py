#!/usr/bin/python
# -*- coding: utf-8 -*-

#@author: Yijing Kong
#@create_time: 7 June,2018
#@email: yijingkong623@gmail.com

'''
I would code algorithms_1 as follows:
1) input the graph(simple undirected graph);
2) find k-path between s and {d1,d2,d3,...,dm};
3) define varialbe and constant;
4) call function in modek and build optimization model;
5) output the intermediate value
'''

import sys
import mosek
from mosek.fusion import *

'''
Request类
数据成员:
		source: t_1时刻的transfer source
		destination: List数据结构，需要传输数据的目的结点的集合
		to_be_transferred_data_size: 从源结点到目的结点传输数据的总容量
		start_time: Request的到达时刻
		deadline: deadline,Request的结束时刻
		path_between_u_v: 字典数据结构，任意两个datacenter之间的最短路
		residual_link_bandwidth_e: list数据结构，t_1~t_2这个时间段内任意一条链路剩余带宽
成员函数:
		algo_1(): 实现algorithm_1
		Optimization(): mosek构建优化模型，目的是判断reques是否可被接受

'''
class DecisionOfRequest(object):
	def __init__(self, src, dst, f, t_1, t_2, p_u_v, interval):
		self.source = src
		self.destination = dst
		self.to_be_transferred_data_size = f
		self.start_time = t_1
		self.deadline = t_2
		self.path_between_u_v = p_u_v
		# self.residual_link_bandwidth_e = c_e_t
		self.time_slot = interval

	def algo_1(self):
		return self.Optimization()

	def Optimization(self):
	 	 # Create coefficient matrix

	 	 # 优化目标中对w_d的累加就是(c^T)*(vector(w_d))
	 	c = [1.0, 1.0, 1.0, 1.0 ,1.0, 1.0, 1.0, 1.0 ,1.0, 1.0, 1.0, 1.0]
	 	range_k = 13
	 	numberOfShortestPath = 3
	 	sourceDataCenter = [0,4,7,9,10]

	 	 # Create a model with the name 'algo_1'
	 	with Model("algo_1") as M:
	 	 	# Create variable 'w_d' of length m, m暂且等于12, w_d的取值{0, 1}.
	 	 	# 与优化目标相关的变量
	 		w_d = M.variable('w_d', 12, Domain.binary())
 	 	
	 	 	# 如果h_k_t是一个range_k * range_t的数组，那我就没办法保证数组下标从2开始了
	 		h_k_t = M.variable('datacenterAsTS', [range_k, 10], Domain.binary())
	 	 	x_k_d_l = M.variable('dataSizeAtTimet', [range_k, range_k, 10], Domain.greaterThan(0.))
	 	 	z_k_d = M.variable('kAsDOfTS', [range_k, range_k], Domain.binary())
	 	 	y_k_d_p_t = M.variable('allocatedVolumnAtPathpAtTimet', [range_k, range_k,10], Domain.greaterThan(0.))
	 	 	# 14是网络拓扑图中的边数
	 	 	# 变量i_p是为了表示编号为k的某一条最短路径是否属于此次request的允许路径，是为1，不是为0
	 	 	i_p = M.variable('edgeBelongstoP', [range_k, range_k, numberOfShortestPath], Domain.binary())

	 	 	# Create the constraints
	 	 	for t in (self.start_time,self.deadline + 1):
	 	 		M.constraint(h_k_t.index([0,t]), Domain.equalsTo(1.))
	 	 	
	 	 	
	 	 	for t in range(self.start_time,self.deadline + 1):
	 	 		for d in dst:
		 	 		for l_1 in range(self.start_time,self.start_time + t - 1):
				 	 	for k in sourceDataCenter:
				 	 		if k != d:
				 	 			M.constraint(Expr.sub(Expr.sum(x_k_d_l.index([k, d, l_1])), Expr.mul((self.to_be_transferred_data_size),h_k_t.index([d,t]))),  Domain.greaterThan(0.))
				 	 		else:
				 	 			continue


		 	for t in range(self.start_time,self.deadline + 1):
		 		for d in dst:
			 		for k in sourceDataCenter:
			 			if k != d:
			 				M.constraint(Expr.sub(x_k_d_l.index([k, d, t]),Expr.mul(self.to_be_transferred_data_size,h_k_t.index([k,t]))), Domain.lessThan(0.))
			 			else:
			 				continue

		 	for k in sourceDataCenter:
		 		for d in dst:
		 			if k != d:
		 				M.constraint(Expr.sum(z_k_d.index([k,d])), Domain.equalsTo(1.))
		 			else:
		 				continue

		 	for t in range(self.start_time,self.deadline + 1):
		 		for d in dst:
		 			for k in sourceDataCenter:
		 				if k != d:
		 					M.constraint(Expr.sub(x_k_d_l.index([k, d, t]),Expr.mul(self.to_be_transferred_data_size, z_k_d.index([k,d]))), Domain.lessThan(0.))
		 				else:
		 					continue

		 	M.constraint(i_p.pick(self.path_between_u_v), Domain.equalsTo(1.0))
		 	
		 	for t in range(self.start_time,self.deadline + 1):
		 		for k in sourceDataCenter:
		 			for d in dst:
		 				if k != d:
		 					for p in range(numberOfShortestPath):
								M.constraint(Expr.sum(Expr.mul(Expr.mul(self.time_slot,y_k_d_p_t.index([k,d,t])),i_p.index([k,d,p]))),Domain.greaterThan(0.))

			# 最后一个约束条件

			for d in dst:
				for l_2 in range(self.start_time,self.deadline + 1):
					for k in sourceDataCenter:
						M.constraint(Expr.sub(Expr.sum(x_k_d_l.index(k,d,l_2)),Expr.mul(self.to_be_transferred_data_size,w_d.index(d))), Domain.lessThan(0.))

	 	 	# Set the objective function to (c^T * w_d)
	 	 	M.objective('obj', ObjectiveSense.Maximize, Expr.dot(c,w_d))

	 	 	M.solve()

	 	 	# 返回w_d的累加和
	 	 	_w_d = 0
	 	 	for d in dst:
	 	 		if w_d.index(d).level() > 0.5:
	 	 			_w_d = _w_d + 1
	 	 	return _w_d

if __name__ == '__main__':
	# 最开始的传输源
	src = 6
	# 该request的目的datacenters
	dst = [4, 7, 9, 10]
	# 单位是MB
	data_size = 20480
	# 表示该请求到达的时间在第2时隙，在第6时隙截止
	t_1 = 2
	t_2 = 6
	
	'''
	变量p_u_v的描述：
	[s,d,k]:s表示路(s,d)的源结点，d表示(s,d)的目的结点，k表示任意不同两个结点u，v之间k条最短路径，哪条路径可以在本次request中使用 k = {0,1,2,3....}
	先暂时认为任意两不同结点之间只有一条最短路，调用函数求出任意两点间的最短路径，因为不会A*算法
	'''
	p_u_v = [[0, 1, 0],[0, 4, 0],[0, 5, 0],[0, 7, 0],[0, 10, 0],[0, 11, 0],[0, 12, 0],
			 [1, 4, 0],[1, 5, 0],[1, 7, 0],
			 [2, 0, 0],[2, 1, 0],[2, 3, 0],[2, 4, 0],[2, 5, 0],[2, 6, 0],[2, 7, 0],[2, 8, 0],[2, 9, 0],[2, 10, 0],[2, 11, 0],[2, 12, 0],
			 [3, 0, 0],[3, 1, 0],[3, 4, 0],[3, 5, 0],[3, 7, 0],[3, 9, 0],[3, 10, 0],[3, 11, 0],[3, 12, 0],
			 [4, 5, 0],[4, 7, 0],
			 [5, 7, 0],
			 [9, 5, 0],[9, 7, 0],[9, 10, 0],[9, 11, 0],[9, 12, 0],
			 [10,5, 0],[10,7, 0],[10,11, 0],[10,12, 0],
			 [11,5, 0],[11,7, 0],[11,12, 0],
			 [12,5, 0],[12,7, 0]]
	# i_e_p = 
	# # 边的权重,可从xml文件中读取
	# c_e_t = 

	#r = DecisionOfRequest(src, dst, data_size, t_1, t_2, p_u_v, c_e_t, 5*60)
	r = DecisionOfRequest(src, dst, data_size, t_1, t_2, p_u_v, 5*60)
	# 最后肯定是要返回一些数值的，比如：request是否被接受，如果被接受，则在t_1~t_2时刻分配的链路资源
	numberOfDatacenters = r.algo_1()

	print numberOfDatacenters