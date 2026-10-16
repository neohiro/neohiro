#!/usr/bin/env node
/**
 * CLI for tailscale-dns-bypass
 * @module cli
 */

import { TailscaleDnsBypass } from './index.mjs';
import { info, error, warn } from './logger.mjs';

const VERSION = '1.0.0';

const HELP = `
tailscale-dns-bypass v${VERSION}
Route sites that block VPN/Tor egress around a Tailscale exit node.

USAGE:
  tsdb <command> [options]

COMMANDS:
  run              Resolve configured domains, refresh hosts entries, configure split tunnelling
  status           Show managed entries and Tailscale state
  add <domain>     Add a domain (and optional subdomains) without disturbing other entries
  remove <domain>  Remove a domain and its subdomains
  clear            Remove every managed entry from the hosts file
  probe <domain>   Report whether a domain looks blocked from here
  config           Print the effective configuration
  init             Write a starter tsdb.config.json
  help             Show this help

OPTIONS:
  -c, --config <path>    Path to config file
  -n, --dry-run          Report intended changes; touch nothing
  -v, --verbose          Debug logging
  -f, --force            Skip the confirmation prompt
  -l, --log-level <lvl>  debug | info | warn | error
  -h, --help             Show help
      --version          Show version

EXAMPLES:
  tsdb run                       # Refresh configured domains
  tsdb run --dry-run             # Preview
  tsdb add example.com @ www api # Add apex, www and api
  tsdb remove example.com        # Remove apex and any subdomains
  tsdb probe weebly.com          # Is it blocked from here?

CONFIG LOCATIONS (first match wins):
  ./tsdb.config.json
  ./config/tsdb.config.json
  ~/.config/tailscale-dns-bypass/config.json
  ~/.tsdb.config.json

EXIT CODES:
  0 success   1 failure/blocked   2 usage error
`;

/** Exit 2 for usage problems, so scripts can tell them from run failures. */
class UsageError extends Error {}

function parseArgs(argv) {
  const options = { positional: [], args: [] };
  const valueFlags = new Map([
    ['-c', 'config'], ['--config', 'config'],
    ['-l', 'logLevel'], ['--log-level', 'logLevel']
  ]);
  const boolFlags = new Map([
    ['-n', 'dryRun'], ['--dry-run', 'dryRun'],
    ['-v', 'verbose'], ['--verbose', 'verbose'],
    ['-f', 'force'], ['--force', 'force'],
    ['-h', 'help'], ['--help', 'help'],
    ['--version', 'version']
  ]);

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];

    if (valueFlags.has(arg)) {
      const key = valueFlags.get(arg);
      const value = argv[++i];
      // Swallowing the next flag as a value silently ignores the command it
      // belonged to, so reject both a missing value and an option-shaped one.
      if (value === undefined || value.startsWith('-')) {
        throw new UsageError(`${arg} requires a value`);
      }
      options[key] = value;
      continue;
    }
    if (boolFlags.has(arg)) {
      options[boolFlags.get(arg)] = true;
      continue;
    }
    if (arg.startsWith('-') && arg !== '-') throw new UsageError(`Unknown option: ${arg}`);
    options.positional.push(arg);
  }

  options.command = options.positional.shift() || null;
  options.args = options.positional;
  return options;
}

/**
 * Cross-platform confirmation. Deliberately avoids `setRawMode`, which does not
 * exist on Windows and would make `clear` unusable there. A timeout bounds the
 * wait so a non-interactive stdin cannot hang the command.
 */
function confirm(message, timeoutMs = 30_000) {
  const { stdin, stdout } = process;
  return new Promise(resolve => {
    stdout.write(`${message} (y/N) `);
    let settled = false;
    const finish = answer => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      stdin.removeListener('data', onData);
      stdin.removeListener('end', onEnd);
      stdin.pause();
      resolve(answer);
    };
    const onData = chunk => finish(/^y(es)?$/i.test(chunk.toString().trim()));
    const onEnd = () => finish(false);
    const timer = setTimeout(() => finish(false), timeoutMs);

    stdin.setEncoding('utf-8');
    stdin.resume();
    stdin.once('data', onData);
    stdin.once('end', onEnd);
  });
}

function requireArg(args, name) {
  if (!Array.isArray(args) || args.length === 0) throw new UsageError(`<${name}> is required`);
  return args[0];
}

async function cmdRun(bypass, options) {
  const result = await bypass.run();

  if (options.dryRun) {
    info('DRY RUN complete - nothing was written', {
      processed: result.processed,
      succeeded: result.succeeded,
      failed: result.failed
    });
  }

  console.log('\nRun summary');
  console.log(`  processed  ${result.processed}`);
  console.log(`  succeeded  ${result.succeeded}`);
  console.log(`  failed     ${result.failed}`);
  for (const e of result.entries) console.log(`  ${e.ip}\t${e.domain}`);
  if (result.errors.length > 0) {
    console.log('\nErrors');
    for (const e of result.errors) console.log(`  ${e.domain}: ${e.error}`);
  }
  return result.failed === 0 ? 0 : 1;
}

