/**
 * Tests for the Tailscale client
 * @module test/tailscale.test
 */

import { describe, it } from 'node:test';
import { strictEqual, ok } from 'node:assert';
import { TailscaleClient, generateSplitTunnelRoutes, isValidIPv4Cidr } from '../src/tailscale.mjs';

describe('tailscale', () => {
  describe('generateSplitTunnelRoutes', () => {
    it('covers the private ranges', () => {
      const routes = generateSplitTunnelRoutes();
      for (const expected of ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '127.0.0.0/8']) {
        ok(routes.includes(expected), `missing ${expected}`);
      }
    });

    it('returns valid CIDR notation', () => {
      for (const route of generateSplitTunnelRoutes()) {
        ok(isValidIPv4Cidr(route), `${route} should be valid CIDR`);
      }
    });
  });

  describe('isValidIPv4Cidr', () => {
    it('accepts valid IPv4 CIDR', () => {
      for (const good of ['10.0.0.0/8', '0.0.0.0/0', '192.168.1.1/32', '172.16.0.0/12']) {
        ok(isValidIPv4Cidr(good), `${good} should be valid`);
      }
    });

    it('rejects malformed CIDR', () => {
      for (const bad of ['10.0.0.0', '10.0.0.0/33', '10.0.0.256/8', '10.0.0/8', 'not/a/route', '']) {
        ok(!isValidIPv4Cidr(bad), `${bad} should be invalid`);
      }
    });
  });

  describe('advertiseRoutes', () => {
    it('refuses to advertise an invalid route', async () => {
      strictEqual(await new TailscaleClient({ enabled: true }).advertiseRoutes(['10.0.0.0/99']), false);
    });

    it('is a no-op for an empty route list', async () => {
      strictEqual(await new TailscaleClient({ enabled: true }).advertiseRoutes([]), true);
    });

    it('does nothing when disabled', async () => {
      const client = new TailscaleClient({ enabled: false });
      strictEqual(await client.advertiseRoutes(['10.0.0.0/8']), false);
      strictEqual(await client.acceptRoutes(), false);
    });
  });

  describe('_run', () => {
    it('resolves rather than throwing when the binary is missing', async () => {
      const client = new TailscaleClient({ enabled: true });
      client.cliPath = 'definitely-not-a-real-binary-xyz';
      const result = await client._run(['version']);
      ok(result.code !== 0);
      ok(typeof result.stderr === 'string');
    });

    it('captures stdout from a working command', async () => {
      const client = new TailscaleClient({ enabled: true });
      client.cliPath = process.execPath;
      const result = await client._run(['-e', 'process.stdout.write("hi")']);
      strictEqual(result.code, 0);
      strictEqual(result.stdout, 'hi');
    });
  });

  describe('getExitNodeStatus', () => {
    it('degrades safely when tailscale is absent', async () => {
      const client = new TailscaleClient({ enabled: true });
      client.cliPath = 'definitely-not-a-real-binary-xyz';
      strictEqual((await client.getExitNodeStatus()).usingExitNode, false);
    });

    it('reports no exit node when there are no peers', async () => {
      const client = new TailscaleClient({ enabled: true });
      client._run = async () => ({ code: 0, stdout: '{"Self":{"ID":"self"}}', stderr: '' });
      strictEqual((await client.getExitNodeStatus()).usingExitNode, false);
    });

    it('detects an exit-node peer', async () => {
      const client = new TailscaleClient({ enabled: true });
      client._run = async () => ({
        code: 0,
        stdout: JSON.stringify({
          Self: { ID: 'self' },
          peer1: { ID: 'p1', ExitNode: true, TailscaleIPs: ['100.125.87.39'] }
        }),
        stderr: ''
      });
      const status = await client.getExitNodeStatus();
      strictEqual(status.usingExitNode, true);
      strictEqual(status.exitNodeIp, '100.125.87.39');
    });

    it('does not throw on malformed JSON', async () => {
      const client = new TailscaleClient({ enabled: true });
      client._run = async () => ({ code: 0, stdout: 'not json', stderr: '' });
      strictEqual((await client.getExitNodeStatus()).usingExitNode, false);
    });
  });
});