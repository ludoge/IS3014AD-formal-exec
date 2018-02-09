from path_to_predicate import *
from predicate_solve import *
from model.cfg import *


class TestGenerator:
    def __init__(self, prog):
        self.cfg = ast_to_cfg_with_end(prog)

    def findPaths(self):
        return {}

    def findTests(self):
        """
        For each coverage condition given in find path, search for a solution for at least on of the paths given for
        this condition.
        """
        tests = []
        for cover_name, possible_path in self.findPaths().items():
            for path in possible_path:
                vars, constraints = path_predicate(self.cfg, path)
                vars = {k for k, v in vars.items()}
                ps = PredicateSolver(vars, constraints)
                ps.add_constraints()
                solutions = ps.problem.getSolutions()
                if len(solutions) > 0:
                    tests.append(solutions[0])
                    break
            print(f'No solution found for any path given for coverage condition {cover_name}')
            return None
        return tests


class TestTAGenerator(TestGenerator):
    def __init__(self, prog, max_loop=2):
        super().__init__(prog)
        self.max_loop = max_loop

    def findPaths(self):
        assign_labels = get_assigns(self.cfg)
        paths = {}
        for label in assign_labels:
            paths[f'<Assign {label}>'] = []
            for path in get_paths_with_limited_loop(self.cfg, self.max_loop, 'START', label):
                paths[f'<Assign {label}>'].append(path)
                print(path)
            print(f'<Assign {label}>')
            print(len(paths[f'<Assign {label}>']))
        return paths



if __name__ == '__main__':
    p1 = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)),

               Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1),
               label=0)
    p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1), label=3),
            Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)

    ast = Sequence(p1, p2)

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

    test_generator = TestTAGenerator(ast, 2)
    print(test_generator.findTests())
