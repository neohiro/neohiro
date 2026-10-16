/**
 * Main orchestrator for tailscale-dns-bypass
 * @module index
 */

import { loadConfig, validateConfig } from './config.mjs';
import { DnsResolver, getBestIp } from './dns.mjs';
import { HostsManager } from './hosts.mjs';
import { TailscaleClient, generateSplitTunnelRoutes, getLocalGateway } from './tailscale.mjs';
import { HttpProbe } from './probe.mjs';
import { configureLogger, info, warn, error, debug } from './logger.mjs';

const APEX = '@';

export class TailscaleDnsBypass {
  constructor(options = {}) {
    this.options = options;
    this.config = null;
    this.dns = null;
    this.hosts = null;
    this.tailscale = null;
    this.probe = null;
  }

  async init() {
    this.config = await loadConfig(this.options.config);
    validateConfig(this.config);
    configureLogger({
      level: this.options.logLevel || this.config.logging.level,
      format: this.config.logging.format
    });

    this.dns = new DnsResolver(this.config.dns);
    this.hosts = new HostsManager(this.config);
    this.tailscale = new TailscaleClient(this.config.tailscale);
    this.probe = new HttpProbe(this.config.probe);

    info('Initialized tailscale-dns-bypass', {
      domains: this.config.domains.filter(d => d.enabled).length,
      probeEnabled: this.config.probe.enabled,
      tailscaleEnabled: this.config.tailscale.enabled,
      dryRun: Boolean(this.options.dryRun)
    });
  }

  /**
   * Refresh every configured domain.
   *
   * Config-owned entries that left the config are pruned; entries added with
   * `tsdb add` are tagged 'manual' and preserved. Pruning is never implicit
   * beyond that boundary.
   */
  async run() {
    if (!this.config) await this.init();

    const enabled = this.config.domains.filter(d => d.enabled);
    const results = { processed: 0, succeeded: 0, failed: 0, entries: [], errors: [] };

    if (this.config.probe.enabled && !this.options.dryRun) {
      await this._reportProbes(enabled.map(d => d.domain));
    }

    const resolved = [];
    for (const cfg of enabled) {
      results.processed++;
      try {
        resolved.push(await this._resolveEntry(cfg.domain, cfg.subdomains, 'config'));
        results.succeeded++;
      } catch (err) {
        results.failed++;
        results.errors.push({ domain: cfg.domain, error: err.message });
        error('Failed to process domain', { domain: cfg.domain, error: err.message });
      }
    }
    results.entries = resolved;

    const merge = this._group(resolved);

    if (this.options.dryRun) {
      const prior = await this.hosts.getManagedEntries();
      const stale = [...prior].filter(([h, v]) => v.tag === 'config' && !merge.has(h)).length;
      info('DRY RUN - hosts file unchanged', { resolved: merge.size, staleWouldBeRemoved: stale });
    } else if (merge.size > 0) {
      // Skipped when every domain failed to resolve: pruning then would discard
      // entries that are probably still correct.
      info('Hosts entries refreshed', await this.hosts.applyConfigEntries(merge));
    }

    if (this.config.tailscale.enabled) {
      if (this.options.dryRun) {
        info('DRY RUN - would configure Tailscale split tunnelling');
      } else {
        await this._configureTailscale();
      }
    }

    return results;
  }

  async _reportProbes(domains) {
    info('Probing domains for blocks...', { count: domains.length });
    for (const result of await this.probe.probeMultiple(domains)) {
      if (result.blocked) {
        warn('Domain appears blocked', {
          domain: result.domain,
          reason: result.blockReason,
          status: result.statusCode
        });
      } else {
        info('Domain reachable', {
          domain: result.domain,
          status: result.statusCode,
          latencyMs: result.latencyMs
        });
      }
    }
  }

  async _resolveEntry(domain, subdomains = [APEX, 'www'], tag) {
    const ip = await getBestIp(this.dns, domain);
    debug('Resolved domain', { domain, ip });
    return { domain, ip, tag, hostnames: buildHostnames(domain, subdomains), timestamp: Date.now() };
  }

  async _configureTailscale() {
    if (!(await this.tailscale.isAvailable())) {
      warn('Tailscale not available, skipping route configuration');
      return;
    }

    const status = await this.tailscale.getExitNodeStatus();
    if (!status.usingExitNode) {
      debug('Not using an exit node, skipping route advertisement');
      return;
    }

    info('Exit node detected, advertising local routes for split tunnelling', {
      exitNodeIp: status.exitNodeIp
    });

    await this.tailscale.advertiseRoutes(generateSplitTunnelRoutes());
    await this.tailscale.acceptRoutes();
  }

