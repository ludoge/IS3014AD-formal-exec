from collections import defaultdict
from constraint import *
from path_to_predicate import *
import ast


class PredicateSolver(object):
    def __init__(self, vars=set(), constraints=set()):
        self.problem = Problem()
        self.vars = vars
        for v in vars:
            self.problem.addVariable(v, range(-100, 100))
        self.constraints = constraints

    def add_constraint(self, constraint):
        expr = constraint[:]
        L = list(self.vars)
        for i in range(len(L)):
            expr = expr.replace(L[i], f'args[{i}]')
        expr = expr.replace("!", 'not')
        #print(expr)

        def func(*args):
            return eval(expr)

        self.problem.addConstraint(func, self.vars)

    def add_constraints(self):
        for cons in self.constraints:
            self.add_constraint(cons)


if __name__ == '__main__':
    problem = Problem()
    known_vars = {'X', 'Y'}

    ps = PredicateSolver(vars=known_vars, constraints={'X-2-2-2>=0', 'X<0'})

    # problem.addConstraint(lambda X, Y: X-2-2-2 >=0)
    # problem.addConstraint(ps.testf,('X', 'Y'))
    ps.add_constraints()

    print(ps.problem.getSolutions())
