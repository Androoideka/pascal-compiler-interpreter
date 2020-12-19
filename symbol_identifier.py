class Symbol:
    def __init__(self, id_, type_, scope, start, end):
        self.id_ = id_
        self.type_ = type_
        self.scope = scope
        self.start = start
        self.end = end

    def __str__(self):
        return "<{} {} {}>".format(self.id_, self.type_, self.scope)

    def copy(self):
        return Symbol(self.id_, self.type_, self.scope, self.start, self.end)
