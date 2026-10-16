/**
 * Tests for the HTTP block probe
 * @module test/probe.test
 */

import { describe, it } from 'node:test';
import { strictEqual, ok, rejects } from 'node:assert';
import { HttpProbe, DEFAULT_BLOCK_SIGNATURES } from '../src/probe.mjs';

describe('probe', () => {
  describe('HttpProbe', () => {
    it('falls back to the default signature list', () => {
      strictEqual(new HttpProbe({}).blockSignatures.length, DEFAULT_BLOCK_SIGNATURES.length);
    });

    it('treats an empty signature array as "use the defaults"', () => {
      strictEqual(new HttpProbe({ blockSignatures: [] }).blockSignatures.length,
        DEFAULT_BLOCK_SIGNATURES.length);
    });

    it('flags blocking status codes', () => {
      const probe = new HttpProbe({});
      for (const status of [403, 451, 503]) {
        strictEqual(probe._checkBlocked('', status), true, `expected ${status} to block`);
      }
      for (const status of [200, 301, 404, 500]) {
        strictEqual(probe._checkBlocked('', status), false, `expected ${status} not to block`);
      }
    });

    it('flags a 200 that carries a block page', () => {
      const probe = new HttpProbe({});
      strictEqual(probe._checkBlocked('<h1>Access Denied</h1>', 200), true);
      strictEqual(probe._checkBlocked('<p>Sorry, you have been blocked</p>', 200), true);
      strictEqual(probe._checkBlocked('<p>Ray ID: 8abc</p>', 200), true);
    });

    it('does not flag ordinary content', () => {
      strictEqual(new HttpProbe({})._checkBlocked('<h1>Welcome to my site</h1>', 200), false);
    });

    it('matches case-insensitively', () => {
      const probe = new HttpProbe({});
      strictEqual(probe._checkBlocked('ACCESS DENIED', 200), true);
      strictEqual(probe._checkBlocked('access denied', 200), true);
    });

    it('names the signature that matched', () => {
      strictEqual(new HttpProbe({})._identifyBlockReason('Access Denied', 403), 'access denied');
    });

    it('falls back to the status code when no signature matched', () => {
      const probe = new HttpProbe({ blockSignatures: ['never-matches'] });
      strictEqual(probe._identifyBlockReason('nothing here', 403), 'http_403');
    });

    it('rejects a non-string domain', async () => {
      await rejects(() => new HttpProbe({}).probe(''), /non-empty string/);
    });

    it('reports unreachable rather than blocked when the transport fails', async () => {
      const probe = new HttpProbe({ urls: ['https://{domain}:1/'], timeoutMs: 300 });
      const result = await probe.probe('does-not-exist.invalid');
      strictEqual(result.blocked, false, 'a connection error is not evidence of a block');
      strictEqual(result.statusCode, 0);
      strictEqual(result.blockReason, 'unreachable');
    });

    it('returns an empty result for an empty domain list', async () => {
      strictEqual((await new HttpProbe({}).probeMultiple([])).length, 0);
    });

    it('runs every domain even when some fail', async () => {
      const probe = new HttpProbe({ urls: ['https://{domain}:1/'], timeoutMs: 300 });
      const results = await probe.probeMultiple(['a.invalid', 'b.invalid'], 2);
      strictEqual(results.map(r => r.domain).join(','), 'a.invalid,b.invalid');
    });

    it('respects the concurrency bound', async () => {
      const probe = new HttpProbe({ urls: ['https://{domain}:1/'], timeoutMs: 300 });
      let live = 0;
      let peak = 0;
      const original = probe.probe.bind(probe);
      probe.probe = async d => {
        live++;
        peak = Math.max(peak, live);
        try {
          return await original(d);
        } finally {
          live--;
        }
      };
      await probe.probeMultiple(['a.invalid', 'b.invalid', 'c.invalid', 'd.invalid'], 2);
      ok(peak <= 2, `expected peak concurrency <= 2, saw ${peak}`);
    });

    it('rejects an oversized response via content-length', async () => {
      const probe = new HttpProbe({ maxResponseBytes: 10 });
      const response = new Response('x'.repeat(100), { headers: { 'content-length': '100' } });
      await rejects(() => probe._readCapped(response), /Response too large/);
    });

    it('reads a response that fits the cap', async () => {
      strictEqual(await new HttpProbe({ maxResponseBytes: 1024 })._readCapped(new Response('hello')), 'hello');
    });
  });
});