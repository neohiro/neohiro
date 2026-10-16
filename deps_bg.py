import ast

SRC = r"repos\BlackGlass\BlackGlass.py"
src = open(SRC, encoding="utf-8").read()
lines = src.splitlines(keepends=True)
tree = ast.parse(src)

defs = {}
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        defs[node.name] = (node.lineno, node.end_lineno)
    elif isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                defs[t.id] = (node.lineno, node.end_lineno)

BUILTINS = set(dir(__builtins__)) | {"__name__", "__file__", "__doc__", "self", "cls"}

def free_names(start, end):
    seg = ast.parse("".join(lines[start-1:end]))
    return {n.id for n in ast.walk(seg) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}

GROUPS = {
  "lltypes":    ["null","fixed","variable","vector3","vector3d","vector4","quaternion","LLUUID","IPAddr","IPPort","Constraints","const"],
  "codec":      ["llDecodeType","llEncodeType","zerocode_decode","zerocode_encode","printsafe","hexdump","packetErrorTrace","baseTypes","typeLengths"],
  "messages":   ["BaseMessage","message_lookup","registerMessage","getMessageByID","getMessageByName","UseCircuitCode","CompleteAgentMovement","RegionHandshake","FindAgentReply","AvatarPropertiesRequest","AvatarPropertiesReply","RegionHandshakeReply","ChatFromSimulator","ChatFromViewer","AgentThrottle","AgentFOV","AgentHeightWidth","AgentUpdate","PacketAck","StartPingCheck","CompletePingCheck","LogoutRequest","TeleportFinish","CloseCircuit","TeleportOffer","TeleportAccept","TeleportLocationRequest","TeleportStart","TeleportProgress","TeleportFailed","UUIDNameRequest","UUIDNameReply","MapNameRequest","MapItemReply","AgentMovementComplete","AgentDataRequest","AgentDataUpdate","ImprovedTerseObjectUpdate","ObjectUpdate","ObjectUpdateCompressed","CoarseLocationUpdate","ImagePacket","KickUser","ImprovedInstantMessage"],
  "packet":     ["Packet"],
  "network":    ["getMacAddress","__PLATFORM_STRING__","LOGIN_URI","SL_USER_AGENT","login_to_simulator","RegionClient","parse_llsd_xml","render_llsd_xml","safe_decode_llvariable"],
  "agent":      ["SecondLifeAgent"],
  "credentials":["_SECRET_KEY","CREDENTIALS_FILE","_cipher_xor","save_credentials","load_credentials"],
  "ui.widgets": ["LimitedScrolledText"],
  "ui.theme":   ["ThemedDialog","ThemedMessageBox","ThemedAskString","ThemedChoiceDialog","ThemedGroupDialog","ThemedParcelDialog","ThemedProfileDialog"],
  "ui.minimap": ["MinimapCanvas"],
  "ui.chat":    ["ChatTab"],
  "ui.login":   ["LoginPanel"],
  "ui.app":     ["MultiClientApp"],
}

all_defined = set(defs)
assigned = {}
for gname, members in GROUPS.items():
    for m in members:
        if m in assigned:
            print(f"!! {m} assigned twice ({assigned[m]}, {gname})")
        assigned[m] = gname

covered = set(assigned)
missing = all_defined - covered
if missing:
    print("NOT GROUPED:", [(m, defs[m]) for m in sorted(missing, key=lambda m: defs[m][0])])

print("\n=== EXTERNAL DEPENDENCIES PER MODULE ===")
for gname, members in GROUPS.items():
    local = set(members)
    ext = {}
    for m in members:
        s, e = defs[m]
        for n in free_names(s, e):
            if n in local or n in BUILTINS:
                continue
            if n in assigned and assigned[n] != gname:
                ext.setdefault(assigned[n], set()).add(n)
            elif n not in all_assigned_set if False else False:
                pass
    print(f"\n[{gname}]")
    for dep_mod in sorted(ext):
        names = sorted(ext[dep_mod])
        print(f"  from .{dep_mod.replace('.', '_') if False else dep_mod} <- {', '.join(names)}")
