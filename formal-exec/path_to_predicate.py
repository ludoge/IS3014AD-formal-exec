from model.cfg import *
from model.arithmexpr import *
from model.booleanexpr import *

def stringify_expr(expr):
    """
    Convert a boolean or an artitmexpr into a string (with parenthesis) to define constraints
    """
    if expr is BooleanConst or expr is BooleanVar or expr is ArithmConst or expr is ArithmVar:
        return str(expr)
    elif expr is BooleanBinaryExp or expr is ArithmBinExp:
        return "(" + stringify_expr(expr.children[0]) + ")" + expr.operator + "(" + stringify_expr(expr.children[1]) + ")"
    elif expr is BooleanUnaryExp or expr is ArithmUnaryExp:
        return expr.operator + "(" + stringify_expr(expr.children[0]) + ")"
    else:
        return str(expr)


def exec_edge(e, valuation, constraints):
    """
    Given an edge of a control flow graph, a current valuation for variable and constraints, updates them according to
    the command found in the edge
    :param e: edge
    :param valuation: current state of variables to be updated
    :param constraints: current constraints to be updated
    :return:
    """
    if e['booleanexpr'] != BooleanConst(True) and e['booleanexpr'] != BooleanConst(False):
        expr = stringify_expr(e['booleanexpr'])
        for v in valuation:
            expr = expr.replace(v, stringify_expr(valuation[v]))
        constraints.add(expr)

    if e['command'].typename == "Assign":
        var = e['command'].children[0].name
        expr = stringify_expr(e['command'].children[1])
        for v in valuation:
            valuation[v] = valuation[v].replace(var, expr)

    return valuation, constraints


def path_predicate(cfg, path):
    valuation = {str(x): str(x) for x in get_var(cfg)}
    constraints = set()
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        e = cfg[u][v]
<<<<<<< HEAD
        valuation, constraints = exec_edge(e, valuation, constraints)
=======
        valuation, constraints = exec_edge(cfg, e, valuation, constraints)
>>>>>>> d90e978272eb736b8167fb52a729f919ee9d645e
    return valuation, constraints


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
    print(path_predicate(cfg, path))
