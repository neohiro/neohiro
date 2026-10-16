/**
 * End-to-end tests for the CLI contract: argument parsing and exit codes.
 * @module test/cli.test
 *
 * Runs the real binary in a child process. Exit codes are the part of this tool
 * that scripts depend on, so they are tested as observed rather than by calling
 * internals.
 */

import { describe, it, before, after } from 'node:test';
import { strictEqual, ok } from 'node:assert';
import { execFile } from 'child_process';
import { writeFile, mkdir, rm } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { tmpdir } from 'os';

const CLI = join(dirname(dirname(fileURLToPath(import.meta.url))), 'src', 'cli.mjs');

function run(args, options = {}) {
  return new Promise(resolve => {
    execFile(process.execPath, [CLI, ...args], { timeout: 30000, ...options },
      (err, stdout, stderr) => {
        resolve({ code: err?.code ?? 0, stdout, stderr });
      });
  });
}

describe('cli', () => {
  let testDir;
  let hostsPath;
  let configPath;

  before(async () => {
    testDir = join(tmpdir(), `tsdb-cli-${Date.now()}`);
    await mkdir(join(testDir, 'backups'), { recursive: true });
    hostsPath = join(testDir, 'hosts');
    await writeFile(hostsPath, '127.0.0.1 localhost\n', 'utf-8');
    configPath = join(testDir, 'config.json');
    await writeFile(configPath, JSON.stringify({
      domains: [{ domain: 'example.com', subdomains: ['@'], enabled: true }],
      tailscale: { enabled: false },
      hosts: { path: hostsPath, backupDir: join(testDir, 'backups'), createBackup: false },
      logging: { level: 'error', format: 'text' }
    }), 'utf-8');
  });

  after(async () => {
    await rm(testDir, { recursive: true, force: true }).catch(() => {});
  });

  describe('help and version', () => {
    it('prints help with no arguments', async () => {
      const r = await run([]);
      strictEqual(r.code, 0);
      ok(r.stdout.includes('USAGE:'));
    });

    it('prints help for --help', async () => {
      strictEqual((await run(['--help'])).code, 0);
    });

    it('prints the version', async () => {
      const r = await run(['--version']);
      strictEqual(r.code, 0);
      // Bare semver on one line, not the help banner.
      ok(/^\d+\.\d+\.\d+\s*$/.test(r.stdout.trim()), `unexpected: ${JSON.stringify(r.stdout)}`);
    });

    it('documents the exit codes', async () => {
      ok((await run(['--help'])).stdout.includes('EXIT CODES'));
    });
  });

  describe('usage errors exit 2', () => {
    it('rejects an unknown command', async () => {
      strictEqual((await run(['bogus'])).code, 2);
    });

    it('rejects an unknown option', async () => {
      strictEqual((await run(['--nope'])).code, 2);
    });

    it('rejects a value flag with no value', async () => {
      strictEqual((await run(['status', '--config'])).code, 2);
    });

    it('rejects an option used as the value of a flag', async () => {
      // Without this guard '--config --dry-run' silently consumes --dry-run as
      // the path and runs with no config at all.
      strictEqual((await run(['status', '--config', '--dry-run'])).code, 2);
    });

    it('requires a domain argument for add', async () => {
      strictEqual((await run(['add'])).code, 2);
    });

    it('requires a domain argument for remove', async () => {
      strictEqual((await run(['remove'])).code, 2);
    });

    it('requires a domain argument for probe', async () => {
      strictEqual((await run(['probe'])).code, 2);
    });

    it('refuses to clear on a non-TTY without --force', async () => {
      const r = await run(['clear', '--config', configPath]);
      strictEqual(r.code, 2);
      ok(r.stderr.includes('--force'));
    });
  });

  describe('informational commands', () => {
    it('prints the effective config', async () => {
      const r = await run(['config', '--config', configPath]);
      strictEqual(r.code, 0);
      const parsed = JSON.parse(r.stdout);
      strictEqual(parsed.domains[0].domain, 'example.com');
    });

    it('reports status without touching the hosts file', async () => {
      const r = await run(['status', '--config', configPath]);
      strictEqual(r.code, 0);
      ok(r.stdout.includes('Managed entries'));
      ok(r.stdout.includes('Tailscale'));
    });

    it('lists each hosts line once, not once per hostname', async () => {
      await run(['clear', '--force', '--config', configPath]);
      await writeFile(configPath, JSON.stringify({
        domains: [{ domain: 'multi.com', subdomains: ['@', 'www'], enabled: true }],
        tailscale: { enabled: false },
        hosts: { path: hostsPath, backupDir: join(testDir, 'backups'), createBackup: false },
        logging: { level: 'error', format: 'text' }
      }), 'utf-8');

      // Seed two hostnames that share an IP, so they land on a single line.
      await writeFile(hostsPath,
        '127.0.0.1 localhost\n\n' +
        '# === tailscale-dns-bypass managed entries start ===\n' +
        '192.0.2.1\tmulti.com www.multi.com\t# tsdb:config\n' +
        '# === tailscale-dns-bypass managed entries end ===\n', 'utf-8');

      const r = await run(['status', '--config', configPath]);
      strictEqual(r.code, 0);

      // Managed entries are reported per line, so the hostname appears once
      // even though the line carries two. Assert on that section only: the
      // Config block legitimately names the domain again.
      const managed = r.stdout.slice(0, r.stdout.indexOf('\nTailscale'));
      const mentions = managed.split('\n').filter(l => l.includes('multi.com')).length;
      strictEqual(mentions, 1, `expected one entry line, got:\n${managed}`);
    });
  });
});