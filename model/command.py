from anytree import AnyNode


class WhileNode(AnyNode):
    """
    Functions common to all node types are defined here
    """
    def get_labels(self, typename=None):
        labels = set([])
        if self.label is not None and (typename == self.typename or typename is None):
            labels = set([self.label])
        for command in list(self.children):
            try:
                sub_labels = command.get_labels(typename)
                if sub_labels is not None:
                    labels = set(list(labels) + list(sub_labels))
            except AttributeError:
                pass
        return labels

    def get_variables(self):
        variables = set([])
        try:
            print(self.name)
            variables = set([self.name])
        except AttributeError:
            pass
        for child in list(self.children):
            try:
                sub_variables = child.get_variables()
                if sub_variables is not None:
                    variables = set(list(variables) + list(sub_variables))
            except AttributeError:
                pass
        return variables

    def exec_path(self, values):
        path=[]
        self.exec(values=values ,path=path)
        return path


class Command(WhileNode):
    def __init__(self, label=None):
        super().__init__()
        self.typename = "Command"
        if label is not None:
            self.label = label
        else:
            self.label = ''

    def __repr__(self):
        return f"{self.label}: {self.typename}"


class Skip(Command):
    def __init__(self, label=None):
        super().__init__()
        self.typename = "Skip"

    def exec(self, values={}, path=[]):
        if self.label is not None:
            path.append(self.label)
        return values

class Assign(Command):
    def __init__(self, variable, expression, label=None):
        super().__init__(label=label)
        self.typename = "Assign"
        variable.parent = self
        expression.parent = self

    def exec(self, values={}, path=[]):
        if self.label is not None:
            path.append(self.label)
        variable = self.children[0]
        expression = self.children[1]
        values[variable.name] = expression.eval(values)
        return values

    def __repr__(self):
        return f"{self.label}: {self.children[0]}:= {self.children[1]}"


class Sequence(Command):
    def __init__(self, command1, command2):
        super().__init__()
        self.typename = "Sequence"
        command1.parent = self
        command2.parent = self

    def exec(self, values={}, path=[]):
        if self.label is not None:
            path.append(self.label)
        for command in list(self.children):
            values = command.exec(values, path)
        return values

    def __repr__(self):
        return "\n".join(map(repr,list(self.children)))


class If(Command):
    def __init__(self, expr, thencommand, elsecommand=Skip(), label=None):
        super().__init__(label=label)
        self.typename = "If"
        expr.parent = self
        thencommand.parent = self
        elsecommand.parent = self

    def exec(self, values={}, path=[]):
        if self.label is not None:
            path.append(self.label)
        expr = self.children[0]
        thencommand = self.children[1]
        elsecommand = self.children[2]

        if expr.eval(values):
            return thencommand.exec(values=values, path=path)
        else:
            return elsecommand.exec(values=values, path=path)

    def __repr__(self):
        return f"{self.label}: If {self.children[0]}:\n\t" + "\n\t".join(repr(self.children[1]).split('\n'))+"\nelse:\n\t" + "\n\t".join(repr(self.children[2]).split('\n'))


class While(Command):
    def __init__ (self, expr, command, label=None):
        super().__init__(label=label)
        self.typename = "While"
        expr.parent=self
        command.parent=self

    def exec(self, values={}, path=[]):
        if self.label is not None:
            path.append(self.label)
        expr = self.children[0]
        command = self.children[1]

        while expr.eval(values):
            values = command.exec(values=values, path=path)

        return values

    def __repr__(self):
        return f"{self.label}: While {self.children[0]}: \n\t" + "\n\t".join(repr(self.children[1]).split('\n'))


if __name__ == '__main__':
    import os, sys
    sys.path.insert(1, os.path.join(sys.path[0], '..'))
    from model.arithmexpr import *
    from model.booleanexpr import *
    from anytree import RenderTree

    ast = If(BooleanBinaryExp('>=', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('Y'), ArithmConst(1),label=2), label=1)
    print(RenderTree(ast))

    val = {'X': 10, 'Y': 0}

    print(ast.exec(val))
    print(ast.get_labels())
    print(ast.get_labels('Assign'))
    print(ast.get_labels('If'))
    print(ast.get_variables())

    p = []
    ast = While(BooleanBinaryExp('>', ArithmVar('X'), ArithmConst(0)), Assign(ArithmVar('X'), ArithmBinExp('-', ArithmVar('X'), ArithmConst(1)), label=1), label=0)

    print(ast.get_labels("While"))
    print(ast.get_variables())
    print(ast.exec_path(val))



