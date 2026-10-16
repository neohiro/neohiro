/**
 * Type definitions and defaults for tailscale-dns-bypass
 * @module types
 */

/**
 * @typedef {Object} DomainConfig
 * @property {string} domain - The domain name (e.g., "weebly.com")
 * @property {string[]} [subdomains] - Subdomains to bypass; "@" means the apex (default: ["@", "www"])
 * @property {string} [reason] - Human-readable reason for bypass
 * @property {boolean} [enabled=true] - Whether this entry is active
 */

/**
 * @typedef {Object} DomainEntry
 * @property {string} domain
 * @property {string} ip
 * @property {string[]} hostnames
 * @property {number} timestamp
 * @property {string} source - "config" | "manual"
 */

/**
 * @typedef {Object} HostsEntry
 * @property {string} ip
 * @property {string[]} hostnames
 */

/**
 * @typedef {Object} ProbeResult
 * @property {string} domain
 * @property {boolean} blocked
 * @property {number} statusCode
 * @property {string} [blockReason]
 * @property {number} latencyMs
 * @property {number} timestamp
 */

/**
 * @typedef {Object} DiffResult
 * @property {number} added
 * @property {number} removed
 * @property {number} updated
 */

/**
 * @typedef {Object} Config
 * @property {DomainConfig[]} domains
 * @property {{resolvers: string[], timeoutMs: number, cacheTtlMs: number, cacheMaxSize?: number}} dns
 * @property {{enabled: boolean, urls: string[], timeoutMs: number, blockSignatures: string[]}} probe
 * @property {{enabled: boolean, socket: string}} tailscale
 * @property {{path: string, backupDir: string, createBackup: boolean, maxBackups?: number}} hosts
 * @property {{level: string, format: string}} logging
 */

/**
 * @typedef {Object} CliOptions
 * @property {string} [config] - Path to config file
 * @property {boolean} [dryRun] - Show what would be done without making changes
 * @property {boolean} [verbose] - Verbose output
 * @property {boolean} [force] - Force operation without confirmation
 * @property {string} [logLevel] - Override log level
 */

/** @type {Config} */
export const DEFAULT_CONFIG = {
  domains: [
    { domain: 'weebly.com', subdomains: ['@', 'www'], reason: 'Blocks Tailscale exit nodes', enabled: true },
    { domain: 'secondlife.com', subdomains: ['@', 'www', 'marketplace'], reason: 'Blocks Tailscale exit nodes', enabled: true },
    { domain: 'marketplace.secondlife.com', subdomains: ['@'], reason: 'Blocks Tailscale exit nodes', enabled: true }
  ],
  dns: {
    resolvers: ['1.1.1.1', '8.8.8.8'],
    timeoutMs: 5000,
    cacheTtlMs: 300000,
    cacheMaxSize: 1000
  },
  probe: {
    enabled: false,
    urls: ['https://{domain}/'],
    timeoutMs: 10000,
    blockSignatures: []
  },
  tailscale: {
    enabled: true,
    socket: ''
  },
  hosts: {
    path: '',
    backupDir: '',
    createBackup: true,
    maxBackups: 10
  },
  logging: {
    level: 'info',
    format: 'text'
  }
};