from lexer import Lexer
from token_parser import Parser
from symbol_visitor import Symbolizer
from compiler import Generator
from interpreter import Runner
import argparse

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("src")  # Path to PAS file to compile and run
arg_parser.add_argument("gen")  # Path for generated C program
args = vars(arg_parser.parse_args())

with open(args["src"], "r") as source:
    text = source.read()
    lexer = Lexer(text)
    tokens = lexer.lex()
    parser = Parser(tokens)
    ast = parser.parse()
    symbolizer = Symbolizer(ast)
    symbolizer.symbolize()
    generator = Generator(ast)
    generator.generate(args["gen"])
    runner = Runner(ast)
    runner.run()
