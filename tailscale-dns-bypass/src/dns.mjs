/**
 * DNS resolver with TTL + size bounded caching
 * @module dns
 */

import { Resolver } from 'dns/promises';
import { debug, warn, error } from './logger.mjs';

const DEFAULT_MAX_CACHE_SIZE = 1000;

/** Bounded, TTL-expiring map. Oldest insertion is evicted when full (Map preserves insertion order). */
class DnsCache {
  constructor(ttlMs, maxSize) {
    this.ttlMs = ttlMs;
    this.maxSize = maxSize;
    this.cache = new Map();
  }

  get(key) {
    const entry = this.cache.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.cache.delete(key);
      return null;
    }
    return entry.value;
  }

  set(key, value) {
    if (this.cache.size >= this.maxSize) {
      const oldest = this.cache.keys().next();
      if (!oldest.done) this.cache.delete(oldest.value);
    }
    this.cache.set(key, { value, timestamp: Date.now() });
  }

  get size() {
    return this.cache.size;
  }

  clear() {
    this.cache.clear();
  }
}

/**
 * `dns/promises`' Resolver does not accept an AbortSignal, so an AbortController
 * here would silently never fire. Race the query against a timer instead; the
 * underlying query is abandoned when the timer wins.
 */
function resolveWithTimeout(resolver, domain, type, timeoutMs) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`DNS timeout after ${timeoutMs}ms`)), timeoutMs);
  });
  return Promise.race([resolver.resolve(domain, type), timeout]).finally(() => clearTimeout(timer));
}

function assertDomain(domain) {
  if (typeof domain !== 'string' || domain.trim() === '') {
    throw new TypeError('domain must be a non-empty string');
  }
}

export class DnsResolver {
  constructor(config = {}) {
    this.resolvers = config.resolvers || ['1.1.1.1', '8.8.8.8'];
    this.timeoutMs = config.timeoutMs || 5000;
    this.cache = new DnsCache(config.cacheTtlMs || 300000, config.cacheMaxSize || DEFAULT_MAX_CACHE_SIZE);
    this.resolver = new Resolver({ timeout: this.timeoutMs, tries: 2 });
    this.resolver.setServers(this.resolvers);
  }

  /**
   * @param {string} domain
   * @returns {Promise<string[]>}
   */
  async resolve4(domain) {
    assertDomain(domain);
    const cacheKey = `A:${domain}`;
    const cached = this.cache.get(cacheKey);
    if (cached) {
      debug('DNS cache hit', { domain, ips: cached });
      return cached;
    }

    try {
      const ips = await resolveWithTimeout(this.resolver, domain, 'A', this.timeoutMs);
      this.cache.set(cacheKey, ips);
      debug('DNS resolved', { domain, ips });
      return ips;
    } catch (err) {
      error('DNS resolution failed', { domain, error: err.message });
      throw new Error(`Failed to resolve ${domain}: ${err.message}`);
    }
  }

  /**
   * AAAA failure is not fatal: a domain with no IPv6 record is normal.
   * @param {string} domain
   * @returns {Promise<string[]>}
   */
  async resolve6(domain) {
    assertDomain(domain);
    const cacheKey = `AAAA:${domain}`;
    const cached = this.cache.get(cacheKey);
    if (cached) {
      debug('DNS cache hit', { domain, ips: cached });
      return cached;
    }

    try {
      const ips = await resolveWithTimeout(this.resolver, domain, 'AAAA', this.timeoutMs);
      this.cache.set(cacheKey, ips);
      debug('DNS resolved', { domain, ips });
      return ips;
    } catch (err) {
      warn('DNS AAAA resolution failed (may be expected)', { domain, error: err.message });
      return [];
    }
  }

  /**
   * @param {string} domain
   * @returns {Promise<{ipv4: string[], ipv6: string[]}>}
   */
  async resolveAll(domain) {
    assertDomain(domain);
    const [ipv4, ipv6] = await Promise.allSettled([
      this.resolve4(domain),
      this.resolve6(domain)
    ]);
    return {
      ipv4: ipv4.status === 'fulfilled' ? ipv4.value : [],
      ipv6: ipv6.status === 'fulfilled' ? ipv6.value : []
    };
  }

  clearCache() {
    this.cache.clear();
  }
}

/**
 * IPv4 first: the hosts-file bypass is IPv4-centric and dual-stack entries in a
 * hosts file are inconsistently honoured across resolvers.
 * @param {DnsResolver} resolver
 * @param {string} domain
 * @returns {Promise<string>}
 */
export async function getBestIp(resolver, domain) {
  assertDomain(domain);
  const { ipv4, ipv6 } = await resolver.resolveAll(domain);
  if (ipv4.length > 0) return ipv4[0];
  if (ipv6.length > 0) return ipv6[0];
  throw new Error(`No IP addresses found for ${domain}`);
}