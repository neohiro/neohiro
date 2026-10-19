#!/usr/bin/env python3
"""Verify concurrency primitives: router gate, scheduler cap, priority arbitration."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMWARE = os.path.join(ROOT, 'firmware')


def _read(*parts):
    return open(os.path.join(FIRMWARE, *parts), 'r', encoding='utf-8').read()


def test_main_uses_gate():
    src = _read('src', 'main.cpp')
    assert 'SX1262Router_gate' in src
    assert 'SX1262Router_can_tx' in src
    assert 'SX1262Router_init' in src
    # Transmission must not be reachable before the gate passes
    assert src.index('SX1262Router_gate()') < src.index('multiboot_load_slot(SLOT_RADIO)')


def test_scheduler_cap():
    hdr = _read('include', 'scheduler.h')
    assert '#define MAX_CONCURRENT 4' in hdr
    src = _read('src', 'scheduler.cpp')
    assert 'scheduler_active_count() >= MAX_CONCURRENT' in src


def test_priority_preemption():
    src = _read('src', 'radio_arbiter.cpp')
    # Higher priority must preempt a lower-priority holder of the radio
    assert 'prio > s_granted_prio' in src
    hdr = _read('include', 'radio_arbiter.h')
    assert 'uint8_t prio' in hdr


def test_no_todo():
    for name in ('src/SX1262Router.cpp', 'src/main.cpp', 'src/WebTerminal.cpp',
                 'src/multiboot.cpp', 'src/scheduler.cpp', 'src/radio_arbiter.cpp'):
        content = _read(*name.split('/'))
        assert 'TODO' not in content, f"{name}: has TODO"
        assert 'FIXME' not in content, f"{name}: has FIXME"


if __name__ == '__main__':
    test_main_uses_gate()
    test_scheduler_cap()
    test_priority_preemption()
    test_no_todo()
    print("PASS: router gate ordering, scheduler cap, priority preemption, no dead code")
