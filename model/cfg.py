from collections import defaultdict
import copy
import pydot
from model.booleanexpr import *
from model.arithmexpr import *
from model.command import *
import matplotlib.pyplot as plt
import networkx as nx

def ast_to_cfg(prog, previous_edges={("START", BooleanConst(True), Skip())}, cfg=nx.DiGraph()):
    """
    Takes a program as a tree and generates its control flow graph recursively
    Since the tree syntax is not sequential at any given step there are "dangling" edges that are also returned
    :param prog:
    :param previous_edges:
    :return:
    """

    if previous_edges is None:
        return cfg, None

    if prog.typename != "Sequence":
        # Not a sequence, we create a node and link all dangling edges to it
        cfg.add_node(prog.label, command=prog.typename)
        for previous_node, condition, command in previous_edges:
            cfg.add_edge(previous_node, prog.label, booleanexpr=condition, command=command)

    if prog.typename == "Assign" or prog.typename == "Skip":
        # Assign command doesn't branch
        return cfg, {(prog.label, BooleanConst(True), prog)}

    if prog.typename == "If":
        # Here we need to branch, and call our function on both conditions linking them to this command
        # with the appropriate edges
        condition, iftrue, iffalse = prog.children
        cfg, true_dangling_edges = ast_to_cfg(iftrue, previous_edges={(prog.label, condition, Skip())}, cfg=cfg)
        cfg, false_dangling_edges = ast_to_cfg(iffalse, previous_edges={(prog.label, BooleanUnaryExp("!", condition), Skip())}, cfg=cfg)

        true_dangling_edges.update(false_dangling_edges)
        return cfg, true_dangling_edges

    if prog.typename == "While":
        # Here we actually need to loop
        # First we create an edge for the "if true"
        while_condition, do = prog.children
        cfg, dangling_edges = ast_to_cfg(do, cfg=cfg, previous_edges={(prog.label, while_condition, Skip())})
        # Dangling edges loop back to the condition
        for previous_node, condition, command in dangling_edges:
            cfg.add_edge(previous_node, prog.label, booleanexpr=condition, command=command)
        # Don't forget to exit the loop; leave a dangling edge with the opposite of the condition
        return cfg, {(prog.label, BooleanUnaryExp("!", while_condition), Skip())}

    if prog.typename == "Sequence":
        # A sequence command does not call for a node
        # We convert the commands and link them up
        temp_edges = copy.deepcopy(previous_edges)
        for command in list(prog.children):
            cfg, temp_edges = ast_to_cfg(command, cfg=cfg, previous_edges=copy.deepcopy(temp_edges))
        return cfg, temp_edges


def ast_to_cfg_with_end(prog):
    cfg, final_edges = ast_to_cfg(prog)
    cfg.add_node("END")
    for node, condition, command in final_edges:
        cfg.add_edge(node, "END", booleanexpr=condition, command = command)

    return cfg


def get_var_from_exp(expr):
    var = set([])
    if expr.typename == "ArithmVar" or expr.typename == "BooleanVar":
        var.update(expr.name)
    else:
        for e in list(expr.children)[0:]:
            sub = get_var_from_exp(e)
            if sub is not None:
                var.update(get_var_from_exp(e))
    return var


def get_var(cfg):
    """
    Returns all variables appearing in cfg
    :param cfg:
    :return:
    """
    var = set([])
    for (u,v) in cfg.edges:
        for expr in cfg[u][v]['command'].children:
            if expr is not None:
                var.update(get_var_from_exp(expr))
    return var


def get_def(cfg):
    """
    Returns all variables assigned in cfg
    :param cfg:
    :return:
    """
    var = get_var(cfg)
    res = set([])
    for u in cfg.nodes:
        for v in cfg.neighbors(u):
            if cfg[u][v]['command'].typename == "Assign":
                res.update(cfg[u][v]['command'].children[0].name)
    return res


def get_ref(cfg):
    """
    Returns all variables whose value is accessed in cfg
    :param cfg:
    :return:
    """
    var = get_var(cfg)
    res = set([])
    for u in cfg.nodes:
        for v in cfg.neighbors(u):
            exp, command = cfg[u][v]['booleanexpr'], cfg[u][v]['command']
            if exp is not None:
                res.update(get_var_from_exp(exp))
            if command.typename == "Assign":
                #print(get_var_from_exp(command.children[1]))
                res.update(get_var_from_exp(command.children[1]))
    return res


def get_def_after_label(cfg, label):
    """
    Return the variable assigned at this label. If no variable is assigned at this label, return an empty set.
    """
    res = set()
    for v in cfg.neighbors(label):
        if cfg[label][v]['command'].typename == "Assign":
            res.update(cfg[label][v]['command'].children[0].name)
    return res


def get_ref_after_label(cfg, label):
    """
    Return the set of variables which are referenced at this label.
    """
    res = set()
    for v in cfg.neighbors(label):
        exp, command = cfg[label][v]['booleanexpr'], cfg[label][v]['command']
        if exp is not None:
            res.update(get_var_from_exp(exp))
        if command.typename == "Assign":
            res.update(get_var_from_exp(command.children[1]))
    return res


