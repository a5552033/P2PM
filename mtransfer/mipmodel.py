from mosek.fusion import *


#a DC can be the data sender other receivers only if it already has received a full copy of data
#the objective is maximize the number of completed receivers before deadline
def flexiblesrcMIPmodel(pathnum, linknum, destnum, slotnum, fsize, linkonpath, linktimecap, srcUpperBound):
    srcnum = destnum+1  
    #print "\n solve problem: pathnum, linkum, destnum, srcnum, slotnum ", pathnum, linknum, destnum, srcnum, slotnum

    with Model("mipmodel") as M:
        x = M.variable('X', [srcnum, destnum, slotnum], Domain.greaterThan(0.0))
        #y = M.variable('Y', [srcnum,ss destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        y = M.variable('Y', [srcnum*destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        z = M.variable('z', [srcnum, destnum], Domain.binary())   #whether src is the data source of dest
        h = M.variable('h', [srcnum, slotnum], Domain.binary()) #whether src can be a data source in time t
        w = M.variable('w', destnum, Domain.binary()) #whether dest is finished before deadline
        g = M.variable('g', 1, Domain.binary())

        M.objective( "completed_dest", ObjectiveSense.Maximize, Expr.sum(w))

        #constraints on size
        for t in range(slotnum):
            M.constraint( h.index(0,t), Domain.equalsTo(1.) ) #the source site s can be source over all the time
        for s in range(srcnum-1):
            M.constraint( h.index(s+1,0), Domain.equalsTo(0.) ) #all the destination cannot be the data source at time 0

        #constraint on maybe source site
        for d in range(destnum):
            for t in range(slotnum):
                #M.constraint(x.index(d+1,d,t), Domain.equalsTo(0.0)) #each destination can never be the data source of itself
                expr_sumd = Expr.sum(g)
                for tt in range(t):
                    for s in range(srcnum):
                        expr_sumd = Expr.add( expr_sumd, x.index(s,d,tt) )
                expr_sumd = Expr.sub(expr_sumd, Expr.sum(g))
                M.constraint( Expr.sub(expr_sumd, Expr.mul(fsize, h.index(d+1,t))), Domain.greaterThan(0.) )
        
        #constraint on z, only one source of each destination
        M.constraint( Expr.sum(z,0), Domain.equalsTo(1.))
        #multiple senders of a receiver
        #M.constraint(Expr.sum(z,0), Domain.lessThan(srcUpperBound))

        #constraint on z and x
        for d in range(destnum):
            M.constraint(z.index(d+1,d), Domain.equalsTo(0.))
        M.constraint(Expr.sub(Expr.sum(x,2), Expr.mul(fsize,z)), Domain.lessThan(0.))

        for t in range(slotnum):
            for m in range(srcnum):
                for d in range(destnum):
                    M.constraint( Expr.sub(x.index(m,d,t), Expr.mul(fsize, h.index(m,t))), Domain.lessThan(0.) )
                    expr_sumy = Expr.sum(g)
                    for p in range(pathnum):
                        expr_sumy = Expr.add(expr_sumy, y.index(m*destnum+d, p, t) )
                    expr_sumy = Expr.sub( expr_sumy, Expr.sum(g) )
                    M.constraint( Expr.sub( expr_sumy, x.index(m,d,t)), Domain.equalsTo(0.) )
                    #M.constraint( Expr.sub( Expr.sum(y.slice([m*destnum+d,0,t],[m*destnum+d,pathnum, t])), x.index(m,d,t)), Domain.equalsTo(0.) )
            for e in range(linknum):
                linkload_et = Expr.sum(g)
                for s in range(srcnum):
                    for d in range(destnum):
                        for p in range(pathnum):
                            linkload_et = Expr.add(linkload_et, Expr.mul(linkonpath[e][s][d][p], y.index(s*destnum+d,p,t)))
                linkload_et = Expr.sub(linkload_et, Expr.sum(g))
                linkload_et = Expr.sub(linkload_et, linktimecap[e][t])
                M.constraint( linkload_et, Domain.lessThan(0.) )
        
        for d in range(destnum):
            expr_d = Expr.sum(g)
            for m in range(srcnum):
                for t in range(slotnum):
                    expr_d = Expr.add( expr_d, x.index(m,d,t))
            expr_d = Expr.sub(expr_d, Expr.sum(g) )
            M.constraint(Expr.sub( expr_d, Expr.mul(fsize, w.index(d)) ), Domain.greaterThan(0.) )
            M.constraint(expr_d, Domain.lessThan(fsize))
        #x_expr = Expr.sum(x,0,2)
        #print( x_expr.toString() )
        #M.constraint( Expr.sub( x_expr, Expr.mul(fsize, w)), Domain.equalsTo(0.) )

        M.solve()
        res_obj = 0
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
            #print "feasible"
            res_feasible = True

        if res_feasible == False:
            #print "nonfeasible: flexible source!"
            #print M.getPrimalSolutionStatus()
            #print M.getProblemStatus(SolutionType.Default)
            return res_obj, res_x, res_w, res_y, res_feasible

        res_w = w.level()
        res_z = z.level()
        res_y = y.level()
        res_h = h.level()
        z_sum = [0.0 for d in range(destnum)]
        for d in range(destnum):
            res_obj += res_w[d]
        return res_obj, res_x, res_w, res_y, res_feasible

