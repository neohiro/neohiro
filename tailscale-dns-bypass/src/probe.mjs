/**
 * HTTP probe for detecting blocked responses
 * @module probe
 *
 * Blocking at an exit node happens *above* TCP: the connection succeeds and the
 * server returns a normal 200 carrying an "Access Denied" page, or a 403/429/503.
 * This module fingerprints that layer.
 */

import { debug } from './logger.mjs';

/**
 * Ordered: the first signature that matches is reported as the reason, so put
 * the most specific ones first.
 */
export const DEFAULT_BLOCK_SIGNATURES = [
  'sorry, you have been blocked',
  'access to this site has been blocked',
  'your access has been blocked',
  'attention required',
  'checking your browser',
  'challenge-platform',
  'please enable javascript',
  'cf-ray',
  'ray id:',
  'cloudflare',
  'access denied',
  'blocked by',
  '403 forbidden',
  '429 too many requests'
];

const MAX_RESPONSE_BYTES = 1024 * 1024; // 1 MiB
const BLOCKING_STATUS = new Set([403, 451, 503]);

function assertDomain(domain) {
  if (typeof domain !== 'string' || domain.trim() === '') {
    throw new TypeError('domain must be a non-empty string');
  }
}

export class HttpProbe {
  constructor(config = {}) {
    this.urls = config.urls?.length ? config.urls : ['https://{domain}/'];
    this.timeoutMs = config.timeoutMs || 10000;
    this.blockSignatures = config.blockSignatures?.length
      ? config.blockSignatures
      : DEFAULT_BLOCK_SIGNATURES;
    this.maxResponseBytes = config.maxResponseBytes || MAX_RESPONSE_BYTES;
    this.userAgent = config.userAgent || 'tailscale-dns-bypass/1.0';
  }

  /**
   * @param {string} domain
   * @returns {Promise<import('./types.mjs').ProbeResult>}
   */
  async probe(domain) {
    assertDomain(domain);
    const startTime = Date.now();

    for (const url of this.urls) {
      const target = url.replace('{domain}', domain);
      let result;
      try {
        result = await this._fetch(target);
      } catch (err) {
        // Transport failure is not evidence of blocking: the host may simply be
        // unreachable, DNS-broken, or refusing our UA. Try the next URL.
        debug('Probe request failed', { domain, url: target, error: err.message });
        continue;
      }

      const latencyMs = Date.now() - startTime;
      const blocked = this._checkBlocked(result.body, result.statusCode);
      return {
        domain,
        blocked,
        statusCode: result.statusCode,
        blockReason: blocked ? this._identifyBlockReason(result.body, result.statusCode) : undefined,
        latencyMs,
        timestamp: Date.now()
      };
    }

    return {
      domain,
      blocked: false,
      statusCode: 0,
      blockReason: 'unreachable',
      latencyMs: Date.now() - startTime,
      timestamp: Date.now()
    };
  }

  /**
   * Bounded-concurrency probe. A single hanging domain must not stall the rest.
   * @param {string[]} domains
   * @param {number} concurrency
   * @returns {Promise<import('./types.mjs').ProbeResult[]>}
   */
  async probeMultiple(domains, concurrency = 5) {
    if (!Array.isArray(domains) || domains.length === 0) return [];

    const results = [];
    let cursor = 0;

    // Arrow function: `this` must bind to the probe instance.
    const worker = async () => {
      while (cursor < domains.length) {
        const domain = domains[cursor++];
        try {
          results.push(await this.probe(domain));
        } catch (err) {
          results.push({
            domain,
            blocked: false,
            statusCode: 0,
            blockReason: `error: ${err.message}`,
            latencyMs: 0,
            timestamp: Date.now()
          });
        }
      }
    };

    const workers = Array.from(
      { length: Math.max(1, Math.min(concurrency, domains.length)) },
      () => worker()
    );
    await Promise.all(workers);

    return results.sort((a, b) => a.domain.localeCompare(b.domain));
  }

  async _fetch(url) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'User-Agent': this.userAgent, 'Accept': 'text/html,*/*' },
        redirect: 'follow',
        signal: controller.signal
      });

      return { statusCode: response.status, body: await this._readCapped(response) };
    } finally {
      clearTimeout(timer);
    }
  }

  /**
   * Read at most `maxResponseBytes`. A block page is small; anything large is
   * not a block page, and buffering it unbounded is a memory risk.
   */
  async _readCapped(response) {
    const declared = Number(response.headers.get('content-length'));
    if (Number.isFinite(declared) && declared > this.maxResponseBytes) {
      throw new Error(`Response too large: ${declared} bytes`);
    }
    if (!response.body) return '';

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let body = '';
    let total = 0;

    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        total += value.byteLength;
        if (total > this.maxResponseBytes) {
          await reader.cancel().catch(() => {});
          throw new Error(`Response exceeded ${this.maxResponseBytes} bytes`);
        }
        body += decoder.decode(value, { stream: true });
      }
      body += decoder.decode();
    } finally {
      // cancel() may already have released the lock; releaseLock() throws if a
      // read is still pending, and a logging-side throw must not mask the result.
      try {
        reader.releaseLock();
      } catch {
        // already released
      }
    }

    return body;
  }

  _checkBlocked(body, statusCode) {
    if (BLOCKING_STATUS.has(statusCode)) return true;
    const lower = body.toLowerCase();
    return this.blockSignatures.some(sig => lower.includes(sig.toLowerCase()));
  }

  /** Prefer a body signature for a human-readable cause; fall back to the status. */
  _identifyBlockReason(body, statusCode) {
    const lower = body.toLowerCase();
    for (const sig of this.blockSignatures) {
      if (lower.includes(sig.toLowerCase())) return sig;
    }
    return `http_${statusCode}`;
  }
}