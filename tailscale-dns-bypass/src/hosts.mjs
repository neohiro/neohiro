/**
 * Hosts file manager for tailscale-dns-bypass
 * @module hosts
 *
 * All writes are confined to a single delimited block; content outside the
 * markers is preserved byte-for-byte so the tool coexists with whatever else
 * manages the hosts file.
 *
 * ## Ownership tagging
 *
 * Every managed line carries a trailing `# tsdb:<tag>` comment recording whether
 * it was written from the config file (`config`) or by an explicit `tsdb add`
 * (`manual`). That is what lets `run()` refresh config-owned entries and prune
 * those that left the config, while leaving deliberately added domains alone --
 * without a separate state file to remember who owns what. A trailing `#`
 * comment is valid in both the Unix and Windows hosts-file formats.
 */

import { readFile, writeFile, mkdir, readdir, unlink } from 'fs/promises';
import { join } from 'path';
import { debug, info, warn } from './logger.mjs';

const TSDB_MARKER_START = '# === tailscale-dns-bypass managed entries start ===';
const TSDB_MARKER_END = '# === tailscale-dns-bypass managed entries end ===';

const TAG_PREFIX = '# tsdb:';
const TAGS = new Set(['config', 'manual']);
const DEFAULT_MAX_BACKUPS = 10;

/** A hostname is a DNS label sequence; whitespace or `#` would corrupt the record. */
const SAFE_HOSTNAME = /^[A-Za-z0-9._-]+$/;
const SAFE_IPV4 = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;

/**
 * @param {string} ip
 * @param {string[]} hostnames
 * @param {string} [tag]
 */
export function entry(ip, hostnames, tag = 'manual') {
  return { ip, hostnames, tag };
}

export class HostsManager {
  constructor(config) {
    this.hostsPath = config.hosts.path;
    this.backupDir = config.hosts.backupDir;
    this.createBackup = config.hosts.createBackup !== false;
    this.maxBackups = config.hosts.maxBackups || DEFAULT_MAX_BACKUPS;
  }

  async read() {
    try {
      return await readFile(this.hostsPath, 'utf-8');
    } catch (err) {
      if (err.code === 'ENOENT') return '';
      if (err.code === 'EACCES' || err.code === 'EPERM') {
        throw new Error(
          `Permission denied reading ${this.hostsPath}. ` +
          'Run elevated (Administrator on Windows, sudo on Linux/macOS).'
        );
      }
      throw new Error(`Failed to read hosts file: ${err.message}`);
    }
  }

  /**
   * Write the hosts file.
   *
   * Passing `expected` (the content the caller's change was based on) enables an
   * optimistic concurrency check: the write is refused if the file moved
   * underneath. This is not an atomic replace -- another process can still win
   * between the re-read and `writeFile` -- but it turns a silent lost update into
   * an explicit error, which is what matters when other tools share this file.
   */
  async write(content, expected) {
    if (expected !== undefined) {
      const current = await this.read();
      if (current !== expected) {
        throw new Error(
          `${this.hostsPath} changed on disk while it was being edited; ` +
          'nothing was written. Re-run the command.'
        );
      }
    }
    if (this.createBackup) await this._createBackup();
    await writeFile(this.hostsPath, content, 'utf-8');
    info('Hosts file updated', { path: this.hostsPath });
  }

  /**
   * Apply one mutation to the managed block as a single read-modify-write.
   *
   * Every public mutator routes through here so that touching N hostnames
   * produces exactly one backup and one write, and never leaves an intermediate
   * state that a crash midway could preserve.
   *
   * @param {(entries: Map<string, {ip: string, hostnames: string[], tag: string}>) => void} mutate
   * @param {string} verb - Past-tense verb used in the log line
   * @returns {Promise<DiffResult & {changed: boolean}>}
   */
  async _mutate(mutate, verb) {
    const content = await this.read();
    const entries = this._parseManaged(content);

    mutate(entries);

    const next = this._buildHostsContent(content, entries);
    if (next === content) {
      debug('Hosts file already up to date', { path: this.hostsPath });
      return { added: 0, removed: 0, updated: 0, changed: false };
    }

    const diff = this._diff(
      this._managedFrom(content),
      new Map([...entries].map(([h, e]) => [h, e.ip]))
    );
    await this.write(next, content);
    info(`Hosts entries ${verb}`, diff);
    return { ...diff, changed: true };
  }

  /** @returns {Promise<Map<string, {ip: string, hostnames: string[], tag: string}>>} */
  async getManagedEntries() {
    return this._parseManaged(await this.read());
  }

