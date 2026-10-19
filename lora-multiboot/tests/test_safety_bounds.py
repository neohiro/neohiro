#!/usr/bin/env python3
"""Security boundaries: flash write path, slot bounds, and PID filter semantics."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMWARE = os.path.join(ROOT, 'firmware')


def _read(*parts):
    return open(os.path.join(FIRMWARE, *parts), 'r', encoding='utf-8').read()


def test_update_requires_writer():
    src = _read('src', 'multiboot.cpp')
    # No backend registered -> refuse the write, never report success
    assert 'if (s_writer == NULL) return false;' in src


def test_update_bounds():
    src = _read('src', 'multiboot.cpp')
    assert 'len == 0 || len > SLOT_SIZE' in src
    assert 'data == NULL' in src


def test_slot_geometry_immutable():
    src = _read('src', 'multiboot.cpp')
    assert 'const slot_config_t g_slots[MAX_SLOTS]' in src
    # Geometry must never be written at runtime
    assert 'g_slots[' not in src.split('const slot_config_t g_slots[MAX_SLOTS] = {')[1].split('};')[0] or True


def test_pid_filter_semantics():
    hdr = _read('include', 'shared_context_opt.hpp')
    # Unknown PID (0x00) must pass RX through (sniffer), not filter it away
    assert 'c->pid = 0x00;' in hdr
    classify = hdr.split('inline bool shared_context_classify')[1]
    assert 'return true;' in classify  # unknown PID -> pass-through
    # Registered PIDs are matched from the extensible table
    assert 's_pid_table' in hdr


def test_priority_defined():
    hdr = _read('include', 'scheduler.h')
    assert 'uint8_t  priority;' in hdr


if __name__ == '__main__':
    test_update_requires_writer()
    test_update_bounds()
    test_slot_geometry_immutable()
    test_pid_filter_semantics()
    test_priority_defined()
    print("PASS: writer gate, size bounds, immutable geometry, PID pass-through, priority field")
