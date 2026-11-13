#!/usr/bin/env python3
"""List every ordering or equality comparison in a Python file that could involve a non-integer number, with its line. STATIC: the file is parsed, never imported or run.
usage: python3 -I cmpscan.py <file.py> [...]
A comparison is skipped only when every operand is plainly not a price-like number: a string, None, True/False, an int literal with no float beside it, len(...), or an 'in' / 'is' test."""
import ast, sys

def plain(n):
    if isinstance(n, ast.Constant): return isinstance(n.value, (str, bytes, bool, type(None))) or (isinstance(n.value, int))
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("len", "int", "str", "set", "sorted", "type"): return True
    if isinstance(n, (ast.Tuple, ast.List, ast.Set, ast.Dict, ast.JoinedStr)): return True
    return False

def hasfloat(n):
    for x in ast.walk(n):
        if isinstance(x, ast.Constant) and isinstance(x.value, float): return True
    return False

def arith(n):
    return any(isinstance(x, ast.BinOp) and isinstance(x.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)) for x in ast.walk(n))

for path in sys.argv[1:]:
    src = open(path).read(); tree = ast.parse(src); lines = src.split("\n"); seen = set()
    print("==== %s (%d lines)" % (path, len(lines)))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare): continue
        if all(isinstance(o, (ast.In, ast.NotIn, ast.Is, ast.IsNot)) for o in node.ops): continue
        ops = [node.left] + node.comparators
        if all(plain(o) for o in ops): continue
        strs = sum(1 for o in ops if isinstance(o, ast.Constant) and isinstance(o.value, (str, type(None))))
        if strs: continue
        tag = ("F" if hasfloat(node) else "-") + ("A" if arith(node) else "-") + ("=" if any(isinstance(o, (ast.Eq, ast.NotEq)) for o in node.ops) else "-")
        seg = ast.get_source_segment(src, node) or ""
        key = (node.lineno, seg)
        if key in seen: continue
        seen.add(key); out.append((node.lineno, "%5d %s  %s" % (node.lineno, tag, " ".join(seg.split())[:230])))
    for _, l in sorted(out): print(l)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
            nm = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            if nm in ("ceil", "floor", "round", "int", "max", "min") and (nm in ("ceil", "floor") or (nm in ("round", "int") and arith(node))):
                print("%5d CALL %s" % (node.lineno, " ".join((ast.get_source_segment(src, node) or "").split())[:200]))
