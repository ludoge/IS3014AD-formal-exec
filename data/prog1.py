from model.arithmexpr import *
from model.booleanexpr import *
from model.command import *

_p1 = Assign(
    ArithmVar('C'),
    ArithmConst(1),
    label=1)

_p3 = Assign(
    ArithmVar('C'),
    ArithmBinExp('%', ArithmVar('A'), ArithmVar('B')),
    label=3)

_p4 = Assign(
    ArithmVar('A'),
    ArithmVar('B'),
    label=4)

_p5 = Assign(
    ArithmVar('B'),
    ArithmVar('C'),
    label=5)

_p2 = While(
    BooleanBinaryExp('!=', ArithmVar('C'), ArithmConst(0)),
    Sequence(_p3, Sequence(_p4, _p5)),
    label=2)

_p0 = If(
    BooleanBinaryExp('&&',
                     BooleanBinaryExp('>=', ArithmVar('A'), ArithmConst(0)),
                     BooleanBinaryExp('>', ArithmVar('B'), ArithmConst(0))
                     ),
    Sequence(_p1, _p2),
    Skip(),
    label=0)

prog = _p0

test = [{'A': 20, 'B': 15, 'C': 12}, {'A': -2, 'B': -2, 'C': -2}, {'A': 10, 'B': 10, 'C': 10}]

if __name__ == "__main__":
    print(prog)