  async status() {
    if (!this.config) await this.init();

    const entries = await this.hosts.getManagedEntries();
    const available = await this.tailscale.isAvailable();
    const exitNode = available
      ? await this.tailscale.getExitNodeStatus()
      : { usingExitNode: false, exitNodeIp: null };
    const advertised = available ? await this.tailscale.getAdvertisedRoutes() : [];
    const localGateway = await getLocalGateway();

    return {
      managedDomains: entries.size,
      // One record per hosts line, not per hostname: several hostnames routinely
      // share an IP and tag, and listing each of them repeats the same line.
      entries: this._groupLines(entries),
      tailscale: {
        available,
        usingExitNode: exitNode.usingExitNode,
        exitNodeIp: exitNode.exitNodeIp ?? null,
        advertisedRoutes: advertised,
        localGateway
      },
      config: {
        domains: this.config.domains.filter(d => d.enabled).map(d => d.domain),
        probeEnabled: this.config.probe.enabled
      }
    };
  }

  /** @returns {Promise<number>} Hostnames removed */
  async clear() {
    if (!this.config) await this.init();
    return this.hosts.clearManagedEntries();
  }

  /**
   * Add a domain without disturbing anything else already managed.
   * @returns {Promise<import('./types.mjs').DomainEntry>}
   */
  async addDomain(domain, subdomains = [APEX, 'www']) {
    if (!this.config) await this.init();
    const resolved = await this._resolveEntry(domain, subdomains, 'manual');
    await this.hosts.addEntries(
      new Map(resolved.hostnames.map(h => [h, { ip: resolved.ip, hostnames: [h], tag: 'manual' }]))
    );
    return resolved;
  }

  /**
   * Remove a domain and any of its subdomains. Returns false when nothing
   * matched, so a caller can distinguish "gone" from "was never there".
   * @returns {Promise<boolean>}
   */
  async removeDomain(domain) {
    if (!this.config) await this.init();
    const needle = String(domain).toLowerCase();
    const entries = await this.hosts.getManagedEntries();

    const targets = [...entries.keys()].filter(
      host => host === needle || host.endsWith(`.${needle}`)
    );
    if (targets.length === 0) return false;

    await this.hosts.removeEntries(targets);
    return true;
  }

  /** Collapse resolved entries into one record per hostname. */
  _group(entries) {
    const grouped = new Map();
    for (const value of entries) {
      for (const hostname of value.hostnames) {
        grouped.set(hostname, { ip: value.ip, hostnames: [hostname], tag: value.tag });
      }
    }
    return grouped;
  }

  /**
   * Collapse a parsed managed map into one record per (ip, tag) line.
   * @param {Map<string, {ip: string, hostnames: string[], tag: string}>} entries
   */
  _groupLines(entries) {
    const byLine = new Map();
    for (const [hostname, value] of entries) {
      const key = `${value.ip}\t${value.tag}`;
      if (!byLine.has(key)) byLine.set(key, { ip: value.ip, tag: value.tag, hostnames: new Set() });
      byLine.get(key).hostnames.add(hostname);
    }
    return [...byLine.values()].map(line => ({
      ip: line.ip,
      tag: line.tag,
      allHostnames: [...line.hostnames].sort(),
      hostname: [...line.hostnames].sort()[0]
    }));
  }
}

/** `"@"` maps to the apex; anything else is treated as a label to prefix. */
export function buildHostnames(domain, subdomains = [APEX, 'www']) {
  const base = String(domain).toLowerCase();
  const labels = Array.isArray(subdomains) && subdomains.length > 0 ? subdomains : [APEX];
  return [...new Set(labels.map(label => (label === APEX ? base : `${String(label).toLowerCase()}.${base}`)))];
}

export { DEFAULT_CONFIG } from './types.mjs';
export { DnsResolver, getBestIp } from './dns.mjs';
export { HostsManager } from './hosts.mjs';
export { TailscaleClient, generateSplitTunnelRoutes, getLocalGateway } from './tailscale.mjs';
export { HttpProbe, DEFAULT_BLOCK_SIGNATURES } from './probe.mjs';
export { configureLogger } from './logger.mjs';
export { loadConfig, validateConfig } from './config.mjs';