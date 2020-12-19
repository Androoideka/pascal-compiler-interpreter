from ast_nodes import *
from visitor import Visitor
from symbol_identifier import Symbol


class Runner(Visitor):
    def __init__(self, ast):
        self.ast = ast
        self.global_ = {}
        self.local = {}
        self.call_stack = []  # replacement for self.scope
        self.search_new_call = True
        self.return_ = None
        self.return_value = None
        self.break_ = False
        self.newline = True
        self.inputs = None

    def get_symbol(self, node):
        recursion = self.is_recursion()
        id_ = node.value
        if self.call_stack:
            scope = self.call_stack[-1] if self.search_new_call else self.call_stack[-2]
            ref = -2 if recursion and not self.search_new_call else -1
            if scope in self.local:
                curr_scope = self.local[scope][ref]
                if id_ in curr_scope:
                    return curr_scope[id_]
        symbol = self.global_.get(id_)
        if symbol is None:
            print("Greska: Koriscenje nedeklarisane promenljive")
            exit(0)
        return symbol

    def init_scope(self, node):
        scope = id(node)
        self.call_stack.append(scope)
        if scope not in self.local:
            self.local[scope] = []
        self.local[scope].append({})
        if len(self.local[scope]) > 51:
            print("Greska: Detektovana beskonacna rekurzija")
            exit(0)
        for s in node.symbols:
            self.local[scope][-1][s.id_] = s.copy()

    def clear_scope(self, node):
        scope = id(node)
        self.local[scope].pop()
        self.call_stack.pop()

    def is_recursion(self):
        if len(self.call_stack) > 1:
            curr_call = self.call_stack[-1]
            prev_call = self.call_stack[-2]
            if curr_call == prev_call:
                return True
        return False

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

    def visit_Program(self, parent, node):
        for s in node.symbols:
            self.global_[s.id_] = s.copy()
        for n in node.nodes:
            self.visit(node, n)

    def visit_Decl(self, parent, node):
        id_ = self.get_symbol(node.id_)
        id_.value = None

    def visit_ArrayDecl(self, parent, node):
        id_ = self.get_symbol(node.id_)
        id_.symbols = node.symbols
        end, elems = node.end, node.elems
        if elems is not None:
            self.visit(node, elems)
        elif end is not None:
            end = self.visit(node, end)
            if isinstance(end, Symbol):
                end = self.astype(end)
            end += 1
            for i in range(end):
                id_.symbols.put(i, id_.type_, None)
                id_.symbols.get(i).value = None

    def visit_ArrayElem(self, parent, node):
        id_ = self.get_symbol(node.id_)
        index = self.visit(node, node.index)
        if isinstance(index, Symbol):
            index = self.astype(index)
        return id_.symbols.get(index)

    def visit_Assign(self, parent, node):
        id_ = self.visit(node, node.id_)
        value = self.visit(node, node.expr)
        valueType = self.determine_type(node.expr)
        type_ = id_.type_
        if type_ != valueType:
            if not (
                (type_ == "real" and valueType == "integer")
                or (type_ == "string" and valueType == "char")
                or (type_ == "char" and valueType == "string")
            ):
                print("Greska: Koriscenje nekompatibilnih tipova")
                exit(0)
        if isinstance(value, Symbol):
            value = self.astype(value)
        id_.value = value

    def visit_If(self, parent, node):
        cond = self.visit(node, node.cond)
        if isinstance(cond, Symbol):
            cond = self.astype(cond)
        if cond:
            self.visit(node, node.true)
        else:
            if node.false is not None:
                if isinstance(node.false, If):
                    self.visit(node, node.false)
                else:
                    self.visit(node, node.false)

    def visit_While(self, parent, node):
        cond = self.visit(node, node.cond)
        if isinstance(cond, Symbol):
            cond = self.astype(cond)
        while cond:
            self.visit(node, node.block)
            if self.break_ or self.return_:
                break
            cond = self.visit(node, node.cond)
            if isinstance(cond, Symbol):
                cond = self.astype(cond)
        self.break_ = False

    def visit_Repeat(self, parent, node):
        self.visit(node, node.block)
        cond = self.visit(node, node.cond)
        if isinstance(cond, Symbol):
            cond = self.astype(cond)
        while not cond:
            self.visit(node, node.block)
            if self.break_ or self.return_:
                break
            cond = self.visit(node, node.cond)
            if isinstance(cond, Symbol):
                cond = self.astype(cond)
        self.break_ = False

    def visit_For(self, parent, node):
        self.visit(node, node.init)
        step = self.visit(node, node.cond.first)
        result = None
        cond = self.visit(node, node.cond)
        if isinstance(cond, Symbol):
            cond = self.astype(cond)
        while cond:
            self.visit(node, node.block)
            if self.break_ or self.return_:
                break
            if node.cond.symbol == "<=":
                step.value += 1
            if node.cond.symbol == ">=":
                step.value -= 1
            cond = self.visit(node, node.cond)
            if isinstance(cond, Symbol):
                cond = self.astype(cond)
        self.break_ = False

    def visit_FuncImpl(self, parent, node):
        id_ = self.get_symbol(node.id_)
        id_.params = node.params
        id_.varblock = node.varblock
        id_.execblock = node.execblock

        if node.id_.value == "main":
            self.init_scope(node.execblock)
            if node.varblock is not None:
                self.visit(node.execblock, node.varblock)
            self.visit(node, node.execblock)
            self.clear_scope(node.execblock)

    def visit_FuncCall(self, parent, node):
        func = node.id_.value
        args = node.args.args
        field_widths = node.args.field_widths
        decimal_field_widths = node.args.decimal_field_widths
        if func == "write" or func == "writeln":
            for a, fw, dfw in zip(args, field_widths, decimal_field_widths):
                format_ = "{"
                value = self.visit(node.args, a)
                if isinstance(value, Symbol):
                    value = self.astype(value)
                if fw is not None or dfw is not None:
                    format_ += ":"
                    if fw is not None and fw.value != 0:
                        vfw = self.visit(node.args, fw)
                        format_ += str(vfw)
                    if dfw is not None:
                        format_ += "."
                        vdfw = self.visit(node.args, dfw)
                        format_ += str(vdfw)
                        format_ += "f"
                format_ += "}"
                format_ = format_.format(value)
                print(format_, end="")
            if func.endswith("ln"):
                print("")
        elif func == "read" or func == "readln":
            if self.newline:
                self.newline = False
                self.inputs = input().split()
            if func.endswith("ln"):
                self.newline = True
            for i, a in enumerate(args):
                id_ = self.visit(node.args, a)
                if hasattr(id_, "symbols"):
                    for j, c in enumerate(self.inputs[i], start=1):
                        id_.symbols.put(j, id_.type_, None)
                        id_.symbols.get(j).value = c
                else:
                    id_.value = self.inputs[i]
            if i + 1 < len(self.inputs):
                self.inputs = self.inputs[i + 1 :]
        elif func == "inc":
            value = self.visit(node.args, args[0])
            if isinstance(value, Symbol):
                value.value += 1
        elif func == "dec":
            value = self.visit(node.args, args[0])
            if isinstance(value, Symbol):
                value.value -= 1
        elif func == "ord":
            value = self.visit(node.args, args[0])
            if isinstance(value, Symbol):
                value = self.astype(value)
            value = ord(value)
            return value
        elif func == "chr":
            value = self.visit(node.args, args[0])
            if isinstance(value, Symbol):
                value = self.astype(value)
            value = chr(value)
            return value
        elif func == "length":
            if isinstance(args[0], String):
                return len(args[0].value)
            elif isinstance(args[0], Id):
                id_ = self.visit(node.args, args[0])
                index = 1
                while index < len(id_.symbols) and id_.symbols.get(index).value:
                    index += 1
                index -= 1
                return index
        elif func == "insert":
            """
            procedure Insert(
              const source: string;
              var S: string;
              const Index: Integer
            );
            """
            srcArg, destArg, index = args[0], args[1], args[2]
            dest = self.get_symbol(destArg)
            index = self.visit(node.args, index)
            if isinstance(index, Symbol):
                index = self.astype(index)
            values = []
            if isinstance(srcArg, String):
                values = [c for c in srcArg.value]
            elif isinstance(srcArg, Char):
                values = [srcArg.value]
            else:
                src = self.visit(node.args, srcArg)
                if hasattr(src, "symbols"):
                    elems = [s.value for s in src.symbols]
                    values = [c for c in elems if c is not None]
                elif hasattr(src, "value"):
                    values = [src.value]
                else:
                    values = [src]
            leftovers = []
            for v in values:
                if index < len(dest.symbols):
                    leftovers.append(dest.symbols.get(index).value)
                dest.symbols.put(index, dest.type_, None)
                dest.symbols.get(index).value = v
                index += 1
            for v in leftovers:
                dest.symbols.put(index, dest.type_, None)
                dest.symbols.get(index).value = v
                index += 1
        else:
            impl = self.global_[func]
            self.init_scope(impl.execblock)

            prevReturn_ = self.return_
            self.return_ = None
            self.visit(node, node.args)
            if impl.varblock is not None:
                self.visit(impl.execblock, impl.varblock)
            self.visit(node, impl.execblock)
            result = self.return_value
            self.return_value = None

            self.clear_scope(impl.execblock)
            self.return_ = prevReturn_
            return result

    def visit_Vars(self, parent, node):
        for n in node.nodes:
            self.visit(parent, n)

    def visit_Block(self, parent, node):
        for n in node.nodes:
            if self.break_ or self.return_:
                break
            if isinstance(n, Break):
                self.break_ = True
                break
            elif isinstance(n, Continue):
                break
            elif isinstance(n, (Return, Exit)):
                self.return_ = True
                if n.expr is not None:
                    self.return_value = self.visit(n, n.expr)
                break
            else:
                self.visit(node, n)

    def visit_Params(self, parent, node):
        pass

    def visit_Args(self, parent, node):
        func = parent.id_.value
        impl = self.global_[func]
        for p, a in zip(impl.params.params, node.args):
            self.search_new_call = False
            arg = self.visit(impl.execblock, a)
            self.search_new_call = True
            id_ = self.visit(impl.execblock, p.id_)
            id_.value = arg
            if isinstance(arg, Symbol):
                id_.value = self.astype(arg)

    def visit_Elems(self, parent, node):
        id_ = self.get_symbol(parent.id_)
        for i, e in enumerate(node.elems):
            value = self.visit(node, e)
            id_.symbols.put(i, id_.type_, None)
            id_.symbols.get(i).value = value

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
        return node.value

    def visit_Real(self, parent, node):
        return node.value

    def visit_Boolean(self, parent, node):
        if node.value == "true":
            return True
        elif node.value == "false":
            return False

    def visit_Char(self, parent, node):
        return node.value

    def visit_String(self, parent, node):
        return node.value

    def visit_Id(self, parent, node):
        return self.get_symbol(node)

    def astype(self, x):
        if hasattr(x, "value"):
            if x.type_ == "integer":
                return int(x.value)
            elif x.type_ == "real":
                return float(x.value)
            return x.value
        else:
            index = 1
            value = ""
            while index < len(x.symbols) and x.symbols.get(index).value:
                value += x.symbols.get(index).value
                index += 1
            return value

    def visit_BinOp(self, parent, node):
        first = self.visit(node, node.first)
        if isinstance(first, Symbol):
            first = self.astype(first)
        second = self.visit(node, node.second)
        if isinstance(second, Symbol):
            second = self.astype(second)
        if node.symbol == "+":
            return first + second
        elif node.symbol == "-":
            return first - second
        elif node.symbol == "*":
            return first * second
        elif node.symbol == "/":
            return first / second
        elif node.symbol == "div":
            return first // second
        elif node.symbol == "mod":
            return first % second
        elif node.symbol == "=":
            return first == second
        elif node.symbol == "<>":
            return first != second
        elif node.symbol == "<":
            return first < second
        elif node.symbol == ">":
            return first > second
        elif node.symbol == "<=":
            return first <= second
        elif node.symbol == ">=":
            return first >= second
        elif node.symbol == "and":
            bool_first = first
            bool_second = second
            return bool_first and bool_second
        elif node.symbol == "or":
            bool_first = first
            bool_second = second
            return bool_first or bool_second
        elif node.symbol == "xor":
            bool_first = first
            bool_second = second
            return bool_first != bool_second
        else:
            return None

    def visit_UnOp(self, parent, node):
        first = self.visit(node, node.first)
        backup_first = first
        if isinstance(first, Symbol):
            first = first.value
        if node.symbol == "-":
            return -first
        elif node.symbol == "not":
            bool_first = first
            return not bool_first
        else:
            return None

    def run(self):
        self.visit(None, self.ast)
