from model.arithmexpr import *
from model.booleanexpr import *
from model.command import *

_p1 = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)),
               Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(2)), label=1),
               label=0)
_p2 = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1), label=3),
            Assign(ArithmVar('Y'), ArithmConst(-1), label=4), label=2)

prog = Sequence(_p1, _p2)

test = [{'X': -1, 'Y': 2},{'X': 0, 'Y': 2},{'X': 1, 'Y': 2}]

if __name__ == "__main__":
    print(prog)
