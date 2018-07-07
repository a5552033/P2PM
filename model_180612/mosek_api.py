# @author: Yijing Kong
# @create_time: 12 June,2018
# @email: yijingkong623@gmail.com

'''
This python file is coded for using the mosek to optimize the model
There are two functions:
                        flexiblesrcMIPmodel(): the source data centers are flexible
                        fixsrcMIPmodel(): the source data center is fixed
They have same inputs and outputs
'''

# !/usr/bin/python
# coding: utf-8

from mosek.fusion import *


def flexiblesrcMIPmodel(pathnum, linknum, destnum, slotnum, fsize, linkonpath, linktimecap):
    srcnum = destnum + 1
    # print "\n solve problem: pathnum, linkum, destnum, srcnum, slotnum ", pathnum, linknum, destnum, srcnum, slotnum

    with Model("mipmodel") as M:
        x = M.variable('X', [srcnum, destnum, slotnum], Domain.greaterThan(0.0))
        # y = M.variable('Y', [srcnum, destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        y = M.variable('Y', [srcnum * destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        z = M.variable('z', [srcnum, destnum], Domain.inRange(0., 1.))  # whether src is the data source of dest
        h = M.variable('h', [srcnum, slotnum], Domain.binary())  # whether src can be a data source in time t
        w = M.variable('w', destnum, Domain.binary())  # whether dest is finished before deadline
        g = M.variable('g', 1, Domain.binary())

        M.objective("completed_dest", ObjectiveSense.Maximize, Expr.sum(w))

        # constraints on size
        for t in range(slotnum):
            M.constraint(h.index(0, t), Domain.equalsTo(1.))  # the source site s can be source over all the time
        for s in range(srcnum - 1):
            M.constraint(h.index(s + 1, 0),
                         Domain.equalsTo(0.))  # all the destination cannot be the data source at time 0

        # constraint on maybe source site
        for d in range(destnum):
            for t in range(slotnum):
                expr_sumd = Expr.sum(g)
                # M.constraint(x.index(d+1,d,t), Domain.equalsTo(0.0)) #each destination can never be the data source of itself
                for tt in range(t):
                    for s in range(srcnum):
                        expr_sumd = Expr.add(expr_sumd, x.index(s, d, tt))
                expr_sumd = Expr.sub(expr_sumd, Expr.sum(g))
                M.constraint(Expr.sub(expr_sumd, Expr.mul(fsize, h.index(d + 1, t))), Domain.greaterThan(0.))

        # constraint on z, only one source of each destination
        M.constraint(Expr.sum(z, 0), Domain.equalsTo(1.))

        # constraint on z and x ?
        for d in range(destnum):
            M.constraint(z.index(d + 1, 0), Domain.equalsTo(0.))
        M.constraint(Expr.sub(Expr.sum(x, 2), Expr.mul(fsize, z)), Domain.lessThan(0.))

        for t in range(slotnum):
            for m in range(srcnum):
                for d in range(destnum):
                    M.constraint(Expr.sub(x.index(m, d, t), Expr.mul(fsize, h.index(m, t))), Domain.lessThan(0.))
                    expr_sumy = Expr.sum(g)
                    for p in range(pathnum):
                        expr_sumy = Expr.add(expr_sumy, y.index(m * destnum + d, p, t))
                    expr_sumy = Expr.sub(expr_sumy, Expr.sum(g))
                    M.constraint(Expr.sub(expr_sumy, x.index(m, d, t)), Domain.equalsTo(0.))
                    # M.constraint( Expr.sub( Expr.sum(y.slice([m*destnum+d,0,t],[m*destnum+d,pathnum, t])), x.index(m,d,t)), Domain.equalsTo(0.) )
            for e in range(linknum):
                linkload_et = Expr.sum(g)
                for s in range(srcnum):
                    for d in range(destnum):
                        for p in range(pathnum):
                            linkload_et = Expr.add(linkload_et,
                                                   Expr.mul(linkonpath[e][s][d][p], y.index(s * destnum + d, p, t)))
                linkload_et = Expr.sub(linkload_et, Expr.sum(g))
                linkload_et = Expr.sub(linkload_et, linktimecap[e][t])
                M.constraint(linkload_et, Domain.lessThan(0.))

        for d in range(destnum):
            expr_d = Expr.sum(g)
            for m in range(srcnum):
                for t in range(slotnum):
                    expr_d = Expr.add(expr_d, x.index(m, d, t))
            expr_d = Expr.sub(expr_d, Expr.sum(g))
            M.constraint(Expr.sub(expr_d, Expr.mul(fsize, w.index(d))), Domain.greaterThan(0.))
            M.constraint(expr_d, Domain.lessThan(fsize))  # ?

        M.solve()
        res_obj = 0
        res_w = 0
        res_y = 0
        res_z = 0
        res_x = 0
        res_h = 0
        res_feasible = False
        acceptable = [ProblemStatus.PrimalAndDualFeasible,
                      ProblemStatus.PrimalFeasible,
                      ProblemStatus.DualFeasible]

        if M.getProblemStatus(SolutionType.Default) in acceptable:
            res_feasible = True

        if not res_feasible:
            return res_obj, res_x, res_w, res_y, res_feasible

        res_w = w.level()
        res_z = z.level()
        res_y = y.level()
        res_h = h.level()
        for d in range(destnum):
            res_obj += res_w[d]
        return res_obj, res_x, res_w, res_y, res_feasible


# the orignal sender is considered as the data source of all the recievers
def fixsrcMIPmodel(pathnum, linknum, destnum, slotnum, fsize, linkonpath, linktimecap):
    with Model("mipmodel") as M:
        x = M.variable('X', [destnum, slotnum], Domain.greaterThan(0.0))
        y = M.variable('Y', [destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        w = M.variable('w', destnum, Domain.inRange(0., 1.))
        g = M.variable('g', 1, Domain.binary())  # fuzhu bianliang

        obj_expr = Expr.sum(w)
        M.objective("completeddest", ObjectiveSense.Maximize, obj_expr)

        M.constraint(Expr.sub(Expr.sum(x, 1), Expr.mul(fsize, w)), Domain.equalsTo(0.))
        M.constraint(Expr.sub(Expr.sum(y, 1), x), Domain.equalsTo(0.))

        for e in range(linknum):
            for t in range(slotnum):
                linkload_et = Expr.sum(g)
                for d in range(destnum):
                    for p in range(pathnum):
                        linkload_et = Expr.add(linkload_et, Expr.mul(linkonpath[e][d][p], y.index(d, p, t)))
                linkload_et = Expr.sub(linkload_et, Expr.sum(g))
                linkload_et = Expr.sub(linktimecap[e][t], linkload_et)
                M.constraint(linkload_et, Domain.greaterThan(0.0))

        M.solve()
        res_obj = 0
        res_w = 0
        res_y = 0
        res_x = 0

        res_feasible = False
        acceptable = [ProblemStatus.PrimalAndDualFeasible,
                      ProblemStatus.PrimalFeasible,
                      ProblemStatus.DualFeasible]

        if M.getProblemStatus(SolutionType.Default) in acceptable:
            res_feasible = True

        if not res_feasible:
            return res_obj, res_x, res_w, res_y, res_feasible

        res_w = w.level()
        res_x = x.level()
        res_y = y.level()
        for d in range(destnum):
            res_obj += res_w[d]

        return res_obj, res_x, res_w, res_y, res_feasible
