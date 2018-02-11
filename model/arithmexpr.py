from anytree import AnyNode
from model.command import WhileNode

class ArithmExp(WhileNode):
    def __init__(self):
        super().__init__()
        self.typename = "ArithmExp"


class ArithmConst(ArithmExp):
    def __init__(self, value):
        super().__init__()
        self.typename = "ArithmConst"
        self.value = value

    def eval(self, values={}):
        return self.value

    def __repr__(self):
        return str(self.value)

class ArithmVar(ArithmExp):
    def __init__(self, name):
        super().__init__()
        self.typename = "ArithmVar"
        self.name = name

    def eval(self, values={}):
        return values[self.name]

    def __repr__(self):
        return self.name


class ArithmBinExp(ArithmExp):

    OPERATORS = {
        '+': '__add__',
        '-': '__sub__',
        '*': '__mul__',
        '//': '__floordiv__',
        '%': '__mod__',
        '**': '__pow__',
    }

    def __init__(self, operator, left, right):
        super().__init__()
        self.typename = "ArithmBinOP"
        self.operator = operator
        left.parent = self
        right.parent = self

    def eval(self, values={}):
        return getattr(self.children[0].eval(values), self.OPERATORS[self.operator])(self.children[1].eval(values))

    def __repr__(self):
        return f"({self.children[0])}) {self.operator} ({repr(self.children[1])})"


class ArithmUnaryExp(ArithmExp):

    OPERATORS = {
        '-': '__neg__'
    }

    def __init__(self, operator, exp):
        super().__init__()
        self.typename = "ArithmUnaryExp"
        self.operator = operator
        exp.parent = self

    def eval(self, values={}):
        return getattr(self.children[0].eval(values), self.OPERATORS[self.operator])()

    def __repr__(self):
        return f"{self.operator} ({repr(self.children[0])})"

if __name__ == '__main__':
    from anytree import RenderTree
    ast = ArithmBinExp('+', ArithmVar('X'), ArithmUnaryExp('-', ArithmConst(2)))
    print(RenderTree(ast))
    print(ast.eval({'X': 3}))
