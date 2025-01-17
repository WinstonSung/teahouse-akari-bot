import ast
import cmath
import decimal
import fractions
import math
import operator as op
import os
import statistics
import sys

from simpleeval import EvalWithCompoundTypes, DEFAULT_FUNCTIONS, DEFAULT_NAMES, DEFAULT_OPERATORS

from constant import consts

sys.set_int_max_str_digits(0)
if os.name == 'posix':
    os.nice(15)
    import resource

    resource.setrlimit(resource.RLIMIT_AS,
                       (16 * 1024 * 1024, 16 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_DATA,
                       (16 * 1024 * 1024, 16 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_STACK,
                       (16 * 1024 * 1024, 16 * 1024 * 1024))
elif os.name == 'nt':
    import win32process

    win32process.SetPriorityClass(win32process.GetCurrentProcess(
    ), 16384)
    win32process.SetProcessWorkingSetSize(
        win32process.GetCurrentProcess(), 1, 16 * 1024 * 1024)

funcs = {}
named_funcs = {}


def add_func(module):
    for name in dir(module):
        item = getattr(module, name)
        if not name.startswith('_') and callable(item):
            funcs[name] = item


def add_named_func(module):
    named_funcs[module.__name__] = {}
    for name in dir(module):
        item = getattr(module, name)
        if not name.startswith('_') and callable(item):
            named_funcs[module.__name__][name] = item


add_func(math)
add_func(statistics)
add_named_func(cmath)
add_named_func(decimal)
add_named_func(fractions)

s_eval = EvalWithCompoundTypes(
    operators={
        **DEFAULT_OPERATORS,
        ast.BitOr: op.or_,
        ast.BitAnd: op.and_,
        ast.BitXor: op.xor,
        ast.Invert: op.invert,
    },
    functions={**funcs, **DEFAULT_FUNCTIONS,
               'bin': bin,
               'bool': bool,
               'complex': complex,
               'divmod': divmod,
               'hex': hex,
               'len': len,
               'oct': oct,
               'round': round
               },
    names={
        **DEFAULT_NAMES, **consts, **named_funcs,
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf, 'nan': math.nan,
        'cmath': {
            'pi': cmath.pi,
            'e': cmath.e,
            'tau': cmath.tau,
            'inf': cmath.inf,
            'infj': cmath.infj,
            'nan': cmath.nan,
            'nanj': cmath.nanj,
            **named_funcs['cmath'],
        },
    }, )

try:  # rina's rina lazy solution :rina:
    sys.stdout.write('Result ' + str(s_eval.eval(' '.join(sys.argv[1:]))))
except Exception as e:
    sys.stdout.write('Failed ' + str(e))
sys.exit()