  /**
   * Replace the entire managed block. Destructive: anything currently managed
   * and absent from `newEntries` is dropped. Use only when the caller holds the
   * complete intended state; otherwise prefer {@link addEntries}.
   */
  async updateEntries(newEntries) {
    this._assertSafeEntries(newEntries);
    return this._mutate(entries => {
      entries.clear();
      for (const [hostname, value] of newEntries) entries.set(hostname, value);
    }, 'updated');
  }

  /**
   * Merge `newEntries` into the block, leaving every other managed entry alone.
   * This is what `tsdb add` must use.
   */
  async addEntries(newEntries) {
    this._assertSafeEntries(newEntries);
    return this._mutate(entries => {
      for (const [hostname, value] of newEntries) entries.set(hostname, value);
    }, 'added');
  }

  /** Remove exactly the named hostnames; everything else survives. */
  async removeEntries(hostnames) {
    return this._mutate(entries => {
      for (const hostname of hostnames) entries.delete(hostname);
    }, 'removed');
  }

  /**
   * Reconcile the config-owned entries in one pass: drop the ones the caller no
   * longer supplies, then set the supplied ones. Hostnames tagged `manual` are
   * never removed, so `run` cannot discard a deliberate `tsdb add`.
   *
   * @returns {Promise<DiffResult & {changed: boolean}>}
   */
  async applyConfigEntries(newEntries) {
    this._assertSafeEntries(newEntries);
    return this._mutate(entries => {
      for (const [hostname, value] of [...entries]) {
        if (value.tag === 'config' && !newEntries.has(hostname)) entries.delete(hostname);
      }
      for (const [hostname, value] of newEntries) entries.set(hostname, value);
    }, 'refreshed');
  }

  /** @returns {Promise<number>} Number of hostnames removed */
  async clearManagedEntries() {
    const content = await this.read();
    if (!this._hasBlock(content)) return 0;

    const count = this._parseManaged(content).size;
    if (count === 0) return 0;

    const start = content.indexOf(TSDB_MARKER_START);
    const end = content.indexOf(TSDB_MARKER_END);
    const merged = (content.slice(0, start) + content.slice(end + TSDB_MARKER_END.length))
      .replace(/\n{3,}/g, '\n\n')
      .trimEnd() + '\n';

    await this.write(merged, content);
    info('Cleared all managed entries', { count });
    return count;
  }

  /** @returns {Promise<string[]>} Backup basenames, newest first */
  async listBackups() {
    try {
      const files = await readdir(this.backupDir);
      return files.filter(f => f.startsWith('hosts.') && f.endsWith('.bak')).sort().reverse();
    } catch {
      return [];
    }
  }

  async restoreBackup(backupName) {
    const base = String(backupName || '');
    if (!/^hosts\.[A-Za-z0-9.-]+\.bak$/.test(base)) throw new Error('Invalid backup name');
    const content = await readFile(join(this.backupDir, base), 'utf-8');
    await writeFile(this.hostsPath, content, 'utf-8');
    info('Restored hosts from backup', { backup: base });
  }

  // ---- internals -------------------------------------------------------

  _hasBlock(content) {
    const start = content.indexOf(TSDB_MARKER_START);
    const end = content.indexOf(TSDB_MARKER_END);
    return start !== -1 && end !== -1 && end > start;
  }

  /**
   * Split a managed line into ip, hostnames and tag. Untagged lines (written by
   * an older version of this tool) report as 'config' so a later run treats them
   * as config-owned rather than orphaning them.
   */
  _parseLine(line) {
    const hashIndex = line.indexOf('#');
    const withoutComment = (hashIndex === -1 ? line : line.slice(0, hashIndex)).trim();
    if (!withoutComment) return null;

    const parts = withoutComment.split(/\s+/);
    if (parts.length < 2) return null;

    const comment = hashIndex === -1 ? '' : line.slice(hashIndex + 1).trim();
    const tagged = comment.startsWith('tsdb:') ? comment.slice('tsdb:'.length).trim() : '';
    const tag = TAGS.has(tagged) ? tagged : 'config';

    return { ip: parts[0], hostnames: parts.slice(1), tag };
  }

  _managedLines(content) {
    if (!this._hasBlock(content)) return [];
    const start = content.indexOf(TSDB_MARKER_START);
    const end = content.indexOf(TSDB_MARKER_END);

    return content
      .slice(start + TSDB_MARKER_START.length, end)
      .split('\n')
      .map(l => l.trim())
      .filter(Boolean)
      .map(l => this._parseLine(l))
      .filter(Boolean);
  }