async function cmdStatus(bypass) {
  const status = await bypass.status();
  const t = status.tailscale;

  console.log('\nManaged entries');
  if (status.entries.length === 0) {
    console.log('  (none)');
  } else {
    for (const e of status.entries) {
      console.log(`  ${e.ip}\t${e.allHostnames.join(' ')}  # tsdb:${e.tag}`);
    }
  }

  console.log('\nTailscale');
  console.log(`  available        ${t.available}`);
  console.log(`  using exit node  ${t.usingExitNode}`);
  if (t.exitNodeIp) console.log(`  exit node ip     ${t.exitNodeIp}`);
  console.log(`  advertised       ${t.advertisedRoutes.join(', ') || '(none)'}`);
  console.log(`  local gateway    ${t.localGateway ?? '(unknown)'}`);

  console.log('\nConfig');
  console.log(`  domains          ${status.config.domains.join(', ') || '(none)'}`);
  console.log(`  probe enabled    ${status.config.probeEnabled}`);
  return 0;
}

async function cmdAdd(bypass, options) {
  const args = options.args;
  const domain = requireArg(args, 'domain');
  const subdomains = args.length > 0 ? args : ['@', 'www'];
  const e = await bypass.addDomain(domain, subdomains);
  info('Added domain', { domain: e.domain, ip: e.ip, hostnames: e.hostnames });
  return 0;
}

async function cmdRemove(bypass, options) {
  const domain = requireArg(options.args, 'domain');
  const removed = await bypass.removeDomain(domain);
  if (removed) info('Removed domain', { domain });
  else warn('Domain not present in managed entries', { domain });
  return removed ? 0 : 1;
}

async function cmdClear(bypass, options) {
  if (!options.force) {
    // A non-TTY cannot be prompted safely, so require an explicit opt-in.
    if (!process.stdin.isTTY) {
      throw new UsageError('Refusing to clear without --force when stdin is not a TTY');
    }
    if (!await confirm('Remove ALL managed entries from the hosts file?')) {
      info('Cancelled');
      return 0;
    }
  }
  info('Cleared managed entries', { count: await bypass.clear() });
  return 0;
}

async function cmdProbe(bypass, options) {
  const domain = requireArg(options.args, 'domain');
  if (!bypass.config) await bypass.init();

  const result = await bypass.probe.probe(domain);
  console.log(`\nProbe result for ${domain}`);
  console.log(`  blocked    ${result.blocked}`);
  console.log(`  status     ${result.statusCode || '(no response)'}`);
  console.log(`  latency    ${result.latencyMs}ms`);
  if (result.blockReason) console.log(`  reason     ${result.blockReason}`);
  // A block is a finding, not a tool failure, so surface it in the exit code.
  return result.blocked ? 1 : 0;
}

async function cmdConfig(bypass) {
  if (!bypass.config) await bypass.init();
  console.log(JSON.stringify(bypass.config, null, 2));
  return 0;
}

async function cmdInit(bypass, options) {
  const { writeFile } = await import('fs/promises');
  const { existsSync } = await import('fs');
  const { join } = await import('path');
  const { CONFIG_PATHS } = await import('./config.mjs');
  const { DEFAULT_CONFIG } = await import('./types.mjs');

  const target = join(process.cwd(), 'tsdb.config.json');
  if (existsSync(target) && !options.force) {
    throw new UsageError(`${target} already exists (pass --force to overwrite)`);
  }

  // An empty signature list means "use the built-in defaults" rather than
  // "never detect", which is what an empty array used to do silently.
  const config = structuredClone(DEFAULT_CONFIG);
  config.probe.blockSignatures = [];
  await writeFile(target, JSON.stringify(config, null, 2) + '\n', 'utf-8');

  info('Created config', { path: target });
  console.log(`Search order: ${CONFIG_PATHS.join('  ->  ')}`);
  return 0;
}

async function main(argv) {
  let options;
  try {
    options = parseArgs(argv);
  } catch (err) {
    error(err.message);
    console.log(HELP);
    return 2;
  }

  // --version must be handled before the help/empty-command branch: `--version`
  // on its own leaves no command, so the help branch would otherwise swallow it.
  if (options.version) {
    console.log(VERSION);
    return 0;
  }

  if (options.help || !options.command) {
    console.log(HELP);
    return 0;
  }

  const commands = {
    run: cmdRun,
    status: cmdStatus,
    add: cmdAdd,
    remove: cmdRemove,
    clear: cmdClear,
    probe: cmdProbe,
    config: cmdConfig,
    init: cmdInit
  };

  const handler = commands[options.command];
  if (!handler) {
    error(`Unknown command: ${options.command}`);
    console.log(HELP);
    return 2;
  }

  const bypass = new TailscaleDnsBypass({
    config: options.config,
    dryRun: options.dryRun,
    logLevel: options.verbose ? 'debug' : options.logLevel
  });

  try {
    return await handler(bypass, options);
  } catch (err) {
    if (err instanceof UsageError) {
      error(err.message);
      return 2;
    }
    error('Command failed', { command: options.command, error: err.message });
    if (options.verbose) console.error(err.stack);
    return 1;
  }
}

main(process.argv.slice(2))
  .then(code => { process.exitCode = code; })
  .catch(err => {
    error('Fatal error', { error: err.message });
    process.exitCode = 1;
  });