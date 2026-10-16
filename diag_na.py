import subprocess, yaml, collections

r = subprocess.run(["gh", "api", "repos/neohiro/NewsAggregator/contents/.github/workflows/release.yml",
                    "-H", "Accept: application/vnd.github.raw"],
                   capture_output=True)
raw = r.stdout
text = raw.decode("utf-8")

# 1. duplicate-key aware YAML load
def no_dupes(pairs):
    keys = [k for k, _ in pairs]
    dupes = [k for k, c in collections.Counter(keys).items() if c > 1]
    if dupes:
        raise ValueError(f"duplicate keys: {dupes}")
    return dict(pairs)

try:
    yaml.load(text, Loader=yaml.SafeLoader) # plain
    doc = yaml.load(text, Loader=yaml.CSafeLoader if hasattr(yaml,'CSafeLoader') else yaml.SafeLoader)
except Exception as e:
    print("YAML ERROR:", e)

class DupCheck(yaml.SafeLoader):
    pass
def construct_mapping(loader, node, deep=False):
    keys = []
    for knode, _ in node.value:
        k = loader.construct_object(knode, deep=True)
        keys.append(k)
    dupes = [k for k, c in collections.Counter(keys).items() if c > 1]
    if dupes:
        raise ValueError(f"duplicate keys: {dupes} at line {node.start_mark.line+1}")
    return yaml.SafeLoader.construct_mapping(loader, node, deep=True)
DupCheck.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)

try:
    yaml.load(text, Loader=DupCheck)
    print("no duplicate keys")
except ValueError as e:
    print("SCHEMA ISSUE:", e)

print("\nline endings:", "CRLF" if b"\r\n" in raw else "LF")
print("trailing bytes:", raw[-40:])
on_block = text.split("\njobs:", 1)[0]
print("\n--- on: block ---")
print(on_block)
