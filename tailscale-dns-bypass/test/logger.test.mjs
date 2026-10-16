/**
 * Tests for the logger
 * @module test/logger.test
 */

import { describe, it, beforeEach, after } from 'node:test';
import { strictEqual, ok } from 'node:assert';
import { configureLogger, debug, info, warn, error, createChildLogger } from '../src/logger.mjs';

describe('logger', () => {
  const original = {};
  let captured;

  beforeEach(() => {
    captured = {};
    for (const level of ['debug', 'info', 'warn', 'error']) {
      original[level] = console[level];
      captured[level] = [];
      console[level] = (...args) => captured[level].push(args.join(' '));
    }
  });

  after(() => {
    for (const level of ['debug', 'info', 'warn', 'error']) console[level] = original[level];
  });

  it('filters below the configured level', () => {
    configureLogger({ level: 'warn', format: 'text' });
    debug('nope');
    info('nope');
    warn('yes');
    error('yes');

    strictEqual(captured.debug.length, 0);
    strictEqual(captured.info.length, 0);
    strictEqual(captured.warn.length, 1);
    strictEqual(captured.error.length, 1);
  });

  it('defaults to info', () => {
    configureLogger({ level: 'info', format: 'text' });
    debug('nope');
    info('yes');
    strictEqual(captured.debug.length, 0);
    strictEqual(captured.info.length, 1);
  });

  it('ignores an unknown level rather than disabling logging', () => {
    configureLogger({ level: 'info', format: 'text' });
    configureLogger({ level: 'bogus' });
    info('still logged');
    strictEqual(captured.info.length, 1);
  });

  it('includes metadata in text output', () => {
    configureLogger({ level: 'info', format: 'text' });
    info('message', { domain: 'example.com' });
    ok(captured.info[0].includes('message'));
    ok(captured.info[0].includes('example.com'));
  });

  it('emits parseable JSON when asked', () => {
    configureLogger({ level: 'info', format: 'json' });
    info('json message', { key: 'value' });

    const parsed = JSON.parse(captured.info[0]);
    strictEqual(parsed.level, 'info');
    strictEqual(parsed.message, 'json message');
    strictEqual(parsed.key, 'value');
    ok(parsed.timestamp);
  });

  it('omits meta entirely when there is none', () => {
    configureLogger({ level: 'info', format: 'json' });
    info('bare');
    ok(!('meta' in JSON.parse(captured.info[0])));
  });

  it('survives circular metadata and still emits valid JSON', () => {
    configureLogger({ level: 'info', format: 'json' });
    const meta = { name: 'loop' };
    meta.self = meta;

    info('circular', meta);
    const parsed = JSON.parse(captured.info[0]);
    strictEqual(parsed.message, 'circular');
    ok(captured.info[0].includes('unserializable'));
  });

  it('does not colour output in JSON mode', () => {
    configureLogger({ level: 'info', format: 'json' });
    info('plain');
    ok(!captured.info[0].includes('\x1b['));
  });

  it('merges a child logger default', () => {
    configureLogger({ level: 'info', format: 'json' });
    createChildLogger({ component: 'dns' }).info('child', { extra: 1 });

    const parsed = JSON.parse(captured.info[0]);
    strictEqual(parsed.component, 'dns');
    strictEqual(parsed.extra, 1);
  });

  it('lets the child override its default', () => {
    configureLogger({ level: 'info', format: 'json' });
    createChildLogger({ component: 'dns' }).info('override', { component: 'probe' });
    strictEqual(JSON.parse(captured.info[0]).component, 'probe');
  });
});