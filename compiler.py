from ast_nodes import *
from visitor import Visitor
from symbol_identifier import Symbol
import re


class Generator(Visitor):
    def __init__(self, ast):
        self.ast = ast
        self.py = ""
        self.level = 0
        self.global_ = {}
        self.local = []  # block flow

    def get_symbol(self, node):
        id_ = node.value
        for block in reversed(self.local):
            if id_ in block:
                return block[id_]
        symbol = self.global_.get(id_)
        if symbol is None:
            print("Greska: Koriscenje nedeklarisane promenljive")
            exit(0)
        return symbol

    def in_scope(self, node):
        id_ = node.value
        for block in reversed(self.local):
            if id_ in block:
                return True
        return id_ in self.global_

    def init_scope(self, node):
        self.local.append({})
        for s in node.symbols:
            self.local[-1][s.id_] = s.copy()

    def clear_scope(self, node):
        self.local.pop()

    def determine_type(self, arg):
        if isinstance(arg, BinOp):
            if arg.symbol == "/":
                return "real"
            if arg.symbol == "mod" or arg.symbol == "div":
                return "integer"
            if "=" in arg.symbol or "<" in arg.symbol or ">" in arg.symbol:
                return "boolean"
            first = self.determine_type(arg.first)
            second = self.determine_type(arg.second)
            if first == "real" or second == "real":
                return "real"
            if first == "char" or second == "char":
                return "char"
            if first == "string" or second == "string":
                return "string"
            return "integer"
        if isinstance(arg, UnOp):
            return self.determine_type(arg.first)
        if isinstance(arg, Integer):
            return "integer"
        if isinstance(arg, Real):
            return "real"
        if isinstance(arg, Boolean):
            return "boolean"
        if isinstance(arg, Char):
            return "char"
        if isinstance(arg, String):
            return "string"
        if isinstance(arg, (FuncCall, ArrayElem)):
            id_ = self.get_symbol(arg.id_)
            return id_.type_
        if isinstance(arg, Id):
            id_ = self.get_symbol(arg)
            return id_.type_

    def append(self, text):
        self.py += str(text)

    def newline(self):
        self.append("\n")

    def indent(self):
        for i in range(self.level):
            self.append("\t")

    def startblockwrapper(self):
        self.indent()
        self.append("{")
        self.newline()
        self.level += 1

    def endblockwrapper(self):
        self.level -= 1
        self.indent()
        self.append("}")
        self.newline()

    def visit_Program(self, parent, node):
        for s in node.symbols:
            self.global_[s.id_] = s.copy()
        for n in node.nodes:
            self.visit(node, n)

    def visit_Decl(self, parent, node):
        self.visit(node, node.type_)
        self.append(" ")
        self.visit(node, node.id_)

    def visit_ArrayDecl(self, parent, node):
        self.visit(node, node.type_)
        self.append(" ")
        self.visit(node, node.id_)
        self.append("[")
        self.visit(node, node.end)
        self.append("]")
        if node.elems is not None:
            self.append(" = {")
            self.visit(node, node.elems)
            self.append("}")
        else:
            self.append(" = {0}")

    def visit_ArrayElem(self, parent, node):
        symbol = self.get_symbol(node.id_)
        self.visit(node, node.id_)
        self.append("[")
        self.visit(node, node.index)
        self.append(" - ")
        self.visit(node, symbol.start)
        self.append("]")

    def visit_Assign(self, parent, node):
        self.visit(node, node.id_)
        self.append(" = ")
        self.visit(node, node.expr)

    def visit_If(self, parent, node):
        self.append("if(")
        self.visit(node, node.cond)
        self.append(")")
        self.newline()
        self.startblockwrapper()
        self.visit(node, node.true)
        self.endblockwrapper()
        if node.false is not None:
            self.indent()
            self.append("else")
            if isinstance(node.false, If):
                self.append(" ")
                self.visit(node, node.false)
            else:
                self.newline()
                self.startblockwrapper()
                self.visit(node, node.false)
                self.endblockwrapper()

    def visit_While(self, parent, node):
        self.append("while(")
        self.visit(node, node.cond)
        self.append(")")
        self.newline()
        self.startblockwrapper()
        self.visit(node, node.block)
        self.endblockwrapper()

    def visit_Repeat(self, parent, node):
        self.append("do")
        self.newline()
        self.startblockwrapper()
        self.visit(node, node.block)
        self.endblockwrapper()
        self.indent()
        self.append("while(")
        self.append("!")
        self.visit(node, node.cond)
        self.append(");")
        self.newline()

    def visit_For(self, parent, node):
        self.append("for(")
        self.visit(node, node.init)
        self.append("; ")
        self.visit(node, node.cond)
        self.append("; ")
        self.visit(node, node.init.id_)
        if node.cond.symbol == "<=":
            self.append("++")
        if node.cond.symbol == ">=":
            self.append("--")
        self.append(")")
        self.newline()
        self.startblockwrapper()
        self.visit(node, node.block)
        self.endblockwrapper()

    def visit_FuncImpl(self, parent, node):
        id_ = self.get_symbol(node.id_)
        id_.params = node.params
        id_.varblock = node.varblock
        id_.execblock = node.execblock

        if node.type_ is not None:
            self.visit(node, node.type_)
        else:
            self.append("void")
        self.append(" ")
        self.visit(node, node.id_)
        self.append("(")
        self.visit(node, node.params)
        self.append(")")
        self.newline()
        self.startblockwrapper()
        if node.varblock is not None:
            self.visit(node, node.varblock)
        self.visit(node, node.execblock)
        self.endblockwrapper()

    def visit_FuncCall(self, parent, node):
        func = node.id_.value
        args = node.args.args
        field_widths = node.args.field_widths
        decimal_field_widths = node.args.decimal_field_widths
        if func == "write" or func == "writeln" or func == "read" or func == "readln":
            if func.startswith("write"):
                self.append('printf("')
            elif func.startswith("read"):
                self.append('scanf("')
            params = []
            for a, fw, dfw in zip(args, field_widths, decimal_field_widths):
                if isinstance(a, (Integer, Real, Boolean, Char, String)):
                    self.append(a.value)
                else:
                    self.append("%")
                    if fw is not None and fw.value != 0:
                        self.visit(node.args, fw)
                    if dfw is not None:
                        self.append(".")
                        self.visit(node.args, dfw)
                    type_ = self.determine_type(a)
                    if type_ == "integer":
                        self.append("d")
                    elif type_ == "real":
                        self.append("f")
                    elif type_ == "boolean":
                        self.append("d")
                    elif type_ == "char":
                        self.append("c")
                    elif type_ == "string":
                        self.append("s")
                    params.append(a)
            if func == "writeln":
                self.append(r"\n")
            self.append('"')
            for p in params:
                self.append(", ")
                if func.startswith("read"):
                    type_ = self.determine_type(p)
                    if type_ != "string":
                        self.append("&")
                self.visit(node.args, p)
            self.append(")")
        elif func == "inc":
            if len(args) == 1:
                self.visit(node.args, args[0])
                self.append("++")
        elif func == "dec":
            if len(args) == 1:
                self.visit(node.args, args[0])
                self.append("--")
        elif func == "ord":
            if len(args) == 1:
                self.visit(node.args, args[0])
        elif func == "chr":
            if len(args) == 1:
                self.visit(node.args, args[0])
        elif func == "length":
            if len(args) == 1:
                self.append("strlen(")
                self.visit(node.args, args[0])
                self.append(")")
        elif func == "insert":
            """
            procedure Insert(
              const source: string;
              var S: string;
              const Index: Integer
            );
            """
            if len(args) == 3:
                src = args[0]
                dst = args[1]
                index = args[2]
                tempVariableId = Id("temp")
                tempCounterId = Id("i")
                counter = 0
                while self.in_scope(tempVariableId):
                    tempVariableId = Id("temp" + str(counter))
                    counter += 1
                self.local[-1][tempVariableId.value] = Symbol(
                    tempVariableId,
                    Type("char"),
                    self.local[-1],
                    Integer(0),
                    FuncCall("length", Args(dst, [], [])),
                )
                counter = 0
                while self.in_scope(tempCounterId):
                    tempCounterId = Id("i" + str(counter))
                    counter += 1
                self.local[-1][tempCounterId.value] = Symbol(
                    tempVariableId, Type("integer"), self.local[-1], None, None
                )
                srcType = None
                if isinstance(src, FuncCall):
                    srcType = self.get_symbol(src.id_).type_
                elif isinstance(src, Id):
                    srcType = self.get_symbol(src).type_
                elif isinstance(src, String):
                    srcType = "string"
                elif isinstance(src, Char):
                    srcType = "char"
                self.append("char ")
                self.append(tempVariableId.value)
                self.append("[strlen(")
                self.visit(node.args, dst)
                self.append(")];")
                self.newline()
                self.indent()
                self.append("strncpy(")
                self.append(tempVariableId.value)
                self.append(", ")
                self.visit(node.args, dst)
                self.append(", ")
                self.append("strlen(")
                self.visit(node.args, dst)
                self.append("));")
                self.newline()
                self.indent()

                self.append(tempVariableId.value)
                self.append("[")
                self.append("strlen(")
                self.visit(node.args, dst)
                self.append(")] = '\\0';")
                self.newline()
                self.indent()

                self.append("for(int ")
                self.append(tempCounterId.value)
                self.append(" = 0; ")
                self.append(tempCounterId.value)
                self.append(" < ")
                if srcType == "char":
                    self.append("1")
                else:
                    self.append("strlen(")
                    self.visit(node.args, src)
                    self.append(")")
                self.append("; ")
                self.append(tempCounterId.value)
                self.append("++)")
                self.newline()
                self.startblockwrapper()
                self.indent()
                self.visit(node.args, dst)
                self.append("[")
                self.append(tempCounterId.value)
                self.append(" + ")
                self.visit(node.args, index)
                self.append(" - 1] = ")
                if srcType == "char":
                    self.visit(node.args, src)
                else:
                    self.append(tempVariableId.value)
                    self.append("[")
                    self.append(tempCounterId.value)
                    self.append("]")
                self.append(";")
                self.newline()
                self.endblockwrapper()

                self.newline()
                self.indent()
                self.append("strcpy(")
                self.visit(node.args, dst)
                self.append(" + ")
                self.visit(node.args, index)
                if srcType == "string":
                    self.append(" + ")
                    self.append("strlen(")
                    self.visit(node.args, src)
                    self.append(") - 1")
                self.append(", ")
                self.append(tempVariableId.value)
                self.append(" + ")
                self.visit(node.args, index)
                self.append(" - 1")
                self.append(")")
        else:
            self.append(func)
            self.append("(")
            self.visit(node, node.args)
            self.append(")")

    def visit_Vars(self, parent, node):
        for n in node.nodes:
            self.indent()
            self.visit(node, n)
            self.append(";")
            self.newline()

    def visit_Block(self, parent, node):
        self.init_scope(node)

        for n in node.nodes:
            self.indent()
            self.visit(node, n)
            if not isinstance(n, (If, While, Repeat, For)):
                self.append(";")
            self.newline()

        self.clear_scope(node)

    def visit_Params(self, parent, node):
        for i, p in enumerate(node.params):
            if i > 0:
                self.append(", ")
            self.visit(p, p.type_)
            self.append(" ")
            self.visit(p, p.id_)

    def visit_Args(self, parent, node):
        for i, a in enumerate(node.args):
            if i > 0:
                self.append(", ")
            self.visit(node, a)

    def visit_Elems(self, parent, node):
        for i, e in enumerate(node.elems):
            if i > 0:
                self.append(", ")
            self.visit(node, e)

    def visit_Break(self, parent, node):
        self.append("break")

    def visit_Continue(self, parent, node):
        self.append("continue")

    def visit_Exit(self, parent, node):
        self.append("return")
        if node.expr is not None:
            self.append(" ")
            self.visit(node, node.expr)

    def visit_Return(self, parent, node):
        self.append("return")
        if node.expr is not None:
            self.append(" ")
            self.visit(node, node.expr)

    def visit_Type(self, parent, node):
        if node.value == "integer":
            self.append("int")
        elif node.value == "real":
            self.append("float")
        elif node.value == "boolean":
            self.append("int")
        elif node.value == "string":
            self.append("char")
        else:
            self.append(node.value)

    def visit_Integer(self, parent, node):
        self.append(node.value)

    def visit_Real(self, parent, node):
        self.append(node.value)

    def visit_Boolean(self, parent, node):
        if node.value == "true":
            self.append("1")
        elif node.value == "false":
            self.append("0")

    def visit_Char(self, parent, node):
        self.append("'")
        self.append(node.value)
        self.append("'")

    def visit_String(self, parent, node):
        self.append('"')
        self.append(node.value)
        self.append('"')

    def visit_Id(self, parent, node):
        self.append(node.value)

    def visit_BinOp(self, parent, node):
        if node.symbol == "xor":
            self.append("!")
        self.visit(node, node.first)
        if node.symbol == "and":
            self.append(" && ")
        elif node.symbol == "or":
            self.append(" || ")
        elif node.symbol == "mod":
            self.append(" % ")
        elif node.symbol == "div":
            self.append(" / ")
        elif node.symbol == "=":
            self.append(" == ")
        elif node.symbol == "<>" or node.symbol == "xor":
            self.append(" != ")
        else:
            self.append(" ")
            self.append(node.symbol)
            self.append(" ")
        if node.symbol == "xor":
            self.append("!")
        self.visit(node, node.second)

    def visit_UnOp(self, parent, node):
        if node.symbol == "not":
            self.append("!")
        else:
            self.append(node.symbol)
        self.visit(node, node.first)

    def generate(self, path):
        self.visit(None, self.ast)
        self.py = re.sub("\n\s*\n", "\n", self.py)
        with open(path, "w") as source:
            source.write(self.py)
        return path