#the orignal sender is considered as the data source of all the recievers
def fixsrcMIPmodel(pathnum, linknum, destnum, slotnum, fsize, linkonpath, linktimecap):
    with Model("mipmodel") as M:
        x = M.variable('X', [destnum, slotnum], Domain.greaterThan(0.0))
        y = M.variable('Y', [destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        w = M.variable('w', destnum, Domain.binary())
        g = M.variable('g',1, Domain.binary()) #fuzhu bianliang

        obj_expr = Expr.sum(w)
        M.objective( "completeddest", ObjectiveSense.Maximize, obj_expr)

        M.constraint( Expr.sub( Expr.sum(x,1), Expr.mul(fsize, w) ), Domain.equalsTo(0.) )        
        M.constraint( Expr.sub(Expr.sum(y,1), x),  Domain.equalsTo(0.) )
        
        for e in range(linknum):
            for t in range(slotnum):
                linkload_et = Expr.sum(g)
                for d in range(destnum):
                    for p in range(pathnum):
                        linkload_et = Expr.add(linkload_et, Expr.mul(linkonpath[e][d][p], y.index(d,p,t)))
                linkload_et = Expr.sub(linkload_et, Expr.sum(g))

                linkload_et = Expr.sub(linktimecap[e][t], linkload_et)
                M.constraint( linkload_et, Domain.greaterThan(0.0) )
        
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
            #print "feasible2"
            res_feasible = True
            #print M.getPrimalSolutionStatus()
            #print M.getProblemStatus(SolutionType.Default)

        if res_feasible == False:
            #print "nonfeasible: single source!"
            #print M.getPrimalSolutionStatus()
            #print M.getProblemStatus(SolutionType.Default)
            return res_obj, res_x, res_w, res_y, res_feasible
        
        res_w = w.level()
        res_x = x.level()
        res_y = y.level()
        for d in range(destnum):
            res_obj += res_w[d]

        return res_obj, res_x, res_w, res_y, res_feasible


def test():
    with Model("mipmodel") as M:
        x = M.variable('x', [2,2], Domain.greaterThan(0.0))
        h = M.variable('h', 2, Domain.binary())

        #for d in range(2):
        #    M.constraint( Expr.sub(Expr.sum(x.slice([d,0],[d,2])), Expr.mul(100.0, h.index(d))), Domain.equalsTo(0.)) 
        M.constraint( Expr.sub(Expr.sum(x,1), Expr.mul(100.0, h)), Domain.equalsTo(0.))
        M.objective( "completeddest", ObjectiveSense.Maximize, Expr.sum(h))
        M.solve()
        res_h = 0
        res_x = 0
        res_feasible = False        
        acceptable = [
                        ProblemStatus.PrimalAndDualFeasible,
                        ProblemStatus.PrimalFeasible,
                        ProblemStatus.DualFeasible]

        if M.getProblemStatus(SolutionType.Default) in acceptable:
            #print "feasible2"
            res_feasible = True
            print M.getPrimalSolutionStatus()
            print M.getProblemStatus(SolutionType.Default)
            res_h=h.level()
            res_x=x.level()
            print res_h,res_x

        if res_feasible == False:
            #print "nonfeasible2"
            print M.getPrimalSolutionStatus()
            print M.getProblemStatus(SolutionType.Default)


#a DC can be the data sender other recievers only if it already has received a full copy of data
#the objective is maximize data transferred before a certain time
def maxThroughputmodel(pathnum, linknum, destnum, fsize, slotnum, linkonpath, linktimecap, remainratio, assignedsrcfordest, sourcelist):
    srcnum = destnum+1  
    print "\n solve problem: pathnum, linkum, destnum, srcnum, slotnum ", pathnum, linknum, destnum, srcnum, slotnum

    with Model("mipmodel") as M:
        x = M.variable('X', [srcnum, destnum, slotnum], Domain.greaterThan(0.0)) #the data amount transferred from src to dest in every timeslot
        #y = M.variable('Y', [srcnum, destnum, pathnum, slotnum], Domain.greaterThan(0.0))
        y = M.variable('Y', [srcnum*destnum, pathnum, slotnum], Domain.greaterThan(0.0)) #resource allocation on path in every timeslot
        z = M.variable('z', [srcnum, destnum], Domain.binary())   #whether src is the data source of a dest
        h = M.variable('h', [srcnum, slotnum], Domain.binary()) #whether src can be a data source in timeslot t
        w = M.variable('w', destnum, Domain.greaterThan(0.)) #the data amount received at a dest before the end of the timeline used
        g = M.variable('g', 1, Domain.binary()) #auxiliary variable

        M.objective( "completed_data_ratio", ObjectiveSense.Maximize, Expr.sum(w))
        #constraints on size
        for t in range(slotnum):
            for src in sourcelist:
                M.constraint(h.index(src,t), Domain.equalsTo(1.) ) #the source site s can be source over all the time
        #print destnum
        for d in range(destnum):
            s = d+1
            if s not in sourcelist:
                M.constraint(h.index(s,0), Domain.equalsTo(0.) ) #all the destination cannot be the data source at time 0
                #M.constraint(z.index(s,d), Domain.equalsTo(0.) )
        #M.constraint(Expr.sub(fsize, w), Domain.greaterThan(0.)) #the data received at dests is no more than the to-be-transferred remaining data size
        M.constraint(Expr.sub(w, remainratio), Domain.lessThan(0.))
        #constraint on maybe source site
        for d in range(destnum):
            for t in range(slotnum):
                #M.constraint(x.index(d+1,d,t), Domain.equalsTo(0.0)) #each destination can never be the data source of itself
                expr_sumd = Expr.sum(g)
                #check the time before t: the data size at every dc
                for tt in range(t):
                    for s in range(srcnum):
                        expr_sumd = Expr.add( expr_sumd, x.index(s,d,tt) )
                expr_sumd = Expr.sub(expr_sumd, Expr.sum(g))
                #M.constraint( Expr.sub(expr_sumd, Expr.mul(fsize, h.index(d+1,t))), Domain.greaterThan(0.) )
                #print "remainratio", remainratio
                M.constraint( Expr.sub(expr_sumd, Expr.mul(remainratio[d],Expr.mul(fsize, h.index(d+1,t)))), Domain.greaterThan(0.) )

        #constraint on z, only one source of each destination
        M.constraint(Expr.sum(z, 0), Domain.lessThan(1.))
        M.constraint(Expr.sub(z, assignedsrcfordest), Domain.greaterThan(0.0) )
        #M.constraint(Expr.sum(z,0), Domain.lessThan(srcUpperBound))

        #constraint on z and x
        for d in range(destnum):
            #every destinatin cannot be the source of itself
            M.constraint(z.index(d+1,d), Domain.equalsTo(0.))
            for s in range(srcnum):
                expr_sumd = Expr.sum(g)
                for t in range(slotnum):
                    expr_sumd = Expr.add(expr_sumd, x.index(s,d,t))
                expr_sumd = Expr.sub(expr_sumd, Expr.sum(g))
                #expr_sumd = Expr.mul(fsize, expr_sumd)
                M.constraint(Expr.sub( expr_sumd, Expr.mul(remainratio[d], Expr.mul(fsize, z.index(s,d)))), Domain.lessThan(0.))
        #M.constraint(Expr.sub(Expr.sum(x,2), Expr.mul(fsize,z)), Domain.lessThan(0.))

        #constraint on path y and link e
        for t in range(slotnum):
            for m in range(srcnum):
                for d in range(destnum):
                    M.constraint( Expr.sub(x.index(m,d,t), Expr.mul(remainratio[d],Expr.mul(fsize, h.index(m,t)))), Domain.lessThan(0.) )
                    expr_sumy = Expr.sum(g)
                    for p in range(pathnum):
                        expr_sumy = Expr.add(expr_sumy, y.index(m*destnum+d, p, t) )
                    expr_sumy = Expr.sub( expr_sumy, Expr.sum(g) )
                    M.constraint( Expr.sub( expr_sumy, x.index(m,d,t)), Domain.equalsTo(0.) )
                    #M.constraint( Expr.sub( Expr.sum(y.slice([m*destnum+d,0,t],[m*destnum+d,pathnum, t])), x.index(m,d,t)), Domain.equalsTo(0.) )
            for e in range(linknum):
                linkload_et = Expr.sum(g)
                for s in range(srcnum):
                    for d in range(destnum):
                        for p in range(pathnum):
                            linkload_et = Expr.add(linkload_et, Expr.mul(linkonpath[e][s][d][p], y.index(s*destnum+d,p,t)))
                linkload_et = Expr.sub(linkload_et, Expr.sum(g))
                linkload_et = Expr.sub(linkload_et, linktimecap[e][t])
                M.constraint( linkload_et, Domain.lessThan(0.) )
        
        for d in range(destnum):
            expr_d = Expr.sum(g)
            for m in range(srcnum):
                for t in range(slotnum):
                    expr_d = Expr.add( expr_d, x.index(m,d,t))
            expr_d = Expr.sub(expr_d, Expr.sum(g))
            M.constraint( Expr.sub( expr_d, Expr.mul(fsize, w.index(d)) ), Domain.greaterThan(0.) )
            #M.constraint( expr_d, Domain.lessThan(fsize))

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
            #print "feasible"
            res_feasible = True

        if res_feasible == False:
            #print "nonfeasible: max_throughput"
            #print M.getPrimalSolutionStatus()
            #print M.getProblemStatus(SolutionType.Default)
            return res_w, res_y, res_z, res_feasible

        res_w = w.level()
        res_z = z.level()
        res_y = y.level()
        res_h = h.level()
        res_x = x.level()

        #print "res_x", res_x
   
        return  res_w, res_y, res_z, res_feasible
        



