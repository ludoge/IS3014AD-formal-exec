from path_to_predicate import *
from predicate_solve import *
from model.cfg import *
from tests.tests import *


class TestGenerator:
    def __init__(self, prog):
        self.prog = prog
        self.cfg = ast_to_cfg_with_end(copy.deepcopy(prog))
        self.test = Test([])

    def findPaths(self):
        return {}

    def findTests(self, paths=None):
        """
        For each coverage condition given in find path, search for a solution for at least on of the paths given for
        this condition.
        """
        tests = []
        full_test = True
        if paths is None:
            paths = self.findPaths()
        for cover_name, possible_path in paths.items():
            solution_found = False
            for path in possible_path:
                vars, constraints = path_predicate(self.cfg, path)
                vars = {k for k, v in vars.items()}
                ps = PredicateSolver(vars, constraints)
                ps.add_constraints()
                solutions = ps.problem.getSolutions()
                if len(solutions) > 0:
                    tests.append(solutions[0])
                    solution_found = True
                    break
            if not solution_found:
                print(f'WARNING: No solution found for any path given for coverage condition {cover_name}')
                full_test = False
        return tests, full_test

    def findReducedTests(self):
        test_valuation, is_full_test = self.findTests()
        self.test.data = copy.deepcopy(test_valuation)
        max_score = self.test.runTests(copy.deepcopy(self.prog))
        current_score = 0
        minimum_test = []
        remaining_valuations = copy.deepcopy(test_valuation)
        while current_score < max_score:
            best_valuation = None
            best_score = 0
            for valuation in remaining_valuations:
                self.test.data = copy.deepcopy(minimum_test) + [copy.deepcopy(valuation)]
                score = self.test.runTests(copy.deepcopy(self.prog))
                if score > best_score:
                    best_score = score
                    best_valuation = copy.deepcopy(valuation)
            minimum_test.append(best_valuation)
            remaining_valuations = [valuation for valuation in remaining_valuations if valuation != best_valuation]
            current_score = best_score
        print(f"Test found for a coverage of {int(current_score*100)/100}%")
        return minimum_test


class TestTAGenerator(TestGenerator):
    def __init__(self, prog, max_loop=2):
        super().__init__(prog)
        self.max_loop = max_loop
        self.test = TestTA([])

    def findPaths(self):
        assign_labels = get_assigns(self.cfg)
        paths = {}
        for label in assign_labels:
            paths[f'<Assign {label}>'] = []
            for path in get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', label):
                paths[f'<Assign {label}>'].append(path)
        return paths


class TestTDGenerator(TestGenerator):
    def __init__(self, prog, max_loop=2):
        super().__init__(prog)
        self.max_loop = max_loop
        self.test = TestTD([])

    def findPaths(self):
        decision_labels = get_all_conditions(self.cfg).keys()
        paths = {}
        for label in decision_labels:
            neighbors = list(self.cfg.neighbors(label))
            paths[f'<Decision {label} True>'] = []
            for path in get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', neighbors[0]):
                paths[f'<Decision {label} True>'].append(path)
            paths[f'<Decision {label} False>'] = []
            for path in get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', neighbors[1]):
                paths[f'<Decision {label} False>'].append(path)
        return paths


class TestkTCGenerator(TestGenerator):
    def __init__(self, prog, k):
        super().__init__(prog)
        self.k = k
        self.test = TestkTC([], k)

    def findPaths(self):
        all_k_paths = get_paths(self.cfg, self.k)
        paths = {}
        for i in range(len(all_k_paths)):
            paths[f'<{self.k}-path n° {i}>'] = [all_k_paths[i]]
        return paths


class TestiTBGenerator(TestGenerator):
    def __init__(self, prog, i):
        super().__init__(prog)
        self.i = i
        self.test = TestiTB([], i)

    def findPaths(self):
        all_i_loops = get_paths_with_limited_loop(self.cfg, self.i)
        paths = {}
        for i in range(len(all_i_loops)):
            paths[f'<{self.i}-loop path n° {i}>'] = [all_i_loops[i]]
        return paths


