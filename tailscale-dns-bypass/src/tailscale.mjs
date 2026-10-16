/**
 * Tailscale integration for tailscale-dns-bypass
 * @module tailscale
 *
 * Tailscale's exit-node feature sends *all* traffic through the remote node.
 * Sites that fingerprint VPN/Tor egress answer with a block page (e.g. HTTP 200
 * with "Access Denied" or 403/429/503).
 *
 * Traffic flow requirement:
 * - Domains like weebly.com, secondlife.com, marketplace.secondlife.com, and others
 *   with anti-Tor/anti-VPN blocking must **skip Tor** (bypass Tor proxy/circuit routing)
 *   while **still routing through the Tailscale exit node and its underlying VPNs egress**
 *   (rather than bypassing the exit node via the local gateway).
 * - General traffic attempts TCP via Tor, filtering/bypassing Tor for blocked domains,
 *   and falling back to UDP via VPN nodes to the public exit.
 */

import { spawn } from 'child_process';
import { join } from 'path';
import { existsSync } from 'fs';
import { debug, info, warn, error } from './logger.mjs';

const CLI_TIMEOUT_MS = 30000;
const GATEWAY_TIMEOUT_MS = 5000;

const CIDR4 = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\/(\d{1,2})$/;

export function isValidIPv4Cidr(cidr) {
  const m = CIDR4.exec(String(cidr));
  if (!m) return false;
  for (let i = 1; i <= 4; i++) {
    const octet = Number(m[i]);
    if (!Number.isInteger(octet) || octet < 0 || octet > 255) return false;
  }
  const prefix = Number(m[5]);
  return prefix >= 0 && prefix <= 32;
}

/**
 * Local-only prefixes. Advertising these lets clients keep LAN access while
 * their default route still points at the exit node. Note this does not *by
 * itself* restore egress for public hosts; that is what the hosts-file entry
 * plus a more specific route does.
 */
export function generateSplitTunnelRoutes() {
  return ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '169.254.0.0/16', '127.0.0.0/8'];
}

export class TailscaleClient {
  constructor(config = {}) {
    this.enabled = config.enabled !== false;
    this.cliPath = this._findCli();
  }

  _findCli() {
    if (process.platform !== 'win32') return 'tailscale';
    const candidates = [
      join(process.env.ProgramFiles || 'C:\\Program Files', 'Tailscale', 'tailscale.exe'),
      join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Tailscale', 'tailscale.exe'),
      join(process.env.LOCALAPPDATA || '', 'Programs', 'Tailscale', 'tailscale.exe')
    ];
    return candidates.find(p => existsSync(p)) || 'tailscale';
  }

  async isAvailable() {
    if (!this.enabled) return false;
    return (await this._run(['version'])).code === 0;
  }

  /**
   * `tailscale status --json` is an object keyed by peer, with a `Self` entry.
   * Exit-node peers carry `ExitNode: true`. Guard the shape: a CLI upgrade that
   * reshapes this should degrade, not crash the run.
   */
  async getExitNodeStatus() {
    const result = await this._run(['status', '--json']);
    if (result.code !== 0) {
      debug('tailscale status failed', { code: result.code, stderr: result.stderr });
      return { usingExitNode: false };
    }

    let status;
    try {
      status = JSON.parse(result.stdout);
    } catch (err) {
      debug('tailscale status was not JSON', { error: err.message });
      return { usingExitNode: false };
    }

    const peers = Object.values(status || {}).filter(p => p && typeof p === 'object');
    const exitPeer = peers.find(p => p.ExitNode === true);
    if (!exitPeer) return { usingExitNode: false };

    const ips = exitPeer.TailscaleIPs || [];
    return { usingExitNode: true, exitNodeIp: ips[0] || null };
  }

  async advertiseRoutes(routes) {
    if (!this.enabled) return false;
    if (!Array.isArray(routes) || routes.length === 0) return true;

    const invalid = routes.filter(r => !isValidIPv4Cidr(r));
    if (invalid.length > 0) {
      error('Refusing to advertise invalid CIDR routes', { invalid });
      return false;
    }

    const result = await this._run(['set', '--advertise-routes', routes.join(',')]);
    if (result.code === 0) {
      info('Advertised routes', { routes });
      return true;
    }
    error('Failed to advertise routes', { routes, stderr: result.stderr });
    return false;
  }

  async acceptRoutes() {
    if (!this.enabled) return false;
    const result = await this._run(['set', '--accept-routes=true']);
    if (result.code === 0) {
      info('Accepting routes from exit node');
      return true;
    }
    warn('Failed to accept routes', { stderr: result.stderr });
    return false;
  }

  async getAdvertisedRoutes() {
    const result = await this._run(['status', '--json']);
    if (result.code !== 0) return [];
    try {
      const status = JSON.parse(result.stdout);
      return Array.isArray(status.Routes) ? status.Routes : [];
    } catch {
      return [];
    }
  }

  /** Run the CLI with a hard timeout so a wedged daemon cannot hang the run. */
  _run(args) {
    return new Promise(resolve => {
      let child;
      try {
        child = spawn(this.cliPath, args, { windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
      } catch (err) {
        resolve({ code: -1, stdout: '', stderr: err.message });
        return;
      }

      let stdout = '';
      let stderr = '';
      let settled = false;

      const finish = payload => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(payload);
      };

      child.stdout?.on('data', d => { stdout += d; });
      child.stderr?.on('data', d => { stderr += d; });

      const timer = setTimeout(() => {
        try { child.kill('SIGKILL'); } catch { /* already gone */ }
        finish({ code: -1, stdout, stderr: 'tailscale CLI timed out' });
      }, CLI_TIMEOUT_MS);

      child.on('error', err => finish({ code: -1, stdout, stderr: err.message }));
      child.on('close', code => finish({ code, stdout, stderr }));
    });
  }
}

/**
 * Best-effort local default gateway, used only for reporting. While an exit node
 * is selected this is the Tailscale interface, so treat the value as informational.
 * @returns {Promise<string|null>}
 */
export async function getLocalGateway() {
  if (process.platform === 'win32') {
    const out = await runCapture('powershell', [
      '-NoProfile',
      '-Command',
      "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1).NextHop"
    ], GATEWAY_TIMEOUT_MS);
    return out || null;
  }

  const out = await runCapture('ip', ['route', 'show', 'default'], GATEWAY_TIMEOUT_MS);
  const match = out && out.match(/default via (\d+\.\d+\.\d+\.\d+)/);
  return match ? match[1] : null;
}

function runCapture(cmd, args, timeoutMs) {
  return new Promise(resolve => {
    let child;
    try {
      child = spawn(cmd, args, { windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'] });
    } catch {
      resolve('');
      return;
    }
    let out = '';
    let settled = false;
    const finish = value => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(value);
    };
    child.stdout?.on('data', d => { out += d; });
    const timer = setTimeout(() => {
      try { child.kill('SIGKILL'); } catch { /* already gone */ }
      finish('');
    }, timeoutMs);
    child.on('error', () => finish(''));
    child.on('close', () => finish(out.trim()));
  });
}