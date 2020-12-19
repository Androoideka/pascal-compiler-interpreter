class Node:
    pass


class Program(Node):
    def __init__(self, nodes):
        self.nodes = nodes


class Decl(Node):
    def __init__(self, type_, id_):
        self.type_ = type_
        self.id_ = id_


class ArrayDecl(Node):
    def __init__(self, type_, id_, start, end, elems):
        self.type_ = type_
        self.id_ = id_
        self.start = start
        self.end = end
        self.elems = elems


class ArrayElem(Node):
    def __init__(self, id_, index):
        self.id_ = id_
        self.index = index


class Assign(Node):
    def __init__(self, id_, expr):
        self.id_ = id_
        self.expr = expr


class If(Node):
    def __init__(self, cond, true, false):
        self.cond = cond
        self.true = true
        self.false = false


class While(Node):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block


class Repeat(Node):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block


class For(Node):
    def __init__(self, init, cond, block):
        self.init = init
        self.cond = cond
        self.block = block


class FuncImpl(Node):
    def __init__(self, type_, id_, params, varblock, execblock):
        self.type_ = type_
        self.id_ = id_
        self.params = params
        self.varblock = varblock
        self.execblock = execblock


class FuncCall(Node):
    def __init__(self, id_, args):
        self.id_ = id_
        self.args = args


class Vars(Node):
    def __init__(self, nodes):
        self.nodes = nodes


class Block(Node):
    def __init__(self, nodes):
        self.nodes = nodes


class Params(Node):
    def __init__(self, params):
        self.params = params


# https://wiki.freepascal.org/Formatting_output
class Args(Node):
    def __init__(self, args, field_widths, decimal_field_widths):
        self.args = args
        self.field_widths = field_widths
        self.decimal_field_widths = decimal_field_widths


class Elems(Node):
    def __init__(self, elems):
        self.elems = elems


class Break(Node):
    pass


class Continue(Node):
    pass


class Exit(Node):
    def __init__(self, expr):
        self.expr = expr


class Return(Node):
    def __init__(self, expr):
        self.expr = expr


class Type(Node):
    def __init__(self, value):
        self.value = value


class Integer(Node):
    def __init__(self, value):
        self.value = value


class Real(Node):
    def __init__(self, value):
        self.value = value


class Boolean(Node):
    def __init__(self, value):
        self.value = value


class Char(Node):
    def __init__(self, value):
        self.value = value


class String(Node):
    def __init__(self, value):
        self.value = value


class Id(Node):
    def __init__(self, value):
        self.value = value


class BinOp(Node):
    def __init__(self, symbol, first, second):
        self.symbol = symbol
        self.first = first
        self.second = second


class UnOp(Node):
    def __init__(self, symbol, first):
        self.symbol = symbol
        self.first = first
