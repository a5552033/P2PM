#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from mosek.fusion import *


def LPmodel(trafficnum, pathnum, linknum, src, dst, fsize, linkonpath, linkcapacity, plen):
    with Model("LPModel") as M:
        x = M.variable('X', [trafficnum, pathnum], Domain.greaterThan(0.0))
        y = M.variable('Y', linknum, Domain.greaterThan(0.0))
        u = M.variable('U', [trafficnum, pathnum], Domain.binary())
        # z = M.variable('Z', 1, )

        M.objective("min-linkcost", ObjectiveSense.Minimize, Expr.sum(y))

        for k in range(trafficnum):
            for p in range(pathnum):
                M.constraint(Expr.sub(x.index(k, p), Expr.mul(u.index(k, p), fsize[k])), Domain.equalsTo(0.0))

        for k in range(trafficnum):
            M.constraint(Expr.sum(u, 1), Domain.equalsTo(1.0))

        for e in range(linknum):
            expr_sumx = 0
            for k in range(trafficnum):
                for p in range(pathnum):
                    expr_sumx = Expr.add(expr_sumx, Expr.mul(x.index(k, p), linkonpath[src[k]][dst[k]][p][e]))
                    M.constraint(Expr.sub(x.index(k, p), (fsize[k]*plen[src[k]][dst[k]][p])), Domain.lessThan(0.0))
            M.constraint(Expr.sub(expr_sumx, y.index(e)), Domain.equalsTo(0.0))

        for e in range(linknum):
            M.constraint(Expr.sub(y.index(e), linkcapacity[e]), Domain.lessThan(0.0))

        M.solve()

        # res_feasible = False
        routing = [0 for k in range(trafficnum)]

        # acceptable = [
        #     ProblemStatus.PrimalAndDualFeasible,
        #     ProblemStatus.PrimalFeasible,
        #     ProblemStatus.DualFeasible]
        #
        # if M.getProblemStatus(SolutionType.Default) in acceptable:
        #     # print "feasible"
        #     res_feasible = True
        #
        # if not res_feasible:
        #     # print "nonfeasible: flexible source!"
        #     # print M.getPrimalSolutionStatus()
        #     # print M.getProblemStatus(SolutionType.Default)
        #     return routing, res_feasible

        res_x = x.level()
        print("res_x", res_x)

        k = 0
        for i in range(trafficnum*pathnum):
            if res_x[i] > 0:
                routing[k] = i % pathnum
                k += 1
            else: continue

        return routing
