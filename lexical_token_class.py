from enum import Enum, auto


class Class(Enum):
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    FWDSLASH = auto()
    DIV = auto()
    MOD = auto()

    XOR = auto()
    OR = auto()
    AND = auto()
    NOT = auto()

    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    BEGIN = auto()
    END = auto()
    VAR = auto()

    ASSIGN = auto()
    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()
    PERIOD = auto()
    SPAN = auto()

    FUNCTYPE = auto()
    TYPE = auto()
    INTEGER = auto()
    CHAR = auto()
    STRING = auto()
    REAL = auto()
    BOOLEAN = auto()
    ARRAY = auto()
    OF = auto()

    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    REPEAT = auto()

    DOWNTO = auto()
    TO = auto()
    DO = auto()
    THEN = auto()
    UNTIL = auto()

    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    EXIT = auto()

    ID = auto()
    EOF = auto()
