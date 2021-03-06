from collections import Counter
from model.arithmexpr import *
from model.booleanexpr import *
from model.command import *
from model.cfg import *

import networkx as nx


class Test(object):
    def __init__(self, data):
        self.data = data
        self.print_missing = False


class TestTA(Test):
    def __init__(self, data):
        super().__init__(data)

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)
        assignments = []
        covered_assignments = []
        for u, v in cfg.edges:
            if cfg[u][v]['command'].typename == "Assign":
                assignments.append(cfg[u][v]['command'].label)

        for value in self.data:
            path = execution_path(cfg, value)
            for a in assignments:
                if a in path:
                    #print(f"{value} covers assignment {a}")
                    if a not in covered_assignments:
                        covered_assignments.append(a)

        percent_coverage = 100*len(covered_assignments)/len(assignments)
        if self.print_missing:
            for assignment in assignments:
                if assignment not in covered_assignments:
                    print(f"Assignment {assignment} not covered.")
        return percent_coverage


class TestTD(Test):
    def __init__(self, data):
        super().__init__(data)

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)

        decisions = []
        covered_decisions = []

        for u in cfg.nodes:
            # decisions are branches
            if len(list(nx.neighbors(cfg, u))) == 2:
                for v in nx.neighbors(cfg, u):
                    decisions.append((u,v))

        for value in self.data:
            path = execution_path(cfg, value)
            path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
            for d in decisions:
                if d in path_edges:
                    #print(f"{value} covers decision {d}")
                    if d not in covered_decisions:
                        covered_decisions.append(d)

        percent_coverage = 100*len(covered_decisions)/len(decisions)
        if self.print_missing:
            for decision in decisions:
                if decision not in covered_decisions:
                    print(f"Decision {decision} not covered.")
        return percent_coverage


class TestkTC(Test):
    def __init__(self, data, k):
        super().__init__(data)
        self.k = k

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)

        k_paths = get_paths(cfg, self.k)
        covered_k_paths = []

        for value in self.data:
            path = execution_path(cfg, value)
            if path in k_paths:
                #print(f"{value} covers {self.k}-path {path}")
                if path not in covered_k_paths:
                    covered_k_paths.append(path)

        percent_coverage = 100*len(covered_k_paths)/len(k_paths)
        if self.print_missing:
            for path in k_paths:
                if path not in covered_k_paths:
                    print(f"Path {path} not covered.")
        return percent_coverage


class TestiTB(Test):
    def __init__(self, data, i):
        super().__init__(data)
        self.i = i

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)

        i_loops = get_paths_with_limited_loop(cfg, self.i)
        covered_i_loops = []

        for value in self.data:
            path = execution_path(cfg, value)
            if path in i_loops:
                #print(f"{value} covers {self.i}-loops {path}")
                if path not in covered_i_loops:
                    covered_i_loops.append(path)

        percent_coverage = 100*len(covered_i_loops)/len(i_loops)
        if self.print_missing:
            for path in i_loops:
                if path not in covered_i_loops:
                    print(f"Path {path} not covered.")
        return percent_coverage


class TestTDef(Test):
    def __init__(self, data):
        super().__init__(data)

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)

        definitions = get_assigns(cfg)
        covered_definitions = []

        for value in self.data:
            path = execution_path(cfg, value)
            covered_definitions_in_path = get_assigns_with_next_reference(cfg, path)
            for a in covered_definitions_in_path:
                #print(f"{value} covers definition {a}")
                if a not in covered_definitions:
                    covered_definitions.append(a)

        percent_coverage = 100 * len(covered_definitions) / len(definitions)
        if self.print_missing:
            for definition in definitions:
                if definition not in covered_definitions:
                    print(f"Definition {definition} not covered.")
        return percent_coverage


class TestTU(Test):
    def __init__(self, data):
        super().__init__(data)

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)
        variables = get_var(cfg)
        pairs = set()
        covered_pairs = set()
        au = defaultdict(set)
        for variable in variables:
            au[variable].update(all_uses(cfg, variable))
            pairs.update(au[variable])
        for value in self.data:
            path = execution_path(cfg, value)
            for variable in variables:
                for (u, v) in au[variable]:
                    for sp in sub_paths(path, u, v):
                        if check_no_assign_sub_path(cfg, sp, variable):
                            covered_pairs.update([(u, v)])
                            #print(f"Subpath {sp} covers use {u,v}")
        percent_coverage = 100 * len(covered_pairs) / len(pairs)
        if self.print_missing:
            for pair in pairs:
                if pair not in covered_pairs:
                    print(f"Pair Def-Ref {pair} not covered.")
        return percent_coverage


class TestDU(Test):
    def __init__(self, data):
        super().__init__(data)

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)
        variables = get_var(cfg)
        simple_path_pairs = {}
        simple_paths = []
        for variable in variables:
            simple_path_pairs[variable] = all_uses(cfg, variable)
            for (u, v) in simple_path_pairs[variable]:
                for path in get_paths_with_limited_loop(cfg, 1, u, v):
                    if path not in simple_paths and check_no_assign_sub_path(cfg, path, variable):
                        simple_paths.append(path)
        covered_simple_paths = []
        for value in self.data:
            path = execution_path(cfg, value)
            for variable in variables:
                for (u, v) in simple_path_pairs[variable]:
                    for sp in sub_paths(path, u, v):
                        if sp in simple_paths:
                            #print(f"Subpath {sp} is covered")
                            if sp not in covered_simple_paths:
                                covered_simple_paths.append(sp)
        percent_coverage = 100 * len(covered_simple_paths) / len(simple_paths)
        if self.print_missing:
            for path in simple_paths:
                if path not in covered_simple_paths:
                    print(f"Simple path {path} not covered.")
        return percent_coverage


class TestTC(Test):
    def __init__(self, data):
        super().__init__(data)

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)
        conditions = get_all_conditions(cfg)
        all_conditions = [(label, cond_expr, value) for label in conditions for cond_expr in conditions[label] for value in [True, False]]
        covered_conditions = []
        for value in self.data:
            for cond in get_conditions_values(cfg, value, conditions):
                #print(f"Condition {cond[1]} is evaluated to {cond[2]} at label {cond[0]}")
                if cond not in covered_conditions and cond in all_conditions:
                    covered_conditions.append(cond)

        percent_coverage = 100 * len(covered_conditions) / len(all_conditions)
        if self.print_missing:
            for condition in all_conditions:
                if condition not in covered_conditions:
                    print(f"Condition {condition} not covered.")
        return percent_coverage


if __name__ == '__main__':
    from anytree import RenderTree

    #ast = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1),label=2), label=1)

    p1 = ast = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)),
                              Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1),
                     label=0)
    p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1), label=3),
            Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)

    ast = Sequence(p1, p2)

    #print(RenderTree(ast))
    values = [{'X': -1, 'Y': 2},{'X': 0, 'Y': 2},{'X': 1, 'Y': 2}]

    # testTA = TestTA(values)
    # testTA.runTests(ast)

    #testTD = TestTD(values)
    #testTD.runTests(ast)

    #testkTC = TestkTC(values, 6)
    #testkTC.runTests(ast)

    #testiTB = TestiTB(values, 1)
    #testiTB.runTests(ast)

    # testTDef = TestTDef(values)
    # testTDef.runTests(ast)

    #testTU = TestTU(values)
    #print(testTU.runTests(ast))

    testDU = TestDU(values)
    print(testDU.runTests(ast))

    #testTC = TestTC(values)
    #testTC.runTests(ast)
