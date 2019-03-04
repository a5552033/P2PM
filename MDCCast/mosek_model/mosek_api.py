#!/usr/bin/env python
# encoding: utf-8

from mosek.fusion import *


# a DC can be the data sender other receivers only if it already has received a full copy of data
# the objective is maximize the number of completed receivers before deadline
def steinertreeLPmodel(reqnum, treenum, linknum, rSlotNum, fsize, linkontree, linktimecap, W):
    # print "\n solve problem: pathnum, linkum, destnum, srcnum, slotnum ", pathnum, linknum, destnum, srcnum, slotnum

    with Model("lpmodel") as M:
        chi = M.variable('ka', 1, Domain.greaterThan(0.0))
        x = M.variable('X', [reqnum, treenum], Domain.greaterThan(0.))

        temp_sum = 0
        mu = 0.01
        for i in range(reqnum):
            for t in range(treenum):
                temp_sum = Expr.add(temp_sum, Expr.mul(W[i][t], x.index(i, t)))
        obj = Expr.sub(chi, Expr.mul(mu, temp_sum))

        M.objective("multicast_tree", ObjectiveSense.Maximize, obj)

        for i in range(reqnum):
            temp_sum_xd2 = 0
            for t in range(treenum):
                temp_sum_xd2 = Expr.add(temp_sum_xd2, x.index(i, t))
            M.constraint(Expr.sub(chi, temp_sum_xd2), Domain.lessThan(0.0))
            M.constraint(Expr.sub(Expr.mul(rSlotNum[i], temp_sum_xd2), fsize[i]), Domain.greaterThan(0.0))

        for e in range(linknum):
            temp_sum_x = 0
            for i in range(reqnum):
                for t in range(treenum):
                    temp_sum_x = Expr.add(temp_sum_x, Expr.mul(linkontree[i][t][e], x.index(i, t)))
            # print(type(temp_sum_x), temp_sum_x, linknum, reqnum)
            M.constraint(Expr.sub(temp_sum_x, linktimecap[e],), Domain.lessThan(0.))

        M.solve()
        # res_z = 0
        res_x = 0
        # res_h = 0
        res_feasible = False
        acceptable = [
            ProblemStatus.PrimalAndDualFeasible,
            ProblemStatus.PrimalFeasible,
            ProblemStatus.DualFeasible]

        if M.getProblemStatus(SolutionType.Default) in acceptable:
            # print "feasible"
            res_feasible = True

        if not res_feasible:
            # print "nonfeasible: flexible source!"
            # print M.getPrimalSolutionStatus()
            # print M.getProblemStatus(SolutionType.Default)
            return res_x, res_feasible

        res_x = x.level()
        # res_z = z.level()
        # res_h = h.level()
        # z_sum = [0.0 for d in range(destnum)]
        return res_x, res_feasible




