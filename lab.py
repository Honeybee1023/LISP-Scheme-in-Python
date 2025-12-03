"""
LISP Interpreter
"""

#!/usr/bin/env python3

# import typing  # optional import
# import pprint  # optional import
import doctest
import os
import sys

from scheme_utils import (
    number_or_symbol,
    SchemeEvaluationError,
    SchemeNameError,
    SchemeSyntaxError,
    SchemeREPL,
)

sys.setrecursionlimit(20_000)
# NO ADDITIONAL IMPORTS!

####################################################################
# region                  Tokenization
####################################################################


def tokenize(source):
    r"""
    Takes source, a string, and returns a list of individual token strings.
    Ignores comments and whitespace.

    >>> tokenize(' + ')
    ['+']
    >>> tokenize('-867.5309')
    ['-867.5309']
    >>> s = "((parse   these \n tokens) ;but ignore comments\n here );)"
    >>> tokenize(s)
    ['(', '(', 'parse', 'these', 'tokens', ')', 'here', ')']
    """
    tokens = []
    current_token = ""
    comment = False
    for ch in source:
        # ignore comments without doing anything
        if comment:
            if ch == "\n":
                comment = False
            continue

        # ; marks the start of a comment
        if ch == ";":
            comment = True
            continue
        # each token ends with a space of some sort or paren
        elif ch in (" ", "\n", "\t"):
            if current_token != "":
                tokens.append(current_token)
                current_token = ""
        elif ch in ("(", ")"):
            if current_token != "":
                tokens.append(current_token)
                current_token = ""
            tokens.append(ch)
        else:
            current_token += ch
    # add the last token if there is one
    if current_token != "":
        tokens.append(current_token)
    return tokens


# endregion
####################################################################
# region                  Parsing
####################################################################


def parse(tokens):
    """
    Parses a list of token strings and outputs a tree-like representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Hint: Make use of number_or_symbol imported from scheme_utils

    >>> parse(['+'])
    '+'
    >>> parse(['-867.5309'])
    -867.5309
    >>> parse(['(', '(', 'parse', 'these', 'tokens', ')', 'here', ')'])
    [['parse', 'these', 'tokens'], 'here']
    >>> parse(['(', 'adam', 'adam', 'chris', 'duane', ')', ')'])
    SchemeSyntaxError
    """

    def parse_main_paren(tokens):
        if not tokens:
            raise SchemeEvaluationError("Empty Tokens")

        token = tokens.pop(0)  # shorten the list of tokens each time

        if token == "(":
            current_expr = []
            if not tokens:
                raise SchemeSyntaxError("Unclosed parenthesis")
            while tokens[0] != ")":
                # recursively parse the stuff inside this layer of paren
                current_expr.append(parse_main_paren(tokens))
                # unmatched paren when we reach end without )
                if not tokens:
                    raise SchemeSyntaxError("Unmatched parenthesis")
            tokens.pop(0)
            return current_expr
        elif token == ")":
            raise SchemeSyntaxError("Unmatched parenthesis")
        else:
            return number_or_symbol(token)

    result = parse_main_paren(tokens)

    if tokens:
        raise SchemeSyntaxError("Unmatched parenthesis")

    return result


# endregion
####################################################################
# region                       Evaluation
####################################################################


