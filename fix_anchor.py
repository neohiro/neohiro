p = r"patch_bg_core.py"
s = open(p, encoding="utf-8").read()
old = '"        self.parcel_name_cache = {}  # UUID -> parcel name string"'
new = '"        self.parcel_name_cache = {}   # UUID -> parcel name string"'
if old in s:
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)
    print("anchor fixed")
else:
    print("anchor variant already correct")