def execution_path(graph, values):
    current_node = 'START'
    path = []
    while current_node != "END":
        path.append(current_node)
        neighbors = list(graph.neighbors(current_node))
        # First to choose next node
        if len(neighbors)==1:
            next_node = neighbors[0]
        elif len(neighbors)==2:
            if_node, else_node = neighbors[0], neighbors[1]
            condition = graph.edges[current_node, if_node]['booleanexpr']
            if condition.eval(values):
                next_node = if_node
            else:
                next_node = else_node
        #  Now we execute and move on
        values = graph.edges[current_node, next_node]['command'].exec(values=values)
        current_node = next_node
    path.append('END')
    return path


def get_paths_exact(cfg, k, u='START'):
    """
    Finds all paths of length k starting from u recursively
    :param cfg:
    :param k:
    :param u:
    :return:
    """
    if k == 0:
        return [[u]]
    paths = [[u] + path for neighbor in cfg.neighbors(u) for path in get_paths_exact(cfg, k-1, neighbor)]
    return paths


def get_paths(cfg, k, u='START', v='END'):
    if k == 0:
        return []
    return [path for path in get_paths_exact(cfg, k, u) if path[-1] == v] + get_paths(cfg, k - 1, u, v)


def get_paths_with_limited_loop(cfg, i, u='START', v='END', current_loops={}):
    """
    Finds all paths with at most i loops for each 'While' starting from u recursively
    """

    if u == v:
        return [[u]]

    if u in current_loops and current_loops[u][0] > i:
        return []

    res = []
    # Case of a WHILE (or an IF) loop, meaning that we increment counter if we stay in the loop, and erase if when exiting
    neighbors = list(cfg.neighbors(u))
    if len(neighbors) == 2:
        # Stay in the loop
        new_current_loops = copy.deepcopy(current_loops)
        if u in new_current_loops:
            new_current_loops[u][0] += 1
        else:
            new_current_loops[u] = [1, list(current_loops.keys())]
        res += [[u] + path for path in get_paths_with_limited_loop(cfg, i, neighbors[0], v, new_current_loops) if path != []]
        # Exit the loop
        new_current_loops = copy.deepcopy(current_loops)
        if u in new_current_loops:
            del new_current_loops[u]  # Remove this loop
        for sub_u in new_current_loops.keys():  # Remove all sub-loops
            if u in new_current_loops[sub_u][1]:
                del new_current_loops[sub_u]
        res += [[u] + path for path in get_paths_with_limited_loop(cfg, i, neighbors[1], v, new_current_loops) if path != []]
        return res

    return [[u] + path for neighbor in cfg.neighbors(u) for path in get_paths_with_limited_loop(cfg, i, neighbor, v, current_loops) if path != []]


def check_var_next_reference(cfg, variable, path):
    """
    Check if a variable is referenced in a path before being defined again.
    """
    if len(path) <= 1:
        return False
    u = path[0]
    v = path[1]
    exp, command = cfg[u][v]['booleanexpr'], cfg[u][v]['command']
    # If variable is referenced in the expression
    if exp is not None and variable in get_var_from_exp(exp):
        return True
    # If variable is assigned to an other variable
    if command.typename == "Assign" and variable in get_var_from_exp(command.children[1]):
        return True
    # If variable is defined again
    if command.typename == "Assign" and variable == command.children[0].name:
        return False
    return check_var_next_reference(cfg, variable, path[1:])


def get_assigns(cfg):
    """
    Returns all labels of assigns in cfg
    """
    res = set([])
    for u in cfg.nodes:
        for v in cfg.neighbors(u):
            if cfg[u][v]['command'].typename == "Assign":
                res.add(cfg[u][v]['command'].label)
    return res


def get_assigns_with_next_reference(cfg, path):
    """
    Get list of assigns in a path which verify the check_var_next_reference function
    """
    if len(path) <= 1:
        return set()
    u = path[0]
    v = path[1]
    command = cfg[u][v]['command']
    res = get_assigns_with_next_reference(cfg, path[1:])
    if command.typename == "Assign":
        if check_var_next_reference(cfg, command.children[0].name, path[1:]):
            res.add(u)
    return res


def check_no_assign_sub_path(cfg, path, variable):
    """
    Checks if given sub_path contains no further assignments of variable and one use of the variable at the end
    :param cfg:
    :param path:
    :param variable:
    :return:
    """
    u = path[0]
    v = path[-1]

    if len(path) < 2:
        return False

    # Check if variable is assigned after u
    if variable not in get_def_after_label(cfg, u):
        return False

    # Check if variable is referenced after v
    if variable not in get_ref_after_label(cfg, v):
        return False

    for i in range(1, len(path) - 1):
        w = path[i]
        if variable in get_def_after_label(cfg, w):
            return False
    return True


def all_uses(cfg, variable):
    """
    Returns all pairs of nodes where variable is assigned at u and not used until v
    Todo: do this without brute force
    :param variable:
    :return:
    """
    res = set()
    for u in cfg.nodes:
        for v in cfg.nodes:
            all_simple_paths = get_paths(cfg, len(cfg), u, v)
            for sp in all_simple_paths:
                if check_no_assign_sub_path(cfg, sp, variable):
                    #print((u, v))
                    res.add((u, v))
                    break
    return res


