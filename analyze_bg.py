import ast, sys, json

SRC = r"repos\BlackGlass\BlackGlass.py"
src = open(SRC, encoding="utf-8").read()
lines = src.splitlines(keepends=True)
tree = ast.parse(src)

# Collect top-level definitions: name -> (start_line, end_line)
defs = {}
order = []
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        defs[node.name] = (node.lineno, node.end_lineno)
        order.append(node.name)
    elif isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                defs[t.id] = (node.lineno, node.end_lineno)
                order.append(t.id)

BUILTINS = set(dir(__builtins__)) | {"__name__", "__file__", "__doc__"}

def free_names(start, end):
    """Names loaded within line span [start,end] at any depth."""
    seg = ast.parse("".join(lines[start-1:end]))
    loads = set()
    for n in ast.walk(seg):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            loads.add(n.id)
        elif isinstance(n, ast.Attribute):
            pass
    return loads

def module_deps(member_names):
    local = set(member_names)
    deps = {}
    for m in member_names:
        if m not in defs:
            continue
        s, e = defs[m]
        for name in free_names(s, e):
            if name in local or name in BUILTINS:
                continue
            if name in defs:
                deps.setdefault(name, set()).add(m)
    return deps

print("=== TOP-LEVEL DEFINITIONS (line spans) ===")
for name in sorted(order, key=lambda n: defs[n][0]):
    print(f"{defs[name][0]:>5}-{defs[name][1]:<5} {name}")