class TestTDefGenerator(TestGenerator):
    def __init__(self, prog, max_loop=2):
        super().__init__(prog)
        self.max_loop = max_loop
        self.test = TestTDef([])

    def findPaths(self):
        var_list = get_var(self.cfg)
        paths = {}
        for variable in var_list:
            pairs = all_uses(self.cfg, variable)
            ref_by_def = {}
            for pair in pairs:
                if pair[0] in ref_by_def:
                    ref_by_def[pair[0]].append(pair[1])
                else:
                    ref_by_def[pair[0]] = [pair[1]]
                for def_label in ref_by_def:
                    paths[f'<Def {def_label}>'] = []
                    for ref_label in ref_by_def[def_label]:
                        for path1 in get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', def_label):
                            for path2 in get_paths_with_limited_loop(self.cfg, self.max_loop, def_label, ref_label):
                                paths[f'<Def {def_label}>'].append(path1 + path2[1:])
        return paths

    def findTests(self, paths=None):
        full_test = True
        var_labels = get_assigns(self.cfg)
        if paths is None:
            paths = self.findPaths()
        for label in var_labels:
            if f'<Def {label}>' not in paths or len(paths[f'<Def {label}>']) == 0:
                print(f'WARNING: No reference found after assign {label}')
                full_test = False
        test, is_full_test = TestGenerator.findTests(self, paths)
        return test, is_full_test and full_test


class TestTUGenerator(TestGenerator):
    def __init__(self, prog, max_loop=2):
        super().__init__(prog)
        self.max_loop = max_loop
        self.test = TestTU([])

    def findPaths(self):
        var_list = get_var(self.cfg)
        paths = {}
        for variable in var_list:
            pairs = all_uses(self.cfg, variable)
            for pair in pairs:
                paths[f'<Ref {pair[1]} for Ref {pair[0]}>'] = []
                for path1 in get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', pair[0]):
                    for path2 in get_paths_with_limited_loop(self.cfg, self.max_loop, pair[0], pair[1]):
                        paths[f'<Ref {pair[1]} for Ref {pair[0]}>'].append(path1 + path2[1:])
        return paths


class TestDUGenerator(TestGenerator):
    def __init__(self, prog, max_loop=2):
        super().__init__(prog)
        self.max_loop = max_loop
        self.test = TestDU([])

    def findPaths(self):
        var_list = get_var(self.cfg)
        paths = {}
        for variable in var_list:
            pairs = all_uses(self.cfg, variable)
            for pair in pairs:
                # Between the two labels of the pair, we only allow simple paths, and each simple path has its own entry
                # in the paths dictionary.
                i = 0
                for path2 in get_paths_with_limited_loop(self.cfg, 1, pair[0], pair[1]):
                    paths[f'<Ref {pair[1]} for Ref {pair[0]} - path n°{i}>'] = []
                    # Before the first label of the pair, we allow max_loop loops to get all possible way to reach the
                    # simple path.
                    for path1 in get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', pair[0]):
                        paths[f'<Ref {pair[1]} for Ref {pair[0]} - path n°{i}>'].append([path1 + path2[1:]])
                    i += 1
        return paths


class TestTCGenerator(TestGenerator):
    def __init__(self, prog, max_loop=2):
        super().__init__(prog)
        self.max_loop = max_loop
        self.test = TestTC([])
        self.conditions = {}

    def findPaths(self):
        self.conditions = get_all_conditions(self.cfg)
        paths = {}
        for label in self.conditions.keys():
            paths[f'<Conditions {label}>'] = get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', label)
        return paths

    def findTests(self, paths=None):
        tests = []
        full_test = True
        if paths is None:
            paths = self.findPaths()
        for label in self.conditions:
            for condition in self.conditions[label]:
                for cond_value in [True, False]:
                    condition_string = str(condition)
                    if not cond_value:
                        condition_string = str(BooleanUnaryExp("!", condition))
                    solution_found = False
                    for path in paths[f'<Conditions {label}>']:
                        vars, constraints = path_predicate(self.cfg, path)
                        new_condition_string = condition_string
                        for var in vars:
                            new_condition_string = new_condition_string.replace(var, vars[var])
                        constraints.add(new_condition_string)
                        vars = {k for k, v in vars.items()}
                        ps = PredicateSolver(vars, constraints)
                        ps.add_constraints()
                        solutions = ps.problem.getSolutions()
                        if len(solutions) > 0:
                            tests.append(solutions[0])
                            solution_found = True
                            break
                    if not solution_found:
                        print(f'WARNING: No solution found for any path given for coverage condition <Label {label} Condition {condition} Value {cond_value}>')
                        full_test = False

        return tests, full_test


