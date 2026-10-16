/**
 * Tests for the DNS resolver
 * @module test/dns.test
 */

import { describe, it } from 'node:test';
import { strictEqual, rejects } from 'node:assert';
import { DnsResolver, getBestIp } from '../src/dns.mjs';

const sameArray = (actual, expected) => {
  strictEqual(actual.length, expected.length);
  actual.forEach((v, i) => strictEqual(v, expected[i]));
};

describe('dns', () => {
  describe('DnsResolver', () => {
    it('applies defaults when config is empty', () => {
      const resolver = new DnsResolver();
      strictEqual(resolver.timeoutMs, 5000);
      sameArray(resolver.resolvers, ['1.1.1.1', '8.8.8.8']);
    });

    it('honours a custom cache size limit', () => {
      const resolver = new DnsResolver({ cacheMaxSize: 2, cacheTtlMs: 60000 });
      resolver.cache.set('a', ['1.1.1.1']);
      resolver.cache.set('b', ['2.2.2.2']);
      resolver.cache.set('c', ['3.3.3.3']);
      strictEqual(resolver.cache.size, 2);
      strictEqual(resolver.cache.get('a'), null, 'oldest key should be evicted');
    });

    it('expires entries once the ttl elapses', async () => {
      const resolver = new DnsResolver({ cacheTtlMs: 1, cacheMaxSize: 10 });
      resolver.cache.set('a', ['1.1.1.1']);
      await new Promise(r => setTimeout(r, 10));
      strictEqual(resolver.cache.get('a'), null);
    });

    it('clears the cache', () => {
      const resolver = new DnsResolver();
      resolver.cache.set('a', ['1.1.1.1']);
      resolver.clearCache();
      strictEqual(resolver.cache.size, 0);
    });

    it('rejects a non-string domain', async () => {
      const resolver = new DnsResolver();
      await rejects(() => resolver.resolve4(''), /non-empty string/);
      await rejects(() => resolver.resolve4(null), /non-empty string/);
      await rejects(() => resolver.resolveAll(undefined), /non-empty string/);
    });
  });

  describe('getBestIp', () => {
    const stub = (v4, v6) => ({ resolveAll: async () => ({ ipv4: v4, ipv6: v6 }) });

    it('prefers IPv4', async () => {
      strictEqual(await getBestIp(stub(['192.0.2.1'], ['2001:db8::1']), 'example.com'), '192.0.2.1');
    });

    it('falls back to IPv6 when there is no A record', async () => {
      strictEqual(await getBestIp(stub([], ['2001:db8::1']), 'example.com'), '2001:db8::1');
    });

    it('throws when the name has no records at all', async () => {
      await rejects(() => getBestIp(stub([], []), 'example.com'), /No IP addresses found/);
    });

    it('validates the domain before resolving', async () => {
      await rejects(() => getBestIp(stub(['1.1.1.1'], []), ''), /non-empty string/);
    });
  });
});