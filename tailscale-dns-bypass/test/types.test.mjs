/**
 * Tests for the default configuration
 * @module test/types.test
 */

import { describe, it } from 'node:test';
import { strictEqual, ok } from 'node:assert';
import { DEFAULT_CONFIG } from '../src/types.mjs';

describe('DEFAULT_CONFIG', () => {
  it('has every top-level section', () => {
    for (const key of ['domains', 'dns', 'probe', 'tailscale', 'hosts', 'logging']) {
      ok(DEFAULT_CONFIG[key], `missing ${key}`);
    }
  });

  it('ships the domains from the original report', () => {
    const domains = DEFAULT_CONFIG.domains.map(d => d.domain);
    for (const expected of ['weebly.com', 'secondlife.com', 'marketplace.secondlife.com']) {
      ok(domains.includes(expected), `missing ${expected}`);
    }
  });

  it('uses public resolvers so lookups bypass the exit node', () => {
    ok(DEFAULT_CONFIG.dns.resolvers.includes('1.1.1.1'));
    ok(DEFAULT_CONFIG.dns.resolvers.length > 0);
  });

  it('has sane timeouts', () => {
    ok(DEFAULT_CONFIG.dns.timeoutMs >= 100);
    ok(DEFAULT_CONFIG.probe.timeoutMs >= 100);
    ok(DEFAULT_CONFIG.dns.cacheTtlMs >= 1000);
  });

  it('probes by default only when asked', () => {
    // Probing sends a request to every configured domain; it must stay opt-in.
    strictEqual(DEFAULT_CONFIG.probe.enabled, false);
  });

  it('leaves block detection on the built-in defaults', () => {
    strictEqual(DEFAULT_CONFIG.probe.blockSignatures.length, 0);
  });

  it('backs up the hosts file by default', () => {
    strictEqual(DEFAULT_CONFIG.hosts.createBackup, true);
    ok(DEFAULT_CONFIG.hosts.maxBackups >= 1);
  });

  it('leaves platform paths for auto-detection', () => {
    strictEqual(DEFAULT_CONFIG.hosts.path, '');
    strictEqual(DEFAULT_CONFIG.tailscale.socket, '');
  });

  it('uses human-readable logging by default', () => {
    strictEqual(DEFAULT_CONFIG.logging.level, 'info');
    strictEqual(DEFAULT_CONFIG.logging.format, 'text');
  });
});