def evaluate(tree, frame=None):
    """
    Given tree, a fully parsed expression, evaluates and outputs the result of
    evaluating expression according to the rules of the Scheme language.

    >>> evaluate(6.101)
    6.101
    >>> evaluate(['+', 3, ['-', 3, 1, 1], 2])
    6
    """
    if frame is None:
        frame = make_initial_frame()

    if not isinstance(tree, list):
        if isinstance(tree, (int, float, bool)):
            # if number, just return number
            return tree
        else:
            # if symbol, return object associated with symbol
            if frame.is_defined(tree):
                return frame.lookup(tree)
            else:
                raise SchemeNameError("Symbol", tree, "not found/undefined")
            
    else:
        # evaluate([3.14]) should raise a SchemeEvaluationError, float not callable.
        if not isinstance(tree[0], str):
            if not isinstance(tree[0], list):
                raise SchemeEvaluationError("Operation not callable")
            
        # evaluate(['a', 1, 2]), should raise a SchemeNameError
        elif tree[0] not in SCHEME_BUILTINS and not frame.is_defined(tree[0]):
            raise SchemeNameError("Symbol not defined")
        oper = evaluate(tree[0], frame)

        # specially handle conditionals
        if oper=="if":
            if len(tree) != 4:
                raise SchemeEvaluationError("If needs 3 args")
            pred_statement = tree[1]
            true_code = tree[2]
            false_code = tree[3]
            pred_val = evaluate(pred_statement, frame)

            if pred_val is False:
                return evaluate(false_code, frame)
            else:
                return evaluate(true_code, frame)
            
        elif oper == "and":
            # evaluate args left-to-right; return False if any arg is False, otherwise return True
            for expr in tree[1:]:
                val = evaluate(expr, frame)
                if val is False:
                    return False
            return True
        
        elif oper == "or":
            for expr in tree[1:]:
                val = evaluate(expr, frame)
                if val is True:
                    return True
            return False

        # specially handle the define operation
        elif oper == "define":
            args = tree[1:]
            if len(args) < 2:
                raise SchemeEvaluationError("Define needs 2 arguments")
            var = args[0]
            val = args[1]
            if isinstance(var, list):  # simple function definition
                func_name = var[0]
                params = var[1:]
                body = val
                function = Function(params, body, frame)
                frame.define(func_name, function)
                return function
            else:  # normal function or var definition
                # if val is expression or other variable name, need to evaluate first
                if not isinstance(val, (int, float)):
                    val = evaluate(val, frame)
                frame.define(var, val)
                return val
            
        elif oper == "lambda":
            if len(tree) < 2:
                raise SchemeEvaluationError("Lambda needs 2 arguments")
            params = tree[1]
            body = tree[2]
            return Function(params, body, frame)
        
        args = [evaluate(arg, frame) for arg in tree[1:]]
        try:
            return oper(*args)
        except TypeError:
            raise SchemeEvaluationError("Function cannot be completed with given args")


# endregion
####################################################################
# region                      Built-ins
####################################################################


def builtin_mul(*args):
    """
    Computes the product of two or more evaluated numeric args.
    >>> builtin_mul(1, 2)
    2
    >>> builtin_mul(1, 2, -3)
    -6
    """
    if len(args) == 1:
        return args[0]

    if len(args) == 2:
        return args[0] * args[1]

    first_num, *rest_nums = args
    return first_num * builtin_mul(*rest_nums)

def compare_helper(args, relation):
    # relation is some function that takes two args and returns True/False
    # expects len(args) >= 2
    for a, b in zip(args, args[1:]):
        if not relation(a, b):
            return False
    return True

def check_arg_length(name, args, n):
    if len(args) < n:
        raise SchemeEvaluationError(f"{name} needs at least {n} arguments")

#builtin =, >, >=, <, <= operations
def builtin_equal(*args):
    check_arg_length("equal?", args, 2)
    first = args[0]
    for a in args[1:]:
        if a != first:
            return False
    return True

def builtin_gt(*args):
    check_arg_length(">", args, 2)
    return compare_helper(args, lambda a, b: a > b)

def builtin_ge(*args):
    check_arg_length(">=", args, 2)
    return compare_helper(args, lambda a, b: a >= b)


def builtin_lt(*args):
    check_arg_length("<", args, 2)
    return compare_helper(args, lambda a, b: a < b)


def builtin_le(*args):
    check_arg_length("<=", args, 2)
    return compare_helper(args, lambda a, b: a <= b)

#make the not operator a builtin function
def builtin_not(*args):
    if len(args) != 1:
        raise SchemeEvaluationError("not takes exactly one argument")
    return True if args[0] is False else False

#builtins for pair structures
def builtin_cons(*args):
    if len(args) != 2:
        raise SchemeEvaluationError("cons needs exactly 2 arguments")
    return Pair(args[0], args[1])


def builtin_car(*args):
    if len(args) != 1:
        raise SchemeEvaluationError("car needs exactly 1 argument")
    cell = args[0]
    if not isinstance(cell, Pair):
        raise SchemeEvaluationError("car expects a Pair")
    return cell.car


