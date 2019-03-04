#!/usr/bin/env python
# encoding: utf-8

from mosek.fusion import *


# a DC can be the data sender other receivers only if it already has received a full copy of data
# the objective is maximize the number of completed receivers before deadline
def flexiblesrcMIPmodel(pathnum, linknum, destnum, slotnum, fsize, linkonpath, linktimecap, plen):
    srcnum = destnum + 1
    # print "\n solve problem: pathnum, linkum, destnum, srcnum, slotnum ", pathnum, linknum, destnum, srcnum, slotnum

    with Model("mipmodel") as M:
        x = M.variable('X', [srcnum, destnum, slotnum], Domain.greaterThan(0.0))
        # y = M.variable('Y', [srcnum,ss destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        y = M.variable('Y', [srcnum * destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        z = M.variable('z', [srcnum, destnum], Domain.binary())  # whether src is the data source of dest
        h = M.variable('h', [srcnum, slotnum], Domain.binary())  # whether src can be a data source in time t
        w = M.variable('w', destnum, Domain.binary())  # whether dest is finished before deadline

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
                expr_sumd = 0
                for tt in range(t):
                    for s in range(srcnum):
                        expr_sumd = Expr.add(expr_sumd, x.index(s, d, tt))
                M.constraint(Expr.sub(expr_sumd, Expr.mul(fsize, h.index(d + 1, t))), Domain.greaterThan(0.))

        # constraint on z, only one source of each destination
        M.constraint(Expr.sum(z, 0), Domain.equalsTo(1.))
        # multiple senders of a receiver
        # M.constraint(Expr.sum(z,0), Domain.lessThan(srcUpperBound))

        # constraint on z and x
        for d in range(destnum):
            M.constraint(z.index(d + 1, d), Domain.equalsTo(0.))
        M.constraint(Expr.sub(Expr.sum(x, 2), Expr.mul(fsize, z)), Domain.lessThan(0.))

        for t in range(slotnum):
            for m in range(srcnum):
                for d in range(destnum):
                    M.constraint(Expr.sub(x.index(m, d, t), Expr.mul(fsize, h.index(m, t))), Domain.lessThan(0.))
                    expr_sumy = 0
                    for p in range(pathnum):
                        expr_sumy = Expr.add(expr_sumy, y.index(m * destnum + d, p, t))
                        M.constraint(Expr.sub(y.index(m * destnum + d, p, t), fsize * plen[m][d][p]),
                                     Domain.lessThan(0.0))
                    M.constraint(Expr.sub(expr_sumy, x.index(m, d, t)), Domain.equalsTo(0.))
                    # M.constraint( Expr.sub( Expr.sum(y.slice([m*destnum+d,0,t],[m*destnum+d,pathnum, t])), x.index(m,d,t)), Domain.equalsTo(0.) )
            for e in range(linknum):
                linkload_et = 0
                for s in range(srcnum):
                    for d in range(destnum):
                        for p in range(pathnum):
                            linkload_et = Expr.add(linkload_et,
                                                   Expr.mul(linkonpath[s][d][p][e], y.index(s * destnum + d, p, t)))

                M.constraint(Expr.sub(linktimecap[e][t], linkload_et), Domain.greaterThan(0.))

        for d in range(destnum):
            expr_d = 0
            for m in range(srcnum):
                for t in range(slotnum):
                    expr_d = Expr.add(expr_d, x.index(m, d, t))
            M.constraint(Expr.sub(expr_d, Expr.mul(fsize, w.index(d))), Domain.greaterThan(0.))
            M.constraint(expr_d, Domain.lessThan(fsize))

            # arrange data transferred as early timeslot
            for t in range(slotnum):
                size_d_t = 0
                size_d_tt = 0
                for tt in range(t):
                    for m in range(srcnum):
                        size_d_t = Expr.add(size_d_t, x.index(m, d, tt))
                        size_d_tt = Expr.add(size_d_tt, x.index(m, d, tt))
                size_d_tt = Expr.add(size_d_tt, x.index(m, d, t))
                M.constraint(Expr.sub(size_d_tt, size_d_t), Domain.greaterThan(0.))
        # x_expr = Expr.sum(x,0,2)
        # print( x_expr.toString() )
        # M.constraint( Expr.sub( x_expr, Expr.mul(fsize, w)), Domain.equalsTo(0.) )

        M.solve()
        res_obj = 0
        res_w = 0
        res_y = 0
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

        if res_feasible == False:
            # print "nonfeasible: flexible source!"
            # print M.getPrimalSolutionStatus()
            # print M.getProblemStatus(SolutionType.Default)
            return res_obj, res_x, res_w, res_y, res_feasible

        res_x = x.level()
        res_w = w.level()
        # res_z = z.level()
        res_y = y.level()
        # res_h = h.level()
        # z_sum = [0.0 for d in range(destnum)]
        for d in range(destnum):
            res_obj += res_w[d]
        return res_obj, res_x, res_w, res_y, res_feasible


