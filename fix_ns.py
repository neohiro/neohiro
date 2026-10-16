p = r"repos\SystemMonitor\SystemMonitor.PY"
s = open(p, encoding="utf-8").read()
old = 'for ns in ("root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"):'
new = 'for ns in (r"root\\LibreHardwareMonitor", r"root\\OpenHardwareMonitor"):'
assert old in s, "anchor missing"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
import ast
ast.parse(open(p, encoding="utf-8").read())
print("fixed; syntax OK")
