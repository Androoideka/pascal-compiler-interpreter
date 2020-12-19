from visitor import Visitor
from symbol_table import Symbols


class Symbolizer(Visitor):
    def __init__(self, ast):
        self.ast = ast

    def visit_Program(self, parent, node):
        node.symbols = Symbols()
        node.symbols.put("ord", "integer", id(node))
        node.symbols.put("chr", "char", id(node))
        node.symbols.put("inc", None, id(node))
        node.symbols.put("dec", None, id(node))
        node.symbols.put("length", "integer", id(node))
        node.symbols.put("insert", None, id(node))
        for n in node.nodes:
            self.visit(node, n)

    def visit_Decl(self, parent, node):
        parent.symbols.put(node.id_.value, node.type_.value, id(parent))

    def visit_ArrayDecl(self, parent, node):
        node.symbols = Symbols()
        parent.symbols.put(
            node.id_.value, node.type_.value, id(parent), node.start, node.end
        )

    def visit_ArrayElem(self, parent, node):
        pass

    def visit_Assign(self, parent, node):
        pass

    def visit_If(self, parent, node):
        self.visit(node, node.true)
        if node.false is not None:
            self.visit(node, node.false)

    def visit_While(self, parent, node):
        self.visit(node, node.block)

    def visit_Repeat(self, parent, node):
        self.visit(node, node.block)

    def visit_For(self, parent, node):
        self.visit(node, node.block)

    def visit_FuncImpl(self, parent, node):
        type_ = None
        if node.type_ is not None:
            type_ = node.type_.value
        parent.symbols.put(node.id_.value, type_, id(parent))
        self.visit(node, node.execblock)
        if node.varblock is not None:
            self.visit(node.execblock, node.varblock)
        self.visit(node.execblock, node.params)

    def visit_FuncCall(self, parent, node):
        pass

    def visit_Block(self, parent, node):
        node.symbols = Symbols()
        for n in node.nodes:
            self.visit(node, n)

    def visit_Vars(self, parent, node):
        for n in node.nodes:
            self.visit(parent, n)

    def visit_Params(self, parent, node):
        node.symbols = Symbols()
        for p in node.params:
            self.visit(node, p)
            self.visit(parent, p)

    def visit_Args(self, parent, node):
        pass

    def visit_Elems(self, parent, node):
        pass

    def visit_Break(self, parent, node):
        pass

    def visit_Continue(self, parent, node):
        pass

    def visit_Exit(self, parent, node):
        pass

    def visit_Return(self, parent, node):
        pass

    def visit_Type(self, parent, node):
        pass

    def visit_Integer(self, parent, node):
        pass

    def visit_Real(self, parent, node):
        pass

    def visit_Boolean(self, parent, node):
        pass

    def visit_Char(self, parent, node):
        pass

    def visit_String(self, parent, node):
        pass

    def visit_Id(self, parent, node):
        pass

    def visit_BinOp(self, parent, node):
        pass

    def visit_UnOp(self, parent, node):
        pass

    def symbolize(self):
        self.visit(None, self.ast)
