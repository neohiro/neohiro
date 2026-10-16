# tailscale-dns-bypass

Route sites that block VPN/Tor egress — such as `weebly.com`, `secondlife.com`, `marketplace.secondlife.com`, and any other domain exhibiting anti-Tor/anti-VPN blocking behavior — to **skip Tor** while **still going through the Tailscale exit node and its underlying VPNs egress**.

## Traffic flow & architecture

1. **Exit Node**: All default traffic routes through the Tailscale exit node.
2. **Tor / TCP Routing**: TCP attempts route through Tor, but sites fingerprinting VPN/Tor egress answer with block pages (HTTP **200** carrying "Access Denied" / "Sorry, you have been blocked", or HTTP **403 / 429 / 503**).
3. **Bypass Filtering**: For blocked domains, `tailscale-dns-bypass` ensures traffic **skips Tor** (bypassing Tor proxy/circuit routing) while **remaining routed through the Tailscale exit node and its VPN egress** (never escaping to the local ISP gateway).
4. **Fallback**: Unmatched traffic joins UDP via VPN nodes to the public exit.

## How it works

1. **Resolve** the blocked domains to their real IPs using public resolvers
   (`1.1.1.1`, `8.8.8.8`) rather than the exit node's own resolution.
2. **Write** those hostnames into a single delimited block in the hosts file,
   pointing at the real IPs. Direct host mapping bypasses Tor proxy interception.
3. **Maintain Exit Routing**: Split-tunnel routes advertise local LAN prefixes (`10/8`, `192.168/16`, etc.) so LAN access works while the default route (`0.0.0.0/0`) and public IP traffic continue through the Tailscale exit node and VPN egress.

## Install

```bash
git clone <this-repo> tailscale-dns-bypass
cd tailscale-dns-bypass
npm ci          # reproducible: package-lock.json is committed
node src/cli.mjs init
```

`npm ci` is preferred over `npm install` so a reinstall gets the exact tested
dependency tree. `node_modules/` is deliberately **not** tracked in git.

## Usage

```bash
node src/cli.mjs init                # write a starter config
node src/cli.mjs run                 # refresh configured domains
node src/cli.mjs run --dry-run       # preview, touch nothing
node src/cli.mjs status              # managed entries + Tailscale state
node src/cli.mjs add example.com @ www api
node src/cli.mjs remove example.com
node src/cli.mjs probe weebly.com    # exit 1 if it looks blocked
node src/cli.mjs clear --force
```

Add it to `PATH` for the `tsdb` short name:

```bash
npm link            # provides `tsdb`
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | success |
| `1` | run failure, or `probe` found a block |
| `2` | usage error (bad option, missing argument, unknown command) |

Writing the hosts file needs Administrator on Windows, `sudo` on Linux/macOS.
`clear` refuses to prompt when stdin is not a TTY unless `--force` is passed.

## Configuration

Search order (first match wins):

1. `./tsdb.config.json`
2. `./config/tsdb.config.json`
3. `~/.config/tailscale-dns-bypass/config.json`
4. `~/.tsdb.config.json`

See [`config/tsdb.config.example.json`](config/tsdb.config.example.json).

Objects merge recursively. **Arrays are replaced, not merged** — writing
`"domains": [...]` means exactly that list, which is what makes removing an entry
possible. `"@"` is the apex; any other value is a label to prefix.

Validation rejects malformed domains, malformed subdomains, duplicate domains,
empty resolver lists and out-of-range timeouts, reporting every problem at once.

## Ownership: why lines carry a tag

```
# === tailscale-dns-bypass managed entries start ===
192.0.2.1	weebly.com www.weebly.com	# tsdb:config
192.0.2.2	manual.example	# tsdb:manual
# === tailscale-dns-bypass managed entries end ===
```

`run` refreshes `config`-tagged entries and prunes the ones that left the config.
`manual` entries — those from `tsdb add` — are never removed by a run. That is why
`tsdb add` does not silently discard the other entries, and why `run` does not
silently discard your manual additions. A trailing `#` comment is valid in both
the Unix and Windows hosts-file formats.

## Writing safely

- Every change is a **single read-modify-write**, so touching several hostnames
  produces one backup and never leaves an intermediate state.
- A write is refused if the file **changed on disk** while it was being edited,
  rather than silently overwriting someone else's edit. Re-run to apply.
- An **unchanged result is not written at all**, so a no-op run does not churn
  backups.
- Hostnames containing whitespace or `#`, and non-IPv4 literals, are rejected
  before anything is written.
- Config files carrying `__proto__` / `constructor` / `prototype` keys are
  rejected.

These reduce, but do not eliminate, the risk of two tools editing the hosts file
at once: the final `writeFile` is not an atomic replace. If that matters, take a
backup first.

## Development

```bash
npm test        # node:test suite (no external test framework)
npm run lint    # eslint
npm run verify  # both
```

## Limitations

- IPv4 only. AAAA records are resolved as a fallback but the hosts-file entry is
  written as IPv4, because dual-stack hosts entries are handled inconsistently
  across resolvers.
- The hosts file overrides DNS, so a bypassed domain keeps pointing at the IP
  resolved at run time. Re-run `run` after a DNS change.
- Split-tunnel route advertisement preserves LAN reachability; restoring *egress*
  for a blocked host also depends on the host resolving to the real IP, which is
  what the hosts entry provides.