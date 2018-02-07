from path_to_predicate import *
from predicate_solve import *
from model.cfg import *

if __name__ == '__main__':
    p1 = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)),

               Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1),
               label=0)
    p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1), label=3),
            Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)

    ast = Sequence(p1, p2)

    cfg = ast_to_cfg_with_end(ast)

    valuation = {'X': 'X', 'Y': 'Y'}
    constraints = set()
    e = [cfg[u][v] for (u, v) in cfg.edges][2]
    exec_edge(cfg, e, valuation, constraints)

    path = get_paths(cfg, 10)[0]
    print(path)
    vars, constraints = (path_predicate(cfg, path))
    vars = {k for k, v in vars.items()}
    print(vars)

    ps = PredicateSolver(vars, constraints)
    ps.add_constraints()
    print(ps.problem.getSolutions())
