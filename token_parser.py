from lexical_token_class import Class
from ast_nodes import *
from functools import wraps
import pickle


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.curr = tokens.pop(0)
        self.prev = None

    def restorable(call):
        @wraps(call)
        def wrapper(self, *args, **kwargs):
            state = pickle.dumps(self.__dict__)
            result = call(self, *args, **kwargs)
            self.__dict__ = pickle.loads(state)
            return result

        return wrapper

    def eat(self, class_):
        if self.curr.class_ == class_:
            self.prev = self.curr
            self.curr = self.tokens.pop(0)
        else:
            self.die_type(class_.name, self.curr.class_.name)

    def program(self):
        nodes = []
        while self.curr.class_ != Class.EOF:
            if self.curr.class_ == Class.FUNCTYPE:
                nodes.append(self.funcdecl())
            elif self.curr.class_ == Class.VAR or self.curr.class_ == Class.BEGIN:
                nodes.append(self.main_())
            else:
                self.die_deriv(self.program.__name__)
        return Program(nodes)

    def id_(self):
        id_ = Id(self.curr.lexeme)
        if self.prev.class_ == Class.FUNCTYPE:
            self.eat(Class.ID)
            return id_
        self.eat(Class.ID)
        if self.curr.class_ == Class.LPAREN:
            self.eat(Class.LPAREN)
            args = self.args()
            self.eat(Class.RPAREN)
            return FuncCall(id_, args)
        elif self.curr.class_ == Class.LBRACKET:
            self.eat(Class.LBRACKET)
            index = self.logic()
            self.eat(Class.RBRACKET)
            id_ = ArrayElem(id_, index)
        if self.curr.class_ == Class.ASSIGN:
            self.eat(Class.ASSIGN)
            expr = self.logic()
            return Assign(id_, expr)
        else:
            return id_

    def funcdecl(self):
        functype_ = self.curr.lexeme
        self.eat(Class.FUNCTYPE)
        type_ = None
        id_ = self.id_()
        self.eat(Class.LPAREN)
        params = self.params()
        self.eat(Class.RPAREN)
        if functype_ == "function":
            self.eat(Class.COLON)
            type_ = self.type_()
        self.eat(Class.SEMICOLON)
        varblock = None
        if self.curr.class_ == Class.VAR:
            varblock = self.var_()
        execblock = self.block()
        self.eat(Class.SEMICOLON)
        return FuncImpl(type_, id_, params, varblock, execblock)

    def main_(self):
        varblock = None
        if self.curr.class_ == Class.VAR:
            varblock = self.var_()
        execblock = self.block()
        execblock.nodes.append(Return(Integer(0)))
        self.eat(Class.PERIOD)
        return FuncImpl(Type("integer"), Id("main"), Params([]), varblock, execblock)

    def vardecl(self):
        ids_ = []
        nodes = []
        while self.curr.class_ != Class.COLON:
            if len(ids_) > 0:
                self.eat(Class.COMMA)
            ids_.append(self.id_())
        self.eat(Class.COLON)
        start = None
        end = None
        elems = None
        is_array = False
        if self.curr.class_ == Class.ARRAY:
            self.eat(Class.ARRAY)
            self.eat(Class.LBRACKET)
            if self.curr.class_ != Class.RBRACKET:
                start = self.logic()
                self.eat(Class.SPAN)
                end = self.logic()
            self.eat(Class.RBRACKET)
            self.eat(Class.OF)
            is_array = True
        type_ = self.type_()
        if is_array:
            if self.curr.class_ == Class.EQ:
                self.eat(Class.EQ)
                self.eat(Class.LPAREN)
                elems = self.elems()
                self.eat(Class.RPAREN)
            for id_ in ids_:
                nodes.append(ArrayDecl(type_, id_, start, end, elems))
            return nodes
        elif type_.value == "string":
            start = Integer(1)
            # https://wiki.freepascal.org/Character_and_string_types#String_types
            # Short strings have a maximum length of 255 characters with the implicit codepage CP_ACP.
            end = Integer(256)
            if self.curr.class_ == Class.LBRACKET:
                self.eat(Class.LBRACKET)
                if self.curr.class_ != Class.RBRACKET:
                    end = self.logic()
                self.eat(Class.RBRACKET)
            for id_ in ids_:
                nodes.append(ArrayDecl(type_, id_, start, end, elems))
            return nodes
        else:
            for id_ in ids_:
                nodes.append(Decl(type_, id_))
            return nodes

    def if_else(self):
        if_ = self.if_()
        self.eat(Class.SEMICOLON)
        return if_

    def if_(self):
        self.eat(Class.IF)
        cond = self.logic()
        self.eat(Class.THEN)
        true = self.block()
        false = None
        if self.curr.class_ == Class.ELSE:
            self.eat(Class.ELSE)
            if self.curr.class_ == Class.IF:
                false = self.if_()
            else:
                false = self.block()
        return If(cond, true, false)

    def while_(self):
        self.eat(Class.WHILE)
        cond = self.logic()
        self.eat(Class.DO)
        block = self.block()
        self.eat(Class.SEMICOLON)
        return While(cond, block)

    def repeat_(self):
        self.eat(Class.REPEAT)
        block = self.block()
        cond = self.logic()
        self.eat(Class.SEMICOLON)
        return Repeat(cond, block)

    def for_(self):
        self.eat(Class.FOR)
        init = self.id_()
        op = "<="
        if self.curr.class_ == Class.DOWNTO:
            self.eat(Class.DOWNTO)
            op = ">="
        else:
            self.eat(Class.TO)
        compVal = self.logic()
        self.eat(Class.DO)
        block = self.block()
        self.eat(Class.SEMICOLON)
        return For(init, BinOp(op, init.id_, compVal), block)

    def var_(self):
        nodes = []
        self.eat(Class.VAR)
        while self.curr.class_ not in [Class.BEGIN, Class.FUNCTYPE, Class.EOF]:
            nodes.extend(self.vardecl())
            self.eat(Class.SEMICOLON)
        return Vars(nodes)

    def block(self):
        nodes = []
        if self.curr.class_ == Class.BEGIN:
            self.eat(Class.BEGIN)
        while self.curr.class_ != Class.END and self.curr.class_ != Class.UNTIL:
            if self.curr.class_ == Class.IF:
                nodes.append(self.if_else())
            elif self.curr.class_ == Class.WHILE:
                nodes.append(self.while_())
            elif self.curr.class_ == Class.REPEAT:
                nodes.append(self.repeat_())
            elif self.curr.class_ == Class.FOR:
                nodes.append(self.for_())
            elif self.curr.class_ == Class.BREAK:
                nodes.append(self.break_())
            elif self.curr.class_ == Class.CONTINUE:
                nodes.append(self.continue_())
            elif self.curr.class_ == Class.RETURN:
                nodes.append(self.return_())
            elif self.curr.class_ == Class.EXIT:
                nodes.append(self.exit_())
            elif self.curr.class_ == Class.ID:
                nodes.append(self.id_())
                self.eat(Class.SEMICOLON)
            else:
                self.die_deriv(self.block.__name__)
        self.eat(self.curr.class_)
        return Block(nodes)

    def params(self):
        params = []
        while self.curr.class_ != Class.RPAREN:
            if len(params) > 0:
                self.eat(Class.COMMA)
            params.extend(self.vardecl())
        return Params(params)

    def args(self):
        args = []
        field_widths = []
        decimal_field_widths = []
        while self.curr.class_ != Class.RPAREN:
            if len(args) > 0:
                self.eat(Class.COMMA)
            args.append(self.logic())
            if self.curr.class_ == Class.COLON:
                self.eat(self.curr.class_)
                field_widths.append(Integer(self.curr.lexeme))
                self.eat(Class.INTEGER)
                if self.curr.class_ == Class.COLON:
                    self.eat(self.curr.class_)
                    decimal_field_widths.append(Integer(self.curr.lexeme))
                    self.eat(Class.INTEGER)
                else:
                    decimal_field_widths.append(None)
            else:
                field_widths.append(None)
                decimal_field_widths.append(None)
        return Args(args, field_widths, decimal_field_widths)

    def elems(self):
        elems = []
        while self.curr.class_ != Class.RPAREN:
            if len(elems) > 0:
                self.eat(Class.COMMA)
            elems.append(self.logic())
        return Elems(elems)

    def return_(self):
        self.eat(Class.RETURN)
        expr = self.logic()
        self.eat(Class.SEMICOLON)
        return Return(expr)

    def break_(self):
        self.eat(Class.BREAK)
        self.eat(Class.SEMICOLON)
        return Break()

    def continue_(self):
        self.eat(Class.CONTINUE)
        self.eat(Class.SEMICOLON)
        return Continue()

    def exit_(self):
        self.eat(Class.EXIT)
        expr = None
        if self.curr.class_ == Class.LPAREN:
            self.eat(self.curr.class_)
            expr = self.logic()
            self.eat(Class.RPAREN)
        self.eat(Class.SEMICOLON)
        return Exit(expr)

    def type_(self):
        type_ = Type(self.curr.lexeme)
        self.eat(Class.TYPE)
        return type_

    def factor(self):
        if self.curr.class_ == Class.INTEGER:
            value = Integer(self.curr.lexeme)
            self.eat(Class.INTEGER)
            return value
        elif self.curr.class_ == Class.CHAR:
            value = Char(self.curr.lexeme)
            self.eat(Class.CHAR)
            return value
        elif self.curr.class_ == Class.STRING:
            value = String(self.curr.lexeme)
            self.eat(Class.STRING)
            return value
        elif self.curr.class_ == Class.REAL:
            value = Real(self.curr.lexeme)
            self.eat(Class.REAL)
            return value
        elif self.curr.class_ == Class.BOOLEAN:
            value = Boolean(self.curr.lexeme)
            self.eat(Class.BOOLEAN)
            return value
        elif self.curr.class_ == Class.ID:
            return self.id_()
        elif self.curr.class_ in [Class.MINUS, Class.NOT]:
            op = self.curr
            self.eat(self.curr.class_)
            first = None
            if self.curr.class_ == Class.LPAREN:
                self.eat(Class.LPAREN)
                first = self.logic()
                self.eat(Class.RPAREN)
            else:
                first = self.factor()
            return UnOp(op.lexeme, first)
        elif self.curr.class_ == Class.LPAREN:
            self.eat(Class.LPAREN)
            first = self.logic()
            self.eat(Class.RPAREN)
            return first
        elif self.curr.class_ == Class.SEMICOLON:
            return None
        else:
            self.die_deriv(self.factor.__name__)

    def term(self):
        first = self.factor()
        while self.curr.class_ in [Class.STAR, Class.FWDSLASH, Class.MOD, Class.DIV]:
            op = self.curr.lexeme
            self.eat(self.curr.class_)
            second = self.factor()
            first = BinOp(op, first, second)
        return first

    def expr(self):
        first = self.term()
        while self.curr.class_ in [Class.PLUS, Class.MINUS]:
            op = self.curr.lexeme
            self.eat(self.curr.class_)
            second = self.term()
            first = BinOp(op, first, second)
        return first

    def compare(self):
        first = self.expr()
        if self.curr.class_ == Class.EQ:
            op = self.curr.lexeme
            self.eat(Class.EQ)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.NEQ:
            op = self.curr.lexeme
            self.eat(Class.NEQ)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.LT:
            op = self.curr.lexeme
            self.eat(Class.LT)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.GT:
            op = self.curr.lexeme
            self.eat(Class.GT)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.LTE:
            op = self.curr.lexeme
            self.eat(Class.LTE)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.GTE:
            op = self.curr.lexeme
            self.eat(Class.GTE)
            second = self.expr()
            return BinOp(op, first, second)
        else:
            return first

    def logic_term(self):
        first = self.compare()
        while self.curr.class_ == Class.AND:
            op = self.curr.lexeme
            self.eat(Class.AND)
            second = self.compare()
            first = BinOp(op, first, second)
        return first

    def logic(self):
        first = self.logic_term()
        while self.curr.class_ == Class.OR or self.curr.class_ == Class.XOR:
            op = self.curr.lexeme
            self.eat(self.curr.class_)
            second = self.logic_term()
            first = BinOp(op, first, second)
        return first

    @restorable
    def is_func_call(self):
        try:
            self.eat(Class.LPAREN)
            self.args()
            self.eat(Class.RPAREN)
            return True
        except:
            return False

    def parse(self):
        return self.program()

    def die(self, text):
        raise SystemExit(text)

    def die_deriv(self, fun):
        self.die("Derivation error: {}".format(fun))

    def die_type(self, expected, found):
        self.die("Expected: {}, Found: {}".format(expected, found))
