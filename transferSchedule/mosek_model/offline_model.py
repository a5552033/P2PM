#!/usr/bin/env python
# encoding: utf-8
from mosek.fusion import *

def offlineMIPmodel(reqNum, nodeNum, slotNum, pathNum, linkNum, srcOfReq, dstOfReq, M_expr, fsizeOfAllReq,
                    timeOfSurvival, linkonpath, linktimecap):
    #print "offline model..."
    #print "reqNum, nodeNum, slotNum, pathNum, linkNum, fsize, M_expr",reqNum, nodeNum, slotNum, pathNum, linkNum,fsizeOfAllReq,M_expr
    #print "srcOfReq", srcOfReq
    #print "dstOfReq", dstOfReq
    #print "linkonpath", linkonpath
    #print "timeOfSurvival", timeOfSurvival
    #print "linktimecap", linktimecap
    with Model("offlineModel") as M:
        x = M.variable('X', [reqNum, slotNum*nodeNum, nodeNum], Domain.greaterThan(0.0))
        y = M.variable('Y', [reqNum*nodeNum*nodeNum, pathNum, slotNum], Domain.greaterThan(0.0))
        z = M.variable('z', [reqNum, nodeNum, nodeNum], Domain.binary())  # whether src is the data source of dst
        h = M.variable('h', [reqNum, nodeNum, slotNum], Domain.binary())  # whether src can be a data source in time t
        w = M.variable('w', [reqNum, nodeNum], Domain.binary())  # whether dst is finished before deadline
        r = M.variable('r', reqNum, Domain.binary())
        g = M.variable('g', 1, Domain.binary())

        M.objective("accepted_req", ObjectiveSense.Maximize, Expr.sum(r))
        #M.objective("accepted_req", ObjectiveSense.Maximize, Expr.sum(w))

        # constraints on size
        for i in range(reqNum):
            #for u in range(nodeNum):
                #expr_sub = 1 - srcOfReq[i][u] - dstOfReq[i][u]
            for t in range(slotNum):
                for u in range(nodeNum):
                    if srcOfReq[i][u] == 1:
                        # 对于每个request来说，其初始源数据中心始终可以作为任意数据中心的数据传输源
                        M.constraint((Expr.sub(h.index(i, u, t), timeOfSurvival[i][t])), Domain.equalsTo(0.0))
                    if dstOfReq[i][u] == 1:
                        # 得到每一个request的目的节点
                        M.constraint((Expr.sub(h.index(i, u, t), timeOfSurvival[i][t])), Domain.lessThan(0.0))
                    if srcOfReq[i][u]!=1 and dstOfReq[i][u]!=1:
                        # 在某一个request的存活期内，设置不属于该request的数据中心不能作为传输源
                        M.constraint(h.index(i, u, t), Domain.equalsTo(0.0))

        # constraint on maybe source site
        for i in range(reqNum):
            for v in range(nodeNum):
                if dstOfReq[i][v] == 1:
                    expr_sum = Expr.sum(g)
                    for t in range(slotNum):
                        for tt in range(t):
                            for u in range(nodeNum):
                                # print(x.index(i, v*nodeNum+u, tt))
                                expr_sum = Expr.add(expr_sum, x.index(i, tt*nodeNum+u, v))
                        expr_sum = Expr.sub(expr_sum, Expr.sum(g))
                        M.constraint(
                            Expr.sub(expr_sum, Expr.mul(fsizeOfAllReq[i], h.index(i, v, t))), Domain.greaterThan(0.0))

        # 目的数据中心从唯一源数据中心接收数据量不能超过fsize
        for i in range(reqNum):
            for t in range(slotNum):
                for u in range(nodeNum):
                    for v in range(nodeNum):
                        # expr_mul = Expr.mul(h.index(i, u, t), A[i][t][u][v])
                        M.constraint(Expr.sub(x.index(i, t*nodeNum+u, v), Expr.mul(fsizeOfAllReq[i], h.index(i, u, t))),
                                    Domain.lessThan(0.0))
                        # 某一目的数据中心从唯一确定的源数据中心接收到的数据不能超过fsize
                        M.constraint(
                            Expr.sub(x.index(i, t * nodeNum + u, v), Expr.mul(fsizeOfAllReq[i], z.index(i, u, v))),
                            Domain.lessThan(0.0))

        # constraint on z, only one source of each destination
        M.constraint(Expr.sum(z, 1), Domain.equalsTo(1.0))

        # allocating available bandwidth resources
        for t in range(slotNum):
            for i in range(reqNum):
                for u in range(nodeNum):
                    for v in range(nodeNum):
                        expr_sumy = Expr.sum(g)
                        for p in range(pathNum):
                            expr_sumy = Expr.add(expr_sumy, y.index((i*nodeNum*nodeNum+u*nodeNum+v), p, t))
                        expr_sumy = Expr.sub(expr_sumy, Expr.sum(g))
                        M.constraint(Expr.sub(expr_sumy, x.index(i, t*nodeNum+u, v)), Domain.equalsTo(0.))
            for e in range(linkNum):
                linkload_et = Expr.sum(g)
                for i in range(reqNum):
                    for u in range(nodeNum):
                        for v in range(nodeNum):
                            for p in range(pathNum):
                                linkload_et = Expr.add(linkload_et, Expr.mul(linkonpath[e][u][v][p], y.index((i*nodeNum*nodeNum+u*nodeNum+v), p, t)))
                linkload_et = Expr.sub(linkload_et, Expr.sum(g))
                linkload_et = Expr.sub(linkload_et, linktimecap[e][t])
                M.constraint(linkload_et, Domain.lessThan(0.0))

        for i in range(reqNum):
            for v in range(nodeNum):
                if dstOfReq[i][v] == 1: 
                    expr_d = Expr.sum(g)
                    for t in range(slotNum):
                        for u in range(nodeNum):
                            expr_d = Expr.add(expr_d, x.index(i, t*nodeNum+u, v))
                    expr_d = Expr.sub(expr_d, Expr.sum(g))
                    M.constraint(Expr.sub(expr_d, Expr.mul(fsizeOfAllReq[i], w.index(i, v))), Domain.greaterThan(0.))
                if dstOfReq[i][v] == 0:
                    M.constraint(Expr.sub(w.index(i, v), dstOfReq[i][v]), Domain.lessThan(0.0))
      
        for i in range(reqNum):
            expr_sumw = Expr.sum(g)
            for v in range(nodeNum):
                expr_sumw = Expr.add(expr_sumw, w.index(i, v))
            expr_sumw = Expr.sub(expr_sumw, Expr.sum(g))
            M.constraint(Expr.sub(expr_sumw, Expr.mul(r.index(i), M_expr[i])), Domain.equalsTo(0.0))
        

        M.solve()
        res_obj = 0
        res_r = 0
        res_w = 0
        res_y = 0
        res_z = 0
        res_x = 0
        res_h = 0

        res_feasible = False
        acceptable = [
            ProblemStatus.PrimalAndDualFeasible,
            ProblemStatus.PrimalFeasible,
            ProblemStatus.DualFeasible]

        if M.getProblemStatus(SolutionType.Default) in acceptable:
            # print "feasible"
            res_feasible = True

        if res_feasible == False:
            # print "nonfeasible: max_throughput"
            # print M.getPrimalSolutionStatus()
            # print M.getProblemStatus(SolutionType.Default)
            return res_r, res_y, res_feasible

        res_r = r.level()
        res_w = w.level()
        res_z = z.level()
        res_y = y.level()
        res_h = h.level()
        #print "res_w", res_w
        #print "res_r", res_r

        for i in range(reqNum):
            res_obj += res_r[i]
        #print "res_obj", res_obj
        return res_obj, res_y, res_feasible
