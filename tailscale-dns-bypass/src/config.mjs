/**
 * Configuration loader for tailscale-dns-bypass
 * @module config
 */

import { readFile } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { DEFAULT_CONFIG } from './types.mjs';
import { debug, error } from './logger.mjs';

export const CONFIG_PATHS = [
  './tsdb.config.json',
  './config/tsdb.config.json',
  join(homedir(), '.config', 'tailscale-dns-bypass', 'config.json'),
  join(homedir(), '.tsdb.config.json')
];

// One or more labels, then an alphabetic TLD. Rejects bare hostnames, IPs and
// single-label names, all of which cannot be bypassed via the hosts file.
const DOMAIN_RE = /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i;
// "@" is the sentinel for the apex; otherwise a single DNS label.
const SUBDOMAIN_RE = /^(?=.{1,63}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/i;

function detectHostsPath() {
  if (process.platform !== 'win32') return '/etc/hosts';
  const systemRoot = process.env.SystemRoot || 'C:\\Windows';
  return join(systemRoot, 'System32', 'drivers', 'etc', 'hosts');
}

function detectTailscaleSocket() {
  if (process.platform === 'win32') return '\\\\.\\pipe\\tailscale';
  const candidates = [
    '/var/run/tailscale/tailscaled.sock',
    '/run/tailscale/tailscaled.sock',
    join(homedir(), 'Library', 'Application Support', 'Tailscale', 'tailscaled.sock')
  ];
  return candidates.find(p => existsSync(p)) || candidates[0];
}

/**
 * Keys that would let a config file reach into an object's prototype. `JSON.parse`
 * creates `__proto__` as a real own property, so `Object.entries` hands it to us
 * like any other key; assigning it would rewrite the merged object's prototype.
 * None of these are legitimate in this schema, so reject rather than drop.
 */
const FORBIDDEN_KEYS = new Set(['__proto__', 'constructor', 'prototype']);

/**
 * Objects merge recursively; arrays and scalars replace. Replacing arrays is the
 * correct semantic here: a user who writes `"domains": [...]` means exactly that
 * list, not "append to mine". Merging them made it impossible to remove an entry.
 */
function deepMerge(target, source) {
  const result = { ...target };
  for (const [key, value] of Object.entries(source)) {
    if (FORBIDDEN_KEYS.has(key)) {
      throw new Error(`Refusing config key that could poison the prototype: ${key}`);
    }
    const base = target[key];
    result[key] =
      value && typeof value === 'object' && !Array.isArray(value) &&
      base && typeof base === 'object' && !Array.isArray(base)
        ? deepMerge(base, value)
        : value;
  }
  return result;
}

export async function loadConfig(configPath = null) {
  let config = structuredClone(DEFAULT_CONFIG);

  if (configPath) {
    // An explicit path is a user instruction; silence about it is a bug.
    const raw = await readFile(configPath, 'utf-8').catch(err => {
      if (err.code === 'ENOENT') throw new Error(`Config file not found: ${configPath}`);
      throw err;
    });
    config = deepMerge(config, parseJson(raw, configPath));
    debug('Loaded config', { path: configPath });
  } else {
    const found = CONFIG_PATHS.find(p => existsSync(p));
    if (found) {
      const raw = await readFile(found, 'utf-8');
      config = deepMerge(config, parseJson(raw, found));
      debug('Loaded config', { path: found });
    } else {
      debug('No config file found, using defaults');
    }
  }

  if (!config.hosts.path) config.hosts.path = detectHostsPath();
  if (!config.hosts.backupDir) config.hosts.backupDir = join(homedir(), '.tsdb-backups');
  if (!config.tailscale.socket) config.tailscale.socket = detectTailscaleSocket();

  return config;
}

function parseJson(raw, path) {
  try {
    return JSON.parse(raw);
  } catch (err) {
    error('Config is not valid JSON', { path, error: err.message });
    throw new Error(`Invalid JSON in ${path}: ${err.message}`);
  }
}

export function validateConfig(config) {
  const errors = [];
  const seen = new Set();

  if (!Array.isArray(config.domains)) {
    errors.push('domains must be an array');
  } else {
    config.domains.forEach((entry, i) => {
      if (!entry || typeof entry.domain !== 'string') {
        errors.push(`domains[${i}].domain is required and must be a string`);
        return;
      }
      const domain = entry.domain.toLowerCase();
      if (!DOMAIN_RE.test(domain)) {
        errors.push(`domains[${i}].domain "${entry.domain}" is not a valid domain name`);
      }
      if (seen.has(domain)) errors.push(`domains[${i}].domain "${domain}" is duplicated`);
      seen.add(domain);

      if (entry.subdomains !== undefined) {
        if (!Array.isArray(entry.subdomains)) {
          errors.push(`domains[${i}].subdomains must be an array`);
        } else {
          entry.subdomains.forEach((sub, j) => {
            if (typeof sub !== 'string' || (sub !== '@' && !SUBDOMAIN_RE.test(sub))) {
              errors.push(`domains[${i}].subdomains[${j}] "${sub}" is not a valid subdomain`);
            }
          });
        }
      }
      if (entry.enabled !== undefined && typeof entry.enabled !== 'boolean') {
        errors.push(`domains[${i}].enabled must be a boolean`);
      }
    });
  }

  const dns = config.dns;
  if (dns) {
    if (!Array.isArray(dns.resolvers) || dns.resolvers.length === 0) {
      errors.push('dns.resolvers must be a non-empty array');
    }
    if (typeof dns.timeoutMs !== 'number' || dns.timeoutMs < 100) {
      errors.push('dns.timeoutMs must be a number >= 100');
    }
    if (typeof dns.cacheTtlMs !== 'number' || dns.cacheTtlMs < 1000) {
      errors.push('dns.cacheTtlMs must be a number >= 1000');
    }
  }

  const probe = config.probe;
  if (probe) {
    if (probe.urls !== undefined && !Array.isArray(probe.urls)) {
      errors.push('probe.urls must be an array');
    }
    if (typeof probe.timeoutMs !== 'undefined' &&
        (typeof probe.timeoutMs !== 'number' || probe.timeoutMs < 100)) {
      errors.push('probe.timeoutMs must be a number >= 100');
    }
    if (probe.blockSignatures !== undefined && !Array.isArray(probe.blockSignatures)) {
      errors.push('probe.blockSignatures must be an array');
    }
  }

  const hosts = config.hosts;
  if (hosts) {
    if (typeof hosts.createBackup !== 'boolean') errors.push('hosts.createBackup must be a boolean');
    if (hosts.maxBackups !== undefined &&
        (typeof hosts.maxBackups !== 'number' || hosts.maxBackups < 1)) {
      errors.push('hosts.maxBackups must be a number >= 1');
    }
  }

  const tailscale = config.tailscale;
  if (tailscale && typeof tailscale.enabled !== 'boolean') {
    errors.push('tailscale.enabled must be a boolean');
  }

  const logging = config.logging;
  if (logging) {
    if (!['debug', 'info', 'warn', 'error'].includes(logging.level)) {
      errors.push('logging.level must be one of: debug, info, warn, error');
    }
    if (!['json', 'text'].includes(logging.format)) {
      errors.push('logging.format must be one of: json, text');
    }
  }

  if (errors.length > 0) throw new Error(`Invalid config: ${errors.join('; ')}`);
  return true;
}

export function getConfigPath() {
  return CONFIG_PATHS[0];
}