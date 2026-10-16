/**
 * Integration tests for the orchestrator
 * @module test/index.test
 */

import { describe, it, before, after, beforeEach } from 'node:test';
import { strictEqual, ok, deepStrictEqual, rejects } from 'node:assert';
import { writeFile, mkdir, rm, readFile } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { TailscaleDnsBypass, buildHostnames } from '../src/index.mjs';

describe('buildHostnames', () => {
  it('maps @ to the apex', () => {
    deepStrictEqual(buildHostnames('Example.com', ['@']), ['example.com']);
  });

  it('prefixes other labels', () => {
    deepStrictEqual(buildHostnames('example.com', ['www', 'api']),
      ['www.example.com', 'api.example.com']);
  });

  it('de-duplicates', () => {
    deepStrictEqual(buildHostnames('example.com', ['@', '@', 'www', 'www']),
      ['example.com', 'www.example.com']);
  });

  it('defaults to apex plus www', () => {
    deepStrictEqual(buildHostnames('example.com'), ['example.com', 'www.example.com']);
  });

  it('never yields a leading-dot label', () => {
    for (const label of ['@', 'www', 'api']) {
      ok(buildHostnames('example.com', [label]).every(h => !h.startsWith('.')));
    }
  });
});

describe('TailscaleDnsBypass', () => {
  let testDir;
  let hostsPath;
  let backupDir;
  let configPath;
  let bypass;

  const writeConfig = domains => writeFile(configPath, JSON.stringify({
    domains,
    tailscale: { enabled: false },
    hosts: { path: hostsPath, backupDir, createBackup: false, maxBackups: 5 },
    logging: { level: 'error', format: 'text' }
  }), 'utf-8');

  const managed = async target => target.hosts.getManagedEntries();

  before(async () => {
    testDir = join(tmpdir(), `tsdb-index-${Date.now()}`);
    backupDir = join(testDir, 'backups');
    await mkdir(backupDir, { recursive: true });
    hostsPath = join(testDir, 'hosts');
    configPath = join(testDir, 'config.json');
  });

  after(async () => {
    await rm(testDir, { recursive: true, force: true }).catch(() => {});
  });

  beforeEach(async () => {
    await writeFile(hostsPath, '127.0.0.1 localhost\n', 'utf-8');
    await writeConfig([
      { domain: 'example.com', subdomains: ['@', 'www'], enabled: true },
      { domain: 'disabled.com', enabled: false }
    ]);
    bypass = new TailscaleDnsBypass({ config: configPath });
    await bypass.init();
    bypass.dns.resolveAll = async () => ({ ipv4: ['192.0.2.1'], ipv6: [] });
  });

  describe('init', () => {
    it('loads only the enabled domains', () => {
      strictEqual(bypass.config.domains.filter(d => d.enabled).length, 1);
    });
  });

  describe('addDomain', () => {
    it('resolves and records the entry', async () => {
      const e = await bypass.addDomain('manual.com', ['@', 'api']);
      strictEqual(e.domain, 'manual.com');
      strictEqual(e.ip, '192.0.2.1');
      deepStrictEqual(e.hostnames, ['manual.com', 'api.manual.com']);
    });

    it('tags the entry as manual', async () => {
      await bypass.addDomain('manual.com', ['@']);
      strictEqual((await managed(bypass)).get('manual.com').tag, 'manual');
    });

    it('rejects a blank domain', async () => {
      await rejects(() => bypass.addDomain(''), /non-empty string/);
    });

    it('does not delete entries added earlier', async () => {
      await bypass.addDomain('first.com', ['@']);
      await bypass.addDomain('second.com', ['@']);
      deepStrictEqual([...(await managed(bypass)).keys()].sort(), ['first.com', 'second.com']);
    });

    it('survives a subsequent run', async () => {
      await bypass.addDomain('manual.com', ['@']);
      await bypass.run();
      ok((await managed(bypass)).has('manual.com'));
    });
  });

  describe('run', () => {
    it('writes the configured domains', async () => {
      const result = await bypass.run();
      strictEqual(result.succeeded, 1);
      strictEqual(result.failed, 0);
      ok((await managed(bypass)).has('example.com'));
    });

    it('tags its writes as config-owned', async () => {
      await bypass.run();
      strictEqual((await managed(bypass)).get('example.com').tag, 'config');
    });

    it('reports a per-domain failure without aborting the run', async () => {
      bypass.dns.resolveAll = async domain => {
        if (domain === 'example.com') throw new Error('boom');
        return { ipv4: ['192.0.2.9'], ipv6: [] };
      };
      const result = await bypass.run();
      strictEqual(result.failed, 1);
      strictEqual(result.errors[0].domain, 'example.com');
    });

    it('writes nothing in dry-run mode', async () => {
      const dry = new TailscaleDnsBypass({ config: configPath, dryRun: true });
      await dry.init();
      dry.dns.resolveAll = async () => ({ ipv4: ['192.0.2.1'], ipv6: [] });
      await dry.run();
      strictEqual((await managed(dry)).size, 0);
    });

    it('prunes a configured domain removed from the config', async () => {
      await bypass.run();
      ok((await managed(bypass)).has('www.example.com'));

      await writeConfig([{ domain: 'other.com', subdomains: ['@'], enabled: true }]);
      const next = new TailscaleDnsBypass({ config: configPath });
      await next.init();
      next.dns.resolveAll = async () => ({ ipv4: ['192.0.2.1'], ipv6: [] });
      await next.run();

      const after_ = await managed(next);
      ok(!after_.has('example.com'), 'stale configured entry should be pruned');
      ok(!after_.has('www.example.com'), 'stale subdomain should be pruned');
      ok(after_.has('other.com'));
    });

    it('keeps manually added domains that no config entry claims', async () => {
      await bypass.addDomain('manual.com', ['@']);
      await bypass.run();
      ok((await managed(bypass)).has('manual.com'));
    });
  });

  describe('removeDomain', () => {
    it('removes the domain and its subdomains', async () => {
      await bypass.addDomain('shop.com', ['@', 'www', 'api']);
      strictEqual(await bypass.removeDomain('shop.com'), true);
      strictEqual((await managed(bypass)).size, 0);
    });

    it('returns false when nothing matched', async () => {
      strictEqual(await bypass.removeDomain('absent.com'), false);
    });

    it('does not remove a merely similar domain', async () => {
      await bypass.addDomain('shop.com', ['@']);
      await bypass.addDomain('notshop.com', ['@']);
      await bypass.removeDomain('shop.com');

      const after_ = await managed(bypass);
      ok(after_.has('notshop.com'));
      ok(!after_.has('shop.com'));
    });

    it('leaves the hosts file intact for other tools', async () => {
      await bypass.addDomain('shop.com', ['@']);
      await bypass.removeDomain('shop.com');
      ok((await readFile(hostsPath, 'utf-8')).includes('127.0.0.1 localhost'));
    });
  });

  describe('clear', () => {
    it('removes everything it manages and reports the count', async () => {
      await bypass.addDomain('a.com', ['@']);
      await bypass.addDomain('b.com', ['@']);
      strictEqual(await bypass.clear(), 2);
      strictEqual((await managed(bypass)).size, 0);
    });

    it('is a no-op when nothing is managed', async () => {
      strictEqual(await bypass.clear(), 0);
    });
  });

  describe('status', () => {
    it('reports managed entries, ownership and tailscale state', async () => {
      await bypass.addDomain('a.com', ['@', 'www']);
      const status = await bypass.status();

      strictEqual(status.managedDomains, 2);
      strictEqual(status.entries[0].allHostnames.length, 2);
      strictEqual(status.entries[0].tag, 'manual');
      strictEqual(status.tailscale.usingExitNode, false);
      deepStrictEqual(status.config.domains, ['example.com']);
    });
  });
});