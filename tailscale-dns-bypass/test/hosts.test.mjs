/**
 * Tests for the hosts file manager
 * @module test/hosts.test
 */

import { describe, it, before, beforeEach, after } from 'node:test';
import { strictEqual, ok, deepStrictEqual, rejects } from 'node:assert';
import { writeFile, mkdir, rm, readFile, readdir } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { HostsManager } from '../src/hosts.mjs';

const START = '# === tailscale-dns-bypass managed entries start ===';
const END = '# === tailscale-dns-bypass managed entries end ===';

const entry = (ip, ...hostnames) => ({ ip, hostnames, tag: 'config' });
const asMap = (...entries) =>
  new Map(entries.flatMap(e => e.hostnames.map(h => [h, { ip: e.ip, hostnames: e.hostnames, tag: e.tag }])));
const keysOf = async m => [...(await m).keys()];

describe('hosts', () => {
  let testDir;
  let hostsPath;
  let backupDir;
  let manager;

  before(async () => {
    testDir = join(tmpdir(), `tsdb-hosts-${Date.now()}`);
    await mkdir(join(testDir, 'backups'), { recursive: true });
    hostsPath = join(testDir, 'hosts');
    backupDir = join(testDir, 'backups');

    manager = new HostsManager({
      hosts: { path: hostsPath, backupDir, createBackup: false, maxBackups: 10 }
    });
  });

  after(async () => {
    await rm(testDir, { recursive: true, force: true }).catch(() => {});
  });

  beforeEach(async () => {
    await writeFile(
      hostsPath,
      '# Managed by the OS\n127.0.0.1 localhost\n::1 ip6-localhost\n192.168.1.10 nas.local\n',
      'utf-8'
    );
  });

  describe('read', () => {
    it('returns the current file contents', async () => {
      ok((await manager.read()).includes('127.0.0.1 localhost'));
    });
  });

  describe('getManagedEntries', () => {
    it('is empty when there is no managed block', async () => {
      strictEqual((await manager.getManagedEntries()).size, 0);
    });

    it('groups every hostname that shares a line', async () => {
      await writeFile(hostsPath, `${START}\n1.2.3.4 a.com b.com\n5.6.7.8 c.com\n${END}\n`, 'utf-8');
      const entries = await manager.getManagedEntries();

      strictEqual(entries.size, 3);
      strictEqual(entries.get('a.com').ip, '1.2.3.4');
      deepStrictEqual(entries.get('b.com').hostnames, ['a.com', 'b.com']);
      strictEqual(entries.get('c.com').ip, '5.6.7.8');
    });

    it('ignores comments and malformed lines inside the block', async () => {
      await writeFile(hostsPath, `${START}\n# note\n\n1.2.3.4 a.com\ngarbage\n${END}\n`, 'utf-8');
      deepStrictEqual(await keysOf(manager.getManagedEntries()), ['a.com']);
    });
  });

  describe('updateEntries', () => {
    it('adds entries and reports the diff', async () => {
      const result = await manager.updateEntries(asMap(entry('1.2.3.4', 'a.com', 'b.com')));
      deepStrictEqual(result, { added: 2, removed: 0, updated: 0, changed: true });
      ok((await readFile(hostsPath, 'utf-8')).includes('1.2.3.4\ta.com b.com'));
    });

    it('detects an IP change as an update', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      deepStrictEqual(await manager.updateEntries(asMap(entry('2.2.2.2', 'a.com'))),
        { added: 0, removed: 0, updated: 1, changed: true });
    });

    it('drops managed entries absent from the new map', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com'), entry('2.2.2.2', 'b.com')));
      strictEqual((await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')))).removed, 1);
      deepStrictEqual(await keysOf(manager.getManagedEntries()), ['a.com']);
    });

    it('preserves unmanaged content', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      const content = await readFile(hostsPath, 'utf-8');
      ok(content.includes('# Managed by the OS'));
      ok(content.includes('192.168.1.10 nas.local'));
    });

    it('is idempotent', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com'), entry('2.2.2.2', 'b.com')));
      const first = await readFile(hostsPath, 'utf-8');
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com'), entry('2.2.2.2', 'b.com')));
      strictEqual(await readFile(hostsPath, 'utf-8'), first);
    });
  });

  describe('addEntries', () => {
    it('merges without removing unrelated entries', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com'), entry('2.2.2.2', 'b.com')));
      deepStrictEqual(await manager.addEntries(asMap(entry('3.3.3.3', 'c.com'))),
        { added: 1, removed: 0, updated: 0, changed: true });
      deepStrictEqual((await keysOf(manager.getManagedEntries())).sort(), ['a.com', 'b.com', 'c.com']);
    });

    it('replaces a colliding hostname as an update', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com'), entry('2.2.2.2', 'b.com')));
      deepStrictEqual(await manager.addEntries(asMap(entry('9.9.9.9', 'a.com'))),
        { added: 0, removed: 0, updated: 1, changed: true });
      const entries = await manager.getManagedEntries();
      strictEqual(entries.get('a.com').ip, '9.9.9.9');
      strictEqual(entries.get('b.com').ip, '2.2.2.2');
    });
  });

  describe('no-op writes', () => {
    it('reports changed:false and skips the write', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      const again = await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      deepStrictEqual(again, { added: 0, removed: 0, updated: 0, changed: false });
    });

    it('does not create a backup when nothing changed', async () => {
      const backed = new HostsManager({
        hosts: { path: hostsPath, backupDir, createBackup: true, maxBackups: 10 }
      });
      await backed.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      const afterFirst = (await readdir(backupDir)).filter(f => f.endsWith('.bak')).length;

      await backed.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      const afterSecond = (await readdir(backupDir)).filter(f => f.endsWith('.bak')).length;

      strictEqual(afterSecond, afterFirst, 'a no-op must not churn backups');
    });
  });

  describe('concurrent modification', () => {
    it('refuses to write when the file changed underneath', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));

      // Simulate another tool editing the file after we read it but before write.
      const originalRead = manager.read.bind(manager);
      let reads = 0;
      manager.read = async () => {
        reads++;
        if (reads === 2) return `${await originalRead()}# someone else\n`;
        return originalRead();
      };

      await rejects(
        () => manager.updateEntries(asMap(entry('2.2.2.2', 'a.com'))),
        /changed on disk/
      );
      ok(!(await readFile(hostsPath, 'utf-8')).includes('# someone else'),
        'the concurrent edit must survive');
    });
  });

  describe('applyConfigEntries', () => {
    it('prunes config entries that are no longer supplied', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'old.com'), entry('2.2.2.2', 'new.com')));
      await manager.applyConfigEntries(asMap(entry('2.2.2.2', 'new.com')));
      deepStrictEqual(await keysOf(manager.getManagedEntries()), ['new.com']);
    });

    it('never prunes manual entries', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'cfg.com')));
      await manager.addEntries(asMap({ ip: '3.3.3.3', hostnames: ['man.com'], tag: 'manual' }));
      await manager.applyConfigEntries(asMap(entry('1.1.1.1', 'cfg.com')));

      const keys = await keysOf(manager.getManagedEntries());
      ok(keys.includes('cfg.com'));
      ok(keys.includes('man.com'), 'a manual entry must survive a config reconcile');
    });

    it('writes once for a rename, leaving no intermediate state', async () => {
      let writes = 0;
      const originalWrite = manager.write.bind(manager);
      manager.write = async (...args) => {
        writes++;
        return originalWrite(...args);
      };

      await manager.updateEntries(asMap(entry('1.1.1.1', 'before.com')));
      writes = 0;
      await manager.applyConfigEntries(asMap(entry('1.1.1.1', 'after.com')));
      strictEqual(writes, 1, 'reconcile must be a single write');
    });
  });

  describe('removeEntries', () => {
    it('removes only the named hostnames', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com'), entry('2.2.2.2', 'b.com')));
      deepStrictEqual(await manager.removeEntries(['a.com']), { added: 0, removed: 1, updated: 0, changed: true });
      deepStrictEqual(await keysOf(manager.getManagedEntries()), ['b.com']);
    });

    it('reports zero when nothing matched', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      strictEqual((await manager.removeEntries(['nope.com'])).removed, 0);
      strictEqual((await manager.getManagedEntries()).size, 1);
    });

    it('really deletes the hostname even when a sibling shares its IP', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'shop.com'), entry('1.1.1.1', 'notshop.com')));
      await manager.removeEntries(['shop.com']);
      deepStrictEqual(await keysOf(manager.getManagedEntries()), ['notshop.com']);

      // Compare on whitespace-delimited tokens: 'notshop.com' contains the
      // substring 'shop.com', so a plain includes() would be misleading.
      const tokens = (await readFile(hostsPath, 'utf-8')).split('# tsdb:')[0]
        .trim().split(/\s+/).slice(1);
      ok(!tokens.includes('shop.com'), `shop.com still present in ${tokens.join(',')}`);
    });
  });

  describe('clearManagedEntries', () => {
    it('returns the number of hostnames removed', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com', 'b.com')));
      strictEqual(await manager.clearManagedEntries(), 2);
      strictEqual((await manager.getManagedEntries()).size, 0);
    });

    it('returns 0 when nothing is managed', async () => {
      strictEqual(await manager.clearManagedEntries(), 0);
    });

    it('keeps unmanaged content', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      await manager.clearManagedEntries();
      const content = await readFile(hostsPath, 'utf-8');
      ok(content.includes('192.168.1.10 nas.local'));
      ok(!content.includes(START));
    });
  });

  describe('ownership tagging', () => {
    it('writes a trailing tag comment', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      ok((await readFile(hostsPath, 'utf-8')).includes('# tsdb:config'));
    });

    it('round-trips the tag', async () => {
      await manager.updateEntries(asMap({ ip: '1.1.1.1', hostnames: ['m.com'], tag: 'manual' }));
      strictEqual((await manager.getManagedEntries()).get('m.com').tag, 'manual');
    });

    it('treats an untagged legacy line as config-owned', async () => {
      await writeFile(hostsPath, `${START}\n1.2.3.4 legacy.com\n${END}\n`, 'utf-8');
      strictEqual((await manager.getManagedEntries()).get('legacy.com').tag, 'config');
    });

    it('keeps config and manual entries on separate lines', async () => {
      await manager.updateEntries(asMap(entry('1.1.1.1', 'cfg.com')));
      await manager.addEntries(asMap({ ip: '1.1.1.1', hostnames: ['man.com'], tag: 'manual' }));
      const content = await readFile(hostsPath, 'utf-8');
      ok(content.includes('1.1.1.1\tcfg.com\t# tsdb:config'));
      ok(content.includes('1.1.1.1\tman.com\t# tsdb:manual'));
    });

    it('rejects an unknown tag', async () => {
      await rejects(
        () => manager.addEntries(asMap({ ip: '1.1.1.1', hostnames: ['x.com'], tag: 'bogus' })),
        /Invalid tag/
      );
    });

    it('ignores a non-tag comment on a managed line', async () => {
      await writeFile(hostsPath, `${START}\n1.2.3.4 a.com  # some other tool\n${END}\n`, 'utf-8');
      strictEqual((await manager.getManagedEntries()).get('a.com').tag, 'config');
    });
  });

  describe('input safety', () => {
    it('rejects a hostname containing whitespace', async () => {
      await rejects(() => manager.updateEntries(asMap(entry('1.1.1.1', 'bad name.com'))), /Unsafe hostname/);
    });

    it('rejects a hostname that would terminate the record early', async () => {
      await rejects(
        () => manager.updateEntries(asMap(entry('1.1.1.1', 'evil.com\n127.0.0.1 other.com'))),
        /Unsafe hostname/
      );
    });

    it('rejects a non-IPv4 address', async () => {
      await rejects(() => manager.updateEntries(asMap(entry('::1', 'a.com'))), /non-IPv4/);
    });

    it('leaves the file untouched when validation fails', async () => {
      const before = await readFile(hostsPath, 'utf-8');
      await rejects(() => manager.updateEntries(asMap(entry('1.1.1.1', 'bad name')))).catch(() => {});
      strictEqual(await readFile(hostsPath, 'utf-8'), before);
    });
  });

  describe('backups', () => {
    it('creates a backup before writing when enabled', async () => {
      const backed = new HostsManager({
        hosts: { path: hostsPath, backupDir, createBackup: true, maxBackups: 10 }
      });
      await backed.updateEntries(asMap(entry('1.1.1.1', 'a.com')));
      ok((await readdir(backupDir)).some(f => /^hosts\..*\.bak$/.test(f)));
    });

    it('prunes backups beyond maxBackups', async () => {
      const pruned = new HostsManager({
        hosts: { path: hostsPath, backupDir, createBackup: true, maxBackups: 2 }
      });
      for (let i = 0; i < 5; i++) {
        await writeFile(hostsPath, `127.0.0.1 localhost${i}\n`, 'utf-8');
        await pruned.updateEntries(asMap(entry('1.1.1.1', `a${i}.com`)));
      }
      const files = (await readdir(backupDir)).filter(f => f.endsWith('.bak'));
      ok(files.length <= 2, `expected <= 2 backups, found ${files.length}`);
    });

    it('rejects a traversal attempt in restoreBackup', async () => {
      await rejects(() => manager.restoreBackup('../../etc/passwd'), /Invalid backup name/);
    });
  });
});