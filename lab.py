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
    # SchemeSyntaxError, # uncomment in LISP part 2!
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
        #ignore comments without doing anything
        if comment:
            if ch == '\n':
                comment = False
            continue

        #; marks the start of a comment
        if ch == ';':
            comment = True
            continue
        #each token ends with a space of some sort or paren
        elif ch == " " or ch == "\n" or ch == "\t":
            if current_token != "":
                tokens.append(current_token)
                current_token = ""
        elif ch == '(' or ch == ')':
            if current_token != "":
                tokens.append(current_token)
                current_token = ""
            tokens.append(ch)
        else:
            current_token += ch
    #add the last token if there is one
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
    """
    if not tokens:
        raise SchemeEvaluationError("Empty Tokens")

    token = tokens.pop(0) #shorten the list of tokens each time

    if token == '(':
        current_expr = []
        while tokens[0] != ')':
            #recursively parse the stuff inside this layer of paren 
            current_expr.append(parse(tokens)) 
            #unmatched paren when we reach end without )
            if not tokens:
                raise SchemeEvaluationError("Unmatched parenthesis")
        tokens.pop(0)
        return current_expr
    elif token == ')':
        raise SchemeEvaluationError("Unmatched parenthesis")
    else:
        return number_or_symbol(token)


# endregion
####################################################################
# region                       Evaluation
####################################################################

def evaluate(tree):
    """
    Given tree, a fully parsed expression, evaluates and outputs the result of
    evaluating expression according to the rules of the Scheme language.

    >>> evaluate(6.101)
    6.101
    >>> evaluate(['+', 3, ['-', 3, 1, 1], 2])
    6
    """
    if not isinstance(tree, list):
        if isinstance(tree, (int, float)):
            #if number, just return number
            return tree
        else:
            #if symbol, return object associated with symbol
            if tree in SCHEME_BUILTINS:
                return SCHEME_BUILTINS[tree]
            else:
                raise SchemeNameError("Symbol not found/undefined")
    else:
        oper = evaluate(tree[0])
        args = [evaluate(arg) for arg in tree[1:]]
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


SCHEME_BUILTINS = {
    "+": lambda *args: sum(args),
    "*": builtin_mul,
    "-": lambda x, *y: x - sum(y) if y else -x,
    "/": lambda x, *y: x / builtin_mul(*y) if y else 1 / x,
}


# endregion
####################################################################
# region                       REPL
####################################################################

if __name__ == "__main__":
    run_doctest = True
    run_repl = False

    if run_doctest:
        _doctest_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
        doctest.run_docstring_examples(tokenize, globals(), optionflags=_doctest_flags)
        #doctest.testmod(optionflags=_doctest_flags)  # runs ALL doctests

    if run_repl:
        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
        SchemeREPL(sys.modules[__name__], verbose=True, repl_frame=None).cmdloop()

# endregion
