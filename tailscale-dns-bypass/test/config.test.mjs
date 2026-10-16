/**
 * Tests for config loading and validation
 * @module test/config.test
 */

import { describe, it, before, after } from 'node:test';
import { strictEqual, ok, throws, rejects } from 'node:assert';
import { writeFile, mkdir, rm } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { loadConfig, validateConfig, getConfigPath, CONFIG_PATHS } from '../src/config.mjs';
import { DEFAULT_CONFIG } from '../src/types.mjs';

const valid = () => structuredClone(DEFAULT_CONFIG);

describe('config', () => {
  let testDir;

  before(async () => {
    testDir = join(tmpdir(), `tsdb-config-${Date.now()}`);
    await mkdir(testDir, { recursive: true });
  });

  after(async () => {
    await rm(testDir, { recursive: true, force: true }).catch(() => {});
  });

  const write = async (name, obj) => {
    const path = join(testDir, name);
    await writeFile(path, typeof obj === 'string' ? obj : JSON.stringify(obj), 'utf-8');
    return path;
  };

  describe('loadConfig', () => {
    it('fails loudly when an explicit path is missing', async () => {
      await rejects(() => loadConfig(join(testDir, 'nope.json')), /Config file not found/);
    });

    it('returns a usable config when called with no path', async () => {
      const config = await loadConfig();
      ok(Array.isArray(config.domains));
      ok(config.hosts.path.length > 0);
      ok(config.hosts.backupDir.length > 0);
    });

    it('reports a JSON syntax error with the path', async () => {
      const path = await write('bad.json', '{ not json');
      await rejects(() => loadConfig(path), /Invalid JSON/);
    });

    it('merges nested objects', async () => {
      const config = await loadConfig(await write('nested.json', { logging: { level: 'debug' } }));
      strictEqual(config.logging.level, 'debug');
      strictEqual(config.logging.format, DEFAULT_CONFIG.logging.format);
    });

    it('replaces arrays rather than merging them', async () => {
      const config = await loadConfig(
        await write('domains.json', { domains: [{ domain: 'only.com', enabled: true }] })
      );
      strictEqual(config.domains.length, 1);
      strictEqual(config.domains[0].domain, 'only.com');
    });

    it('does not mutate DEFAULT_CONFIG', async () => {
      await loadConfig(await write('mutate.json', { logging: { level: 'error' } }));
      strictEqual(DEFAULT_CONFIG.logging.level, 'info');
    });

    it('refuses a config that could poison the prototype', async () => {
      const path = await write('proto.json', '{"__proto__":{"polluted":true}}');
      await rejects(() => loadConfig(path), /could poison the prototype/);
    });

    it('refuses constructor/prototype keys too', async () => {
      const path = await write('ctor.json', '{"constructor":{"x":1}}');
      await rejects(() => loadConfig(path), /could poison the prototype/);
    });

    it('fills in platform defaults for empty paths', async () => {
      const config = await loadConfig(
        await write('auto.json', { hosts: { path: '' }, tailscale: { socket: '' } })
      );
      ok(config.hosts.path.length > 0);
      ok(config.hosts.backupDir.length > 0);
      ok(config.tailscale.socket.length > 0);
    });
  });

  describe('validateConfig', () => {
    it('accepts the defaults', () => {
      strictEqual(validateConfig(valid()), true);
    });

    it('rejects non-array domains', () => {
      throws(() => validateConfig({ ...valid(), domains: {} }), /domains must be an array/);
    });

    it('rejects a non-string domain', () => {
      throws(() => validateConfig({ ...valid(), domains: [{ domain: 42 }] }), /must be a string/);
    });

    it('rejects a malformed domain', () => {
      for (const bad of ['not a domain', 'nodot', 'trailing.', '-lead.com', 'a..b.com', '1.2.3.4']) {
        throws(
          () => validateConfig({ ...valid(), domains: [{ domain: bad }] }),
          /is not a valid domain name/,
          `expected "${bad}" to be rejected`
        );
      }
    });

    it('rejects duplicate domains case-insensitively', () => {
      const config = valid();
      config.domains = [{ domain: 'dup.com' }, { domain: 'DUP.com' }];
      throws(() => validateConfig(config), /duplicated/);
    });

    it('rejects a malformed subdomain', () => {
      const config = valid();
      config.domains = [{ domain: 'ok.com', subdomains: ['@', 'bad label'] }];
      throws(() => validateConfig(config), /is not a valid subdomain/);
    });

    it('accepts @ as the apex marker', () => {
      const config = valid();
      config.domains = [{ domain: 'ok.com', subdomains: ['@', 'www', 'api-v2'] }];
      strictEqual(validateConfig(config), true);
    });

    it('rejects out-of-range dns settings', () => {
      const slow = valid();
      slow.dns.timeoutMs = 10;
      throws(() => validateConfig(slow), /dns\.timeoutMs/);

      const ttl = valid();
      ttl.dns.cacheTtlMs = 5;
      throws(() => validateConfig(ttl), /dns\.cacheTtlMs/);

      const empty = valid();
      empty.dns.resolvers = [];
      throws(() => validateConfig(empty), /non-empty array/);
    });

    it('rejects an invalid log level', () => {
      const config = valid();
      config.logging.level = 'chatty';
      throws(() => validateConfig(config), /logging\.level/);
    });

    it('reports every problem at once', () => {
      const config = valid();
      config.domains = [{ domain: 'bad domain' }];
      config.logging.level = 'nope';
      let message = '';
      try { validateConfig(config); } catch (err) { message = err.message; }
      ok(message.includes('valid domain name'));
      ok(message.includes('logging.level'));
    });
  });

  describe('getConfigPath', () => {
    it('returns the first search location', () => {
      strictEqual(getConfigPath(), CONFIG_PATHS[0]);
    });
  });
});