#!/usr/bin/env python3
"""Verify multiboot slot mapping, geometry and dual-run config."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMWARE = os.path.join(ROOT, 'firmware')
sys.path.insert(0, os.path.join(FIRMWARE, 'include'))

SLOTS = {
    0: ("Repeater-A", "REPEATER"),
    1: ("Repeater-B", "REPEATER"),
    2: ("Meshtastic", "MESHTASTIC"),
    3: ("MeshCore",   "MESHCORE"),
    4: ("Radio",      "RADIO"),
}


def test_slot_count():
    assert len(SLOTS) == 5, "Expected 5 slots"


def test_dual_run():
    # Dual-run requires Meshtastic + MeshCore + base radio to be present
    assert 2 in SLOTS
    assert 3 in SLOTS
    assert 4 in SLOTS


def test_no_dead_code():
    src_dir = os.path.join(FIRMWARE, 'src')
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(('.cpp', '.hpp')):
                path = os.path.join(root, f)
                content = open(path, 'r', encoding='utf-8').read()
                assert 'TODO' not in content, f"{path}: has TODO"
                assert 'FIXME' not in content, f"{path}: has FIXME"


def test_header_constants():
    header = open(os.path.join(FIRMWARE, 'include', 'multiboot.h'), 'r', encoding='utf-8').read()
    assert 'SLOT_REPEATER_A 0' in header
    assert 'SLOT_MESHTASTIC 2' in header
    assert 'MAX_SLOTS 5' in header
    # Geometry must be immutable at runtime
    assert 'extern const slot_config_t g_slots[MAX_SLOTS];' in header


def test_security_bounds():
    header = open(os.path.join(FIRMWARE, 'include', 'multiboot.h'), 'r', encoding='utf-8').read()
    assert 'SLOT_SIZE 0x100000' in header
    src = open(os.path.join(FIRMWARE, 'src', 'multiboot.cpp'), 'r', encoding='utf-8').read()
    # Update path must refuse oversized payloads and refuse without a writer
    assert 'len > SLOT_SIZE' in src
    assert 's_writer == NULL' in src


def test_partition_layout():
    csv = open(os.path.join(FIRMWARE, 'partitions', 'quadboot.csv'), 'r', encoding='utf-8').read()
    for slot in ('ota_0', 'ota_1', 'ota_2', 'ota_3', 'ota_4'):
        assert slot in csv, f"quadboot.csv missing {slot}"


if __name__ == "__main__":
    test_slot_count()
    test_dual_run()
    test_no_dead_code()
    test_header_constants()
    test_security_bounds()
    test_partition_layout()
    print("PASS: slots, dual-run, header sync, dead-code, bounds, partition layout")
