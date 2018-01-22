from model.arithmexpr import *
from model.booleanexpr import *
from model.command import *
from model.cfg import *


class Test(object):
    def __init__(self, data):
        self.data = data


class TestTA(Test):
    def __init__(self, data):
        super().__init__(data)

    def runTests(self, prog):
        cfg = ast_to_cfg_with_end(prog)
        assignments = []
        for u,v in cfg.edges:
            if cfg[u][v]['command'].typename == "Assign":
                assignments.append(cfg[u][v]['command'].label)




if __name__ == '__main__':
    from anytree import RenderTree

    ast = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1),label=2), label=1)
    print(RenderTree(ast))
    values = [{'X': -1, 'Y': 2}]

    testTA = TestTA(values)
    print(testTA.runTests(ast))