# the orignal sender is considered as the data source of all the recievers
def fixsrcMIPmodel(pathnum, linknum, destnum, slotnum, fsize, linkonpath, linktimecap, plen):
    with Model("mipmodel") as M:
        x = M.variable('X', [destnum, slotnum], Domain.greaterThan(0.0))
        y = M.variable('Y', [destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        w = M.variable('w', destnum, Domain.binary())

        obj_expr = Expr.sum(w)
        M.objective("completeddest", ObjectiveSense.Maximize, obj_expr)

        M.constraint(Expr.sub(Expr.sum(x, 1), Expr.mul(fsize, w)), Domain.equalsTo(0.))
        M.constraint(Expr.sub(Expr.sum(y, 1), x), Domain.equalsTo(0.))

        for e in range(linknum):
            for t in range(slotnum):
                linkload_et = 0
                for d in range(destnum):
                    for p in range(pathnum):
                        M.constraint(Expr.sub(y.index(d, p, t), fsize * plen[d][p]), Domain.lessThan(0.0))
                        linkload_et = Expr.add(linkload_et, Expr.mul(linkonpath[d][p][e], y.index(d, p, t)))
                M.constraint(Expr.sub(linktimecap[e][t], linkload_et), Domain.greaterThan(0.0))

        M.solve()
        res_obj = 0
        res_w = 0
        res_y = 0
        res_x = 0

        res_feasible = False
        acceptable = [
            ProblemStatus.PrimalAndDualFeasible,
            ProblemStatus.PrimalFeasible,
            ProblemStatus.DualFeasible]

        if M.getProblemStatus(SolutionType.Default) in acceptable:
            # print "feasible2"
            res_feasible = True
            # print M.getPrimalSolutionStatus()
            # print M.getProblemStatus(SolutionType.Default)

        if res_feasible == False:
            # print "nonfeasible: single source!"
            # print M.getPrimalSolutionStatus()
            # print M.getProblemStatus(SolutionType.Default)
            return res_obj, res_x, res_w, res_y, res_feasible

        res_w = w.level()
        res_x = x.level()
        res_y = y.level()
        for d in range(destnum):
            res_obj += res_w[d]

        return res_obj, res_x, res_w, res_y, res_feasible


def offlineMIPmodel(reqNum, nodeNum, slotNum, pathNum, linkNum, srcOfReq, dstOfReq, M_expr, fsizeOfAllReq,
                    timeOfSurvival, linkonpath, linktimecap, plen):
    # print "offline model..."
    # print "reqNum, nodeNum, slotNum, pathNum, linkNum, fsize, M_expr",reqNum, nodeNum, slotNum, pathNum, linkNum,fsizeOfAllReq,M_expr
    # print "srcOfReq", srcOfReq
    # print "dstOfReq", dstOfReq
    # print "linkonpath", linkonpath
    # print "timeOfSurvival", timeOfSurvival
    # print "linktimecap", linktimecap
    with Model("offlineModel") as M:
        x = M.variable('X', [reqNum, slotNum * nodeNum, nodeNum], Domain.greaterThan(0.0))
        y = M.variable('Y', [reqNum * nodeNum * nodeNum, pathNum, slotNum], Domain.greaterThan(0.0))
        z = M.variable('z', [reqNum, nodeNum, nodeNum], Domain.binary())  # whether src is the data source of dst
        h = M.variable('h', [reqNum, nodeNum, slotNum], Domain.binary())  # whether src can be a data source in time t
        w = M.variable('w', [reqNum, nodeNum], Domain.binary())  # whether dst is finished before deadline
        r = M.variable('r', reqNum, Domain.binary())
        # g = M.variable('g', 1, Domain.binary())

        M.objective("accepted_req", ObjectiveSense.Maximize, Expr.sum(r))
        # M.objective("accepted_req", ObjectiveSense.Maximize, Expr.sum(w))

        # constraints on size
        for i in range(reqNum):
            # for u in range(nodeNum):
            # expr_sub = 1 - srcOfReq[i][u] - dstOfReq[i][u]
            for t in range(slotNum):
                for u in range(nodeNum):
                    if srcOfReq[i][u] == 1:
                        # 对于每个request来说，其初始源数据中心始终可以作为任意数据中心的数据传输源
                        M.constraint((Expr.sub(h.index(i, u, t), timeOfSurvival[i][t])), Domain.equalsTo(0.0))
                    if dstOfReq[i][u] == 1:
                        # 得到每一个request的目的节点
                        M.constraint((Expr.sub(h.index(i, u, t), timeOfSurvival[i][t])), Domain.lessThan(0.0))
                    if srcOfReq[i][u] != 1 and dstOfReq[i][u] != 1:
                        # 在某一个request的存活期内，设置不属于该request的数据中心不能作为传输源
                        M.constraint(h.index(i, u, t), Domain.equalsTo(0.0))

        # constraint on maybe source site
        for i in range(reqNum):
            for v in range(nodeNum):
                if dstOfReq[i][v] == 1:
                    for t in range(slotNum):
                        expr_sum = 0
                        for tt in range(t):
                            for u in range(nodeNum):
                                # print(x.index(i, v*nodeNum+u, tt))
                                expr_sum = Expr.add(expr_sum, x.index(i, tt * nodeNum + u, v))
                        # expr_sum = Expr.sub(expr_sum, Expr.sum(g))
                        M.constraint(
                            Expr.sub(expr_sum, Expr.mul(fsizeOfAllReq[i], h.index(i, v, t))), Domain.greaterThan(0.0))

        # 目的数据中心从唯一源数据中心接收数据量不能超过fsize
        for i in range(reqNum):
            for t in range(slotNum):
                for u in range(nodeNum):
                    for v in range(nodeNum):
                        # expr_mul = Expr.mul(h.index(i, u, t), A[i][t][u][v])
                        M.constraint(
                            Expr.sub(x.index(i, t * nodeNum + u, v), Expr.mul(fsizeOfAllReq[i], h.index(i, u, t))),
                            Domain.lessThan(0.0))
                        # 某一目的数据中心从唯一确定的源数据中心接收到的数据不能超过fsize
                        M.constraint(
                            Expr.sub(x.index(i, t * nodeNum + u, v), Expr.mul(fsizeOfAllReq[i], z.index(i, u, v))),
                            Domain.lessThan(0.0))

        # constraint on z, only one source of each destination
        # M.constraint(Expr.sum(z, 1), Domain.equalsTo(1.0))
        for i in range(reqNum):
            for v in range(nodeNum):
                if dstOfReq[i][v] == 1:
                    M.constraint(Expr.sum(z.slice([i, 0, v], [i + 1, nodeNum, v + 1])), Domain.equalsTo(1))
                if dstOfReq[i][v] == 0:
                    M.constraint(Expr.sum(z.slice([i, 0, v], [i + 1, nodeNum, v + 1])), Domain.equalsTo(0))

        # allocating available bandwidth resources
        for t in range(slotNum):
            for i in range(reqNum):
                for u in range(nodeNum):
                    for v in range(nodeNum):
                        expr_sumy = 0
                        for p in range(pathNum):
                            M.constraint(Expr.sub(y.index(i * nodeNum * nodeNum + u * nodeNum + v, p, t),
                                                  fsizeOfAllReq[i] * plen[u][v][p]
                                                  ), Domain.lessThan(0.0))
                            expr_sumy = Expr.add(expr_sumy, y.index((i * nodeNum * nodeNum + u * nodeNum + v), p, t))
                        # expr_sumy = Expr.sub(expr_sumy, Expr.sum(g))
                        M.constraint(Expr.sub(expr_sumy, x.index(i, t * nodeNum + u, v)), Domain.equalsTo(0.))
            for e in range(linkNum):
                linkload_et = 0
                for i in range(reqNum):
                    for u in range(nodeNum):
                        for v in range(nodeNum):
                            for p in range(pathNum):
                                linkload_et = Expr.add(linkload_et, Expr.mul(linkonpath[u][v][p][e], y.index(
                                    (i * nodeNum * nodeNum + u * nodeNum + v), p, t)))
                # linkload_et = Expr.sub(linkload_et, Expr.sum(g))
                linkload_et = Expr.sub(linkload_et, linktimecap[e][t])
                M.constraint(linkload_et, Domain.lessThan(0.0))

        for i in range(reqNum):
            for v in range(nodeNum):
                if dstOfReq[i][v] == 1:
                    expr_d = 0
                    for t in range(slotNum):
                        for u in range(nodeNum):
                            expr_d = Expr.add(expr_d, x.index(i, t * nodeNum + u, v))
                    # expr_d = Expr.sub(expr_d, Expr.sum(g))
                    M.constraint(Expr.sub(expr_d, Expr.mul(fsizeOfAllReq[i], w.index(i, v))), Domain.equalsTo(0.))
                if dstOfReq[i][v] == 0:
                    M.constraint(Expr.sub(w.index(i, v), dstOfReq[i][v]), Domain.lessThan(0.0))

        for i in range(reqNum):
            expr_sumw = 0
            for v in range(nodeNum):
                expr_sumw = Expr.add(expr_sumw, w.index(i, v))
            # expr_sumw = Expr.sub(expr_sumw, Expr.sum(g))
            M.constraint(Expr.sub(expr_sumw, Expr.mul(r.index(i), M_expr[i])), Domain.equalsTo(0.0))

        M.solve()
        res_obj = 0
        res_fsize = 0.0
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
            return res_obj, res_fsize, res_r, res_x, res_w, res_y, res_feasible

        res_r = r.level()
        res_w = w.level()
        res_z = z.level()
        res_y = y.level()
        res_h = h.level()
        # print "res_w", res_w
        print "res_r", res_r
        # print("res_y", res_y)

        for i in range(reqNum):
            res_obj += res_r[i]
            if res_r[i] == 1:
                res_fsize += fsizeOfAllReq[i]

        # for i in range(reqNum):
        #     for u in range(nodeNum):
        #         for v in range(nodeNum):
        #             for k in range()
        # res_y_sum = Expr.sum(res_y)

        # print "res_y_sum", res_y_sum
        return res_obj, res_fsize, res_r, res_x, res_w, res_y, res_feasible


def maxThroughputmodel(pathnum, linknum, destnum, fsize, slotnum, linkonpath, linktimecap, remainratio,
                       assignedsrcfordest, sourcelist, plen):
    srcnum = destnum + 1
    # print "\n solve problem: pathnum, linkum, destnum, srcnum, slotnum ", pathnum, linknum, destnum, srcnum, slotnum

    with Model("Max-throughput-model") as M:
        # the data amount transferred from src to dest in every timeslot
        x = M.variable('X', [srcnum, destnum, slotnum], Domain.greaterThan(0.0))
        # y = M.variable('Y', [srcnum, destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        # resource allocation on path in every timeslot
        y = M.variable('Y', [srcnum * destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        z = M.variable('z', [srcnum, destnum], Domain.binary())  # whether src is the data source of a dest
        h = M.variable('h', [srcnum, slotnum], Domain.binary())  # whether src can be a data source in timeslot t
        # the data amount received at a dest before the end of the timeline used
        w = M.variable('w', destnum, Domain.greaterThan(0.))
        # g = M.variable('g', 1, Domain.binary())  # auxiliary variable

        M.objective("completed_data_ratio", ObjectiveSense.Maximize, Expr.sum(w))
        # constraints on size
        for t in range(slotnum):
            for src in sourcelist:
                M.constraint(h.index(src, t), Domain.equalsTo(1.))  # the source site s can be source over all the time
        # print destnum
        for d in range(destnum):
            s = d + 1
            if s not in sourcelist:
                M.constraint(h.index(s, 0),
                             Domain.equalsTo(0.))  # all the destination cannot be the data source at time 0
                # M.constraint(z.index(s,d), Domain.equalsTo(0.) )
        M.constraint(Expr.sub(w, remainratio), Domain.lessThan(0.))
        # constraint on maybe source site
        for d in range(destnum):
            for t in range(slotnum):
                expr_sumd = 0
                # check the time before t: the data size at every dc
                for tt in range(t):
                    for s in range(srcnum):
                        expr_sumd = Expr.add(expr_sumd, x.index(s, d, tt))
                # expr_sumd = Expr.sub(expr_sumd, Expr.sum(g))
                # M.constraint( Expr.sub(expr_sumd, Expr.mul(fsize, h.index(d+1,t))), Domain.greaterThan(0.) )
                # print "remainratio", remainratio
                M.constraint(Expr.sub(expr_sumd, Expr.mul(remainratio[d], Expr.mul(fsize, h.index(d + 1, t)))),
                             Domain.greaterThan(0.))

        # constraint on z, only one source of each destination
        M.constraint(Expr.sum(z, 0), Domain.lessThan(1.))
        M.constraint(Expr.sub(z, assignedsrcfordest), Domain.greaterThan(0.0))
        # M.constraint(Expr.sum(z,0), Domain.lessThan(srcUpperBound))

        # constraint on z and x
        for d in range(destnum):
            # every destinatin cannot be the source of itself
            M.constraint(z.index(d + 1, d), Domain.equalsTo(0.))
            for s in range(srcnum):
                expr_sumd = 0
                for t in range(slotnum):
                    expr_sumd = Expr.add(expr_sumd, x.index(s, d, t))
                # expr_sumd = Expr.sub(expr_sumd, Expr.sum(g))
                # expr_sumd = Expr.mul(fsize, expr_sumd)
                M.constraint(Expr.sub(expr_sumd, Expr.mul(remainratio[d], Expr.mul(fsize, z.index(s, d)))),
                             Domain.lessThan(0.))
        # M.constraint(Expr.sub(Expr.sum(x,2), Expr.mul(fsize,z)), Domain.lessThan(0.))

        # constraint on path y and link e
        for t in range(slotnum):
            for m in range(srcnum):
                for d in range(destnum):
                    M.constraint(Expr.sub(x.index(m, d, t), Expr.mul(remainratio[d], Expr.mul(fsize, h.index(m, t)))),
                                 Domain.lessThan(0.))
                    expr_sumy = 0
                    for p in range(pathnum):
                        expr_sumy = Expr.add(expr_sumy, y.index(m * destnum + d, p, t))
                        M.constraint(Expr.sub(y.index(m * destnum + d, p, t), fsize * plen[m][d][p]),
                                     Domain.lessThan(0.0))
                    # expr_sumy = Expr.sub(expr_sumy, Expr.sum(g))
                    M.constraint(Expr.sub(expr_sumy, x.index(m, d, t)), Domain.equalsTo(0.))
            for e in range(linknum):
                linkload_et = 0
                for s in range(srcnum):
                    for d in range(destnum):
                        for p in range(pathnum):
                            linkload_et = Expr.add(linkload_et,
                                                   Expr.mul(linkonpath[s][d][p][e], y.index(s * destnum + d, p, t)))
                # linkload_et = Expr.sub(linkload_et, Expr.sum(g))
                linkload_et = Expr.sub(linkload_et, linktimecap[e][t])
                M.constraint(linkload_et, Domain.lessThan(0.))

        for d in range(destnum):
            expr_d = 0
            for m in range(srcnum):
                for t in range(slotnum):
                    expr_d = Expr.add(expr_d, x.index(m, d, t))
            # expr_d = Expr.sub(expr_d, Expr.sum(g))
            M.constraint(Expr.sub(expr_d, Expr.mul(fsize, w.index(d))), Domain.greaterThan(0.))
            # M.constraint( expr_d, Domain.lessThan(fsize))

        M.solve()
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
            return res_w, res_y, res_z, res_feasible

        res_w = w.level()
        res_z = z.level()
        res_y = y.level()
        res_h = h.level()
        res_x = x.level()

        # print "res_x", res_x

        return res_w, res_y, res_z, res_feasible


def steinertreeLPmodel(reqnum, treenum, linknum, rSlotNum, fsize, linkontree, linktimecap, W, lifetime, maxlifetime, tcur):
    # print "\n solve problem: pathnum, linkum, destnum, srcnum, slotnum ", pathnum, linknum, destnum, srcnum, slotnum
    #print "fsize", fsize
    with Model("multicast_tree") as M:
        c = M.variable('ka', 1, Domain.greaterThan(0.0))
        x = M.variable('X', [reqnum, treenum], Domain.greaterThan(0.))

        temp_sum = 0
        mu = 0.01
        for i in range(reqnum):
            for t in range(treenum):
                temp_sum = Expr.add(temp_sum, Expr.mul(W[i][t], x.index(i, t)))
        obj = Expr.sub(c, Expr.mul(mu, temp_sum))

        M.objective("multicast_tree", ObjectiveSense.Maximize, obj)

        for i in range(reqnum):
            temp_sum_xd2 = 0
            for t in range(treenum):
                temp_sum_xd2 = Expr.add(temp_sum_xd2, x.index(i, t))
            M.constraint(Expr.sub(Expr.mul(rSlotNum[i], temp_sum_xd2), fsize[i]), Domain.greaterThan(0.0))
            M.constraint(Expr.sub(c, temp_sum_xd2), Domain.lessThan(0.0))
        # print("reqnum, len, linknum", reqnum, len(lifetime), linknum, treenum)
        # print(linkontree, tcur)
        for tm in range(maxlifetime):
            for e in range(linknum):
                temp_sum_x = 0
                for i in range(reqnum):
                    for t in range(treenum):
                        # print(i, tm, e, t)
                        temp_sum_x = Expr.add(temp_sum_x, Expr.mul(lifetime[i][tm], Expr.mul(linkontree[i][t][e], x.index(i, t))))
                # print(e, len())
                M.constraint(Expr.sub(temp_sum_x, linktimecap[e][tcur + tm]), Domain.lessThan(0.))

        M.solve()
        res_x = 0
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
        # print "x", res_x
        return res_x, res_feasible
