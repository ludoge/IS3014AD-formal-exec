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
            cfg, temp_edges = ast_to_cfg(command, cfg=cfg, previous_edges=temp_edges)
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
    return  paths


def get_paths(cfg, k, u='START', v='END'):
    if k == 0:
        return []
    return [path for path in get_paths_exact(cfg, k+1, u) if path[-1] == v] + get_paths(cfg, k-1, u, v)


def get_paths_with_limited_loop(cfg, i, u='START', v='END', visited={}):
    """
    Finds all paths with at most i loops for each 'While' starting from u recursively
    """
    if u == v:
        return [[u]]

    try:
        visited[u] += 1
    except KeyError:
        visited[u] = 1

    if visited[u] > i + 1:
        return []
    return [[u] + path for neighbor in cfg.neighbors(u) for path in get_paths_with_limited_loop(cfg, i, neighbor, v, visited) if path != []]


if __name__ == '__main__':
    from anytree import RenderTree
    p1 = ast = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)), Sequence(Assign(ArithmVar('X'), ArithmBinExp('+', ArithmVar('X'), ArithmConst(1)), label=0.5), Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)),label=1)), label=0)
    p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1),label=3), Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)
    #p1 = If(BooleanBinaryExp('<=',ArithmVar('X'),ArithmConst(0)), Assign(ArithmVar('X'),ArithmUnaryExp("-",ArithmVar('X')),label=2), Assign(ArithmVar('X'), ArithmBinExp("-", ArithmConst(1), ArithmVar('X')), label=3), label=1)
    #p2 = If(BooleanBinaryExp('==',ArithmVar('X'),ArithmConst(1)), Assign(ArithmVar('X'),ArithmConst(1),label=5), Assign(ArithmVar('X'), ArithmBinExp("+", ArithmVar('X'), ArithmConst(1)), label=6), label=4)
    #print(p1)
    prog = Sequence(p1, p2)
    cprog = copy.deepcopy(prog)
    #prog = Sequence(p2, p1)
    #print(RenderTree(prog))
    #print(prog)

    cfg = ast_to_cfg_with_end(prog)
    #for u,v in cfg.edges:
    #    print(cfg[u][v]['command'].typename)
    pos = nx.nx_pydot.pydot_layout(cfg)
    nx.draw_networkx(cfg, pos=pos, arrows=True)
    nx.draw_networkx_edge_labels(cfg, pos=pos, font_size=4)
    plt.axis("off")
    plt.show()


    print(cprog)
    print(get_var(cfg))
    print(get_def(cfg))
    print(get_ref(cfg))

    #for path in nx.all_simple_paths(cfg, source= "START", target="END"):
    #    print(path)
    val = {'X': 10, 'Y': 0}
    print(execution_path(cfg, val))
    print(get_paths(cfg, 12))
    print(get_paths_with_limited_loop(cfg, 1))
