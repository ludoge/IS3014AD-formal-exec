from collections import Counter
from model.arithmexpr import *
from model.booleanexpr import *
from model.command import *
from model.cfg import *

import networkx as nx


class Test(object):
    def __init__(self, data):
        self.data = data


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
                    print(f"{value} covers assignment {a}")
                    if a not in covered_assignments:
                        covered_assignments.append(a)

        percent_coverage = 100*len(covered_assignments)/len(assignments)
        print(f"Test data covers {percent_coverage}% of assignments")


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
                    print(f"{value} covers decision {d}")
                    if d not in covered_decisions:
                        covered_decisions.append(d)

        percent_coverage = 100*len(covered_decisions)/len(decisions)
        print(f"Test data covers {percent_coverage}% of decisions")


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
                print(f"{value} covers {self.k}-path {path}")
                if path not in covered_k_paths:
                    covered_k_paths.append(path)

        percent_coverage = 100*len(covered_k_paths)/len(k_paths)
        print(f"Test data covers {percent_coverage}% of {self.k}-paths")


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
                print(f"{value} covers {self.i}-loops {path}")
                if path not in covered_i_loops:
                    covered_i_loops.append(path)

        percent_coverage = 100*len(covered_i_loops)/len(i_loops)
        print(f"Test data covers {percent_coverage}% of {self.i}-loops")


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
                print(f"{value} covers definition {a}")
                if a not in covered_definitions:
                    covered_definitions.append(a)

        percent_coverage = 100 * len(covered_definitions) / len(definitions)
        print(f"Test data covers {percent_coverage}% of definitions")


if __name__ == '__main__':
    from anytree import RenderTree

    #ast = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1),label=2), label=1)

    p1 = ast = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)),
                     Sequence(Assign(ArithmVar('X'), ArithmBinExp('+', ArithmVar('X'), ArithmConst(1)), label=0.5),
                              Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1)),
                     label=0)
    p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1), label=3),
            Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)

    ast = Sequence(p1, p2)

    #print(RenderTree(ast))
    values = [{'X': -1, 'Y': 2},{'X': 0, 'Y': 2},{'X': 1, 'Y': 2}]

    #testTA = TestTA(values)
    #testTA.runTests(ast)

    #testTD = TestTD(values)
    #testTD.runTests(ast)

    #testkTC = TestkTC(values, 6)
    #testkTC.runTests(ast)

    #testiTB = TestiTB(values, 1)
    #testiTB.runTests(ast)

    testTDef = TestTDef(values)
    testTDef.runTests(ast)
