from model.arithmexpr import *
from model.booleanexpr import *
from model.command import *



_p3 = Assign(
    ArithmVar('A'),
    ArithmBinExp('-', ArithmVar('A'), ArithmVar('B')),
    label=3)

_p4 = Assign(
    ArithmVar('B'),
    ArithmBinExp('-', ArithmVar('B'), ArithmVar('A')),
    label=4)

_p2 = If(
    BooleanBinaryExp('>', ArithmVar('A'), ArithmVar('B')),
    _p3,
    _p4,
    label=2)

_p1 = While(
    BooleanBinaryExp('!=', ArithmVar('A'), ArithmVar('B')),
    _p2,
    label=1)

_p0 = If(
    BooleanBinaryExp('&&',
                     BooleanBinaryExp('>', ArithmVar('A'), ArithmConst(0)),
                     BooleanBinaryExp('>', ArithmVar('B'), ArithmConst(0))
                     ),
    _p1,
    Skip(),
    label=0)

prog = _p0

test = [{'A': 30, 'B': 9}, {'A': 0, 'B': 10}, {'A': 20, 'B': 20}, {'A': 8, 'B': 4}]

if __name__ == "__main__":
    print(prog)