if __name__ == '__main__':
    p1 = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)),
               Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1),
               label=0)
    p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1), label=3),
            Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)

    ast = Sequence(p1, p2)

    p3 = While(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)),
               Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1),
               label=0)
    p4 = If(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1), label=3),
            Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)

    wrong_ast = Sequence(p3, p4)

    """
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
    """

    print(ast)

    print("\n\nTest TA\n")

    print("Solution program 1")
    test_generator = TestTAGenerator(ast)
    solutionTA = test_generator.findReducedTests()
    print(solutionTA)

    print("Solution program 2")
    test_generator = TestTAGenerator(wrong_ast)
    wrongSolutionTA = test_generator.findReducedTests()
    print(wrongSolutionTA)


    print("\n\nTest TD\n")

    print("Solution program 1")
    test_generator = TestTDGenerator(ast)
    solutionTD = test_generator.findReducedTests()
    print(solutionTD)

    print("Solution program 2")
    test_generator = TestTDGenerator(wrong_ast)
    wrongSolutionTD = test_generator.findReducedTests()
    print(wrongSolutionTD)


    print("\n\nTest k-TC\n")

    print("Solution program 1")
    test_generator = TestkTCGenerator(ast, 6)
    solutionkTC = test_generator.findReducedTests()
    print(solutionkTC)

    print("Solution program 2")
    test_generator = TestkTCGenerator(wrong_ast, 6)
    wrongSolutionkTC = test_generator.findReducedTests()
    print(wrongSolutionkTC)


    print("\n\nTest i-TB\n")

    print("Solution program 1")
    test_generator = TestiTBGenerator(ast, 2)
    solutioniTB = test_generator.findReducedTests()
    print(solutioniTB)

    print("Solution program 2")
    test_generator = TestiTBGenerator(wrong_ast, 2)
    wrongSolutioniTB = test_generator.findReducedTests()
    print(wrongSolutioniTB)


    print("\n\nTest TDef\n")

    print("Solution program 1")
    test_generator = TestTDefGenerator(ast)
    solutionTDef = test_generator.findReducedTests()
    print(solutionTDef)

    print("Solution program 2")
    test_generator = TestTDefGenerator(wrong_ast)
    wrongSolutionTDef = test_generator.findReducedTests()
    print(wrongSolutionTDef)


    print("\n\nTest TU\n")

    print("Solution program 1")
    test_generator = TestTUGenerator(ast)
    solutionTU = test_generator.findReducedTests()
    print(solutionTU)

    print("Solution program 2")
    test_generator = TestTUGenerator(wrong_ast)
    wrongSolutionTU = test_generator.findReducedTests()
    print(wrongSolutionTU)


    print("\n\nTest DU\n")

    print("Solution program 1")
    test_generator = TestDUGenerator(ast)
    solutionDU = test_generator.findReducedTests()
    print(solutionDU)

    print("Solution program 2")
    test_generator = TestDUGenerator(wrong_ast)
    wrongSolutionDU = test_generator.findReducedTests()
    print(wrongSolutionDU)

    print("\n\nTest TC\n")

    print("Solution program 1")
    test_generator = TestTCGenerator(ast)
    solutionTC = test_generator.findReducedTests()
    print(solutionTC)

    print("Solution program 2")
    test_generator = TestTCGenerator(wrong_ast)
    wrongSolutionTC = test_generator.findReducedTests()
    print(wrongSolutionTC)