def sub_paths(path, u, v):
    """
    Finds all subpaths in path starting with u and ending with v
    :param path:
    :param u:
    :param v:
    :return:
    """
    res = []
    for i in range(len(path) - 1):
        for j in range(i, len(path)):
            if path[i] == u and path[j] == v:
                res.append(path[i:j + 1])
    return res


def get_conditions_from_expression(expr):
    cond = set([])
    if expr.typename == "BooleanConst":
        return cond
    elif expr.typename == "BooleanVar":
        cond.add(copy.deepcopy(expr))
    elif expr.typename == "BooleanBinaryExp" and expr.operator in ['==', '!=', '<', '>', '<=', '>=']:
        cond.add(copy.deepcopy(expr))
    else:
        for e in list(expr.children):
                cond.update(get_conditions_from_expression(e))
    return cond


def get_all_conditions(cfg):
    """
    Return all boolean condition with their label in cfg
    """
    cond = {}
    for u in cfg.nodes:
        neighbors = list(cfg.neighbors(u))
        if len(neighbors) == 2:
            cond[u] = list(get_conditions_from_expression(cfg[u][neighbors[0]]['booleanexpr']))
    return cond


def get_conditions_values(cfg, values, conditions):
    """
    Get values taken for each condition for this execution
    """
    current_node = 'START'
    conditions_values = []
    while current_node != "END":
        neighbors = list(cfg.neighbors(current_node))
        # First to choose next node
        if len(neighbors)==1:
            next_node = neighbors[0]
        elif len(neighbors)==2:
            if_node, else_node = neighbors[0], neighbors[1]
            condition = cfg.edges[current_node, if_node]['booleanexpr']
            if condition.eval(values):
                next_node = if_node
            else:
                next_node = else_node
            # We check the value of every condition
            if current_node in conditions:
                for cond_expr in conditions[current_node]:
                    cond_value = cond_expr.eval(values)
                    if (current_node, cond_expr, cond_value) not in conditions_values:
                        conditions_values.append((current_node, cond_expr, cond_value))
        #  Now we execute and move on
        values = cfg.edges[current_node, next_node]['command'].exec(values=values)
        current_node = next_node
    return conditions_values

if __name__ == '__main__':
    from anytree import RenderTree

    p0 = While(BooleanBinaryExp('&&',BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)),BooleanBinaryExp('!=', ArithmVar('X'), ArithmConst(10))),
               Assign(ArithmVar('X'), ArithmBinExp('+', ArithmVar('X'), ArithmConst(-1)), label=8), label=7)
    p1 = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)), Sequence(p0, Sequence(
        Assign(ArithmVar('X'), ArithmBinExp('+', ArithmVar('X'), ArithmConst(1)), label=0.5),
        Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1))), label=0)
    p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1),label=3), Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)
    #p1 = If(BooleanBinaryExp('<=',ArithmVar('X'),ArithmConst(0)), Assign(ArithmVar('X'),ArithmUnaryExp("-",ArithmVar('X')),label=2), Assign(ArithmVar('X'), ArithmBinExp("-", ArithmConst(1), ArithmVar('X')), label=3), label=1)
    #p2 = If(BooleanBinaryExp('==',ArithmVar('X'),ArithmConst(1)), Assign(ArithmVar('X'),ArithmConst(1),label=5), Assign(ArithmVar('X'), ArithmBinExp("+", ArithmVar('X'), ArithmConst(1)), label=6), label=4)
    #print(p1)
    prog = Sequence(p1, p2)
    cprog = copy.deepcopy(prog)
    # prog = Sequence(p2, p1)
    #print(RenderTree(prog))
    #print(prog)

    # print(RenderTree(cprog))
    cfg = ast_to_cfg_with_end(prog)
    #print(cfg.nodes)
    #for u,v in cfg.edges:
    #    print(cfg[u][v]['command'].typename)
    pos = nx.nx_pydot.pydot_layout(cfg)
    nx.draw_networkx(cfg, pos=pos, arrows=True)
    nx.draw_networkx_edge_labels(cfg, pos=pos, font_size=4)
    plt.axis("off")
    print(cprog)
    # plt.show()

    print(all_uses(cfg, 'X'))
    # print(check_no_assign_sub_path(cfg, [7, 8], 'X'))

    path = [1, 2, 1, 2, 1, 2]
    print(sub_paths(path, 1, 2))



    # print(get_var(cfg))
    # print(get_def(cfg))
    #print(get_ref(cfg))

    #for path in nx.all_simple_paths(cfg, source= "START", target="END"):
    #    print(path)
    # val = {'X': 10, 'Y': 0}
    # print(execution_path(cfg, val))
    #print(get_paths(cfg, 12))
    #print(get_paths_with_limited_loop(cfg, 1))
    #print(find_nested_loops(cfg))

    val = {'X': 10, 'Y': 0}
    conditions = get_all_conditions(cfg)
    print(conditions)
    print(get_conditions_values(cfg, val, conditions))