def builtin_cdr(*args):
    if len(args) != 1:
        raise SchemeEvaluationError("cdr needs exactly 1 argument")
    cell = args[0]
    if not isinstance(cell, Pair):
        raise SchemeEvaluationError("cdr expects a Pair")
    return cell.cdr

SCHEME_BUILTINS = {
    "+": lambda *args: sum(args),
    "*": builtin_mul,
    "-": lambda x, *y: x - sum(y) if y else -x,
    "/": lambda x, *y: x / builtin_mul(*y) if y else 1 / x,
    "define": "define",  # handled specially in evaluate
    "lambda": "lambda",  # handled specially in evaluate
    "#t": True,
    "#f": False,
    "if": "if",          # special form
    "and": "and",        # special form
    "or": "or",          # special form
    "not": builtin_not,  # builtin function (can be overridden by define)
    "equal?": builtin_equal,
    ">": builtin_gt,
    ">=": builtin_ge,
    "<": builtin_lt,
    "<=": builtin_le,
    "cons": builtin_cons,
    "car": builtin_car,
    "cdr": builtin_cdr,
}


# endregion
####################################################################
# region                      Frames
####################################################################
class Frame:
    """
    A Frame represents a single scope in the Scheme interpreter.

    Frames can have variables defined in them, lookup variables
    in this frame or parent frames.
    """

    def __init__(self, parent_frame=None):
        self.parent_frame = parent_frame
        self.mapping = {}

    def define(self, symbol, value):
        """
        Give this symbol a value in the mapping in this frame.
        """
        self.mapping[symbol] = value

    def lookup(self, symbol):
        """
        Lookup the value of this symbol in this frame,
        otherwise search through parent frames.
        """
        if symbol in self.mapping:
            return self.mapping[symbol]
        elif self.parent_frame is not None:
            return self.parent_frame.lookup(symbol)
        else:
            raise SchemeNameError("Symbol undefined")

    def is_defined(self, symbol):
        """
        Returns True if this symbol is defined in this frame or any parent frame.
        """
        try:
            self.lookup(symbol)
            return True
        except SchemeNameError:
            return False

    def __str__(self):
        return f"Frame({self.mapping})"


def make_initial_frame():
    """
    Creates and returns a Frame with the built-in Scheme functions defined.
    """
    frame = Frame()
    parent_frame = Frame()
    frame.parent_frame = parent_frame
    for symbol, func in SCHEME_BUILTINS.items():
        parent_frame.define(symbol, func)
    return frame


# endregion
# region                  User Functions
####################################################################
class Function:
    """
    A user-defined Scheme function.
    """

    def __init__(self, parameters, body, defining_frame):
        self.parameters = parameters
        self.body = body
        self.defining_frame = defining_frame

    def __call__(self, *args):
        if len(args) != len(self.parameters):
            raise SchemeEvaluationError("Incorrect number of arguments")

        # in frame of this fuction, set params to user input
        new_frame = Frame(self.defining_frame)  # lexical scoping
        for param, arg in zip(self.parameters, args):
            new_frame.define(param, arg)

        return evaluate(self.body, new_frame)


# endregion
# region               Other Data Structures
####################################################################
class Pair:
    """
    A cons cell with two fields: car and cdr.
    """

    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def __str__(self):
        return f"(pair {self.car} {self.cdr})"

    def __repr__(self):
        return self.__str__()
    
class EmptyList:
    def __str__(self):
        return "()"
    def __repr__(self):
        return self.__str__()
    
EMPTY_LIST = EmptyList()
# endregion
# region                       REPL
####################################################################

if __name__ == "__main__":
    run_doctest = True
    run_repl = True

    if run_doctest:
        _doctest_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
        doctest.run_docstring_examples(tokenize, globals(), optionflags=_doctest_flags)
        # doctest.testmod(optionflags=_doctest_flags)  # runs ALL doctests

    if run_repl:
        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
        SchemeREPL(
            sys.modules[__name__], verbose=True, repl_frame=make_initial_frame()
        ).cmdloop()

    print(tokenize("(adam adam chris duane))"))
# endregion