  /** Each hostname maps to its line's full hostname list, for display. */
  _parseManaged(content) {
    const entries = new Map();
    for (const line of this._managedLines(content)) {
      for (const hostname of line.hostnames) {
        entries.set(hostname, { ip: line.ip, hostnames: line.hostnames, tag: line.tag });
      }
    }
    return entries;
  }

  /** Flat `hostname -> ip` view, which is what diffing needs. */
  _managedFrom(content) {
    const flat = new Map();
    for (const line of this._managedLines(content)) {
      for (const hostname of line.hostnames) flat.set(hostname, line.ip);
    }
    return flat;
  }

  _diff(priorFlat, nextIpByHostname) {
    let added = 0;
    let removed = 0;
    let updated = 0;
    for (const hostname of priorFlat.keys()) {
      if (!nextIpByHostname.has(hostname)) removed++;
    }
    for (const [hostname, ip] of nextIpByHostname) {
      const before = priorFlat.get(hostname);
      if (before === undefined) added++;
      else if (before !== ip) updated++;
    }
    return { added, removed, updated };
  }

  /**
   * Refuse to write anything that would corrupt the hosts file: a newline or `#`
   * inside a hostname silently ends the record, and a non-IPv4 literal is not
   * supported by the hosts-file format this tool targets.
   */
  _assertSafeEntries(entries) {
    for (const [hostname, value] of entries) {
      if (!SAFE_HOSTNAME.test(hostname)) {
        throw new Error(`Unsafe hostname rejected: ${JSON.stringify(hostname)}`);
      }
      if (!value || !SAFE_IPV4.test(value.ip)) {
        throw new Error(`Unsafe or non-IPv4 address rejected for ${hostname}: ${JSON.stringify(value?.ip)}`);
      }
      if (!TAGS.has(value.tag)) {
        throw new Error(`Invalid tag for ${hostname}: ${JSON.stringify(value?.tag)}`);
      }
      if (!Array.isArray(value.hostnames) || value.hostnames.length === 0) {
        throw new Error(`Entry for ${hostname} has no hostnames`);
      }
      for (const h of value.hostnames) {
        if (!SAFE_HOSTNAME.test(h)) {
          throw new Error(`Unsafe hostname rejected: ${JSON.stringify(h)}`);
        }
      }
    }
  }

  _buildHostsContent(originalContent, entries) {
    let base;
    if (this._hasBlock(originalContent)) {
      const start = originalContent.indexOf(TSDB_MARKER_START);
      const end = originalContent.indexOf(TSDB_MARKER_END);
      base = originalContent.slice(0, start) + originalContent.slice(end + TSDB_MARKER_END.length);
    } else {
      base = originalContent;
    }
    base = base.replace(/\n{3,}/g, '\n\n').trimEnd();
    // An empty hosts file must not gain a leading blank line before the block.
    base = base ? `${base}\n` : '';

    if (entries.size === 0) return base;

    // The map KEYS are the authoritative hostname set. `value.hostnames` cannot
    // be used here: `_parseManaged` attaches a line's full list to each member,
    // so rebuilding from it would resurrect anything `removeEntries` just
    // deleted. Group by tag+ip so ownership stays legible in the file.
    const byGroup = new Map();
    for (const [hostname, value] of entries) {
      const key = `${value.tag} ${value.ip}`;
      if (!byGroup.has(key)) byGroup.set(key, { tag: value.tag, ip: value.ip, names: new Set() });
      byGroup.get(key).names.add(hostname);
    }

    const lines = [TSDB_MARKER_START];
    const groups = [...byGroup.values()]
      .sort((a, b) => a.tag.localeCompare(b.tag) || a.ip.localeCompare(b.ip));
    for (const group of groups) {
      lines.push(`${group.ip}\t${[...group.names].sort().join(' ')}\t${TAG_PREFIX}${group.tag}`);
    }
    lines.push(TSDB_MARKER_END);

    return `${base}\n${lines.join('\n')}\n`;
  }

  async _createBackup() {
    try {
      await mkdir(this.backupDir, { recursive: true });
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupPath = join(this.backupDir, `hosts.${timestamp}.bak`);
      await writeFile(backupPath, await this.read(), 'utf-8');
      debug('Created hosts backup', { path: backupPath });
      await this._pruneBackups();
    } catch (err) {
      warn('Failed to create hosts backup', { error: err.message });
    }
  }

  /** Bound disk growth: keep only the newest `maxBackups`. */
  async _pruneBackups() {
    const stale = (await this.listBackups()).slice(this.maxBackups);
    for (const name of stale) {
      try {
        await unlink(join(this.backupDir, name));
        debug('Pruned old hosts backup', { name });
      } catch (err) {
        warn('Failed to prune backup', { name, error: err.message });
      }
    }
  }
}