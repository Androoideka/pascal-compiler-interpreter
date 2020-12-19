from symbol_identifier import Symbol


class Symbols:
    def __init__(self):
        self.symbols = {}

    def put(self, id_, type_, scope, start=None, end=None):
        self.symbols[id_] = Symbol(id_, type_, scope, start, end)

    def get(self, id_):
        return self.symbols[id_]

    def contains(self, id_):
        return id_ in self.symbols

    def remove(self, id_):
        del self.symbols[id_]

    def __len__(self):
        return len(self.symbols)

    def __str__(self):
        out = ""
        for _, value in self.symbols.items():
            if len(out) > 0:
                out += "\n"
            out += str(value)
        return out

    def __iter__(self):
        return iter(self.symbols.values())

    def __next__(self):
        return next(self.symbols.values())
