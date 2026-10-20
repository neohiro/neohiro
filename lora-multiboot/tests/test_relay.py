#!/usr/bin/env python3
"""Relay / cross-protocol decode invariants."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRM = os.path.join(ROOT, 'firmware')

def _read(*p):
    return open(os.path.join(FIRM, *p), 'r', encoding='utf-8').read()

def test_relay_no_todo():
    for name in ('src/relay.cpp', 'include/relay.h', 'src/main.cpp', 'src/SX1262Router.cpp'):
        txt = _read(*name.split('/'))
        assert 'TODO' not in txt, f"{name}: has TODO"
        assert 'FIXME' not in txt, f"{name}: has FIXME"

def test_relay_wire():
    main = _read('src', 'main.cpp')
    assert 'relay_init()' in main
    assert 'relay_tick(&s_ctx)' in main
    assert 'shared_context_t s_ctx' in main

def test_relay_classify_path():
    relay = _read('src', 'relay.cpp')
    assert 'shared_context_classify' in relay
    assert 'slot_for_pid' in relay
    assert 'arbiter_request' in relay
    assert 'pid == 0x00' in relay

def test_relay_gateway():
    src = _read('src', 'SX1262Router.cpp')
    assert 's_v=true' in src
    assert 'return s_p && s_a;' in src

if __name__ == '__main__':
    test_relay_no_todo()
    test_relay_wire()
    test_relay_classify_path()
    test_relay_gateway()
    print("PASS: relay wire, classify, gateway, dead-code")
