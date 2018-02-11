from anytree import AnyNode
from model.command import WhileNode


class BooleanExp(WhileNode):
    def __init__(self):
        super().__init__()
        self.typename = "BooleanExp"


class BooleanConst(BooleanExp):
    def __init__(self, value):
        super().__init__()
        self.typename = "BooleanConst"
        self.value = value

    def eval(self, values={}):
        return self.value

    def __repr__(self):
        return str(self.value)

class BooleanVar(BooleanExp):
    def __init__(self, name):
        super().__init__()
        self.typename = "BooleanVar"
        self.name = name

    def eval(self, values):
        return values[self.name]

    def __repr__(self):
        return self.name


class BooleanBinaryExp(BooleanExp):
    OPERATORS = {
        '&&': '__and__',
        '||': '__or__',
        '^':  '__xor__',
        '==': '__eq__',
        '!=': '__ne__',
        '<':  '__lt__',
        '<=': '__le__',
        '>':  '__gt__',
        '>=': '__ge__',
    }

    def __init__(self, operator, left, right):
        super().__init__()
        self.typename = "BooleanBinaryExp"
        self.operator = operator
        left.parent = self
        right.parent = self

    def eval(self, values={}):
        return getattr(self.children[0].eval(values), self.OPERATORS[self.operator])( self.children[1].eval(values))

    def __repr__(self):
        return repr(self.children[0]) + self.operator + repr(self.children[1])


class BooleanUnaryExp(BooleanExp):
    def __init__(self, operator, exp):
        super().__init__()
        self.typename = "BooleanUnaryExp"
        self.operator = operator
        exp.parent = self

    def eval(self, values ={}):
        return not self.children[0].eval(values)

    def __repr__(self):
        return "! "+" ".join(map(repr, self.children))


if __name__ == '__main__':
    testconst1 = BooleanConst(True)
    testconst2 = BooleanConst(False)
    print(testconst1.eval())
    testbin = BooleanBinaryExp('>=', testconst1, testconst2)
    print(testbin.eval())