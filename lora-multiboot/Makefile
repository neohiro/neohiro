# Makefile - lora-multiboot host gate
.PHONY: test check firmware clean
check:
	echo "[gate] verifying layout"
	test -f firmware/src/main.cpp
	test -f firmware/include/multiboot.h
	test -f firmware/partitions/quadboot.csv
	echo "[gate] layout OK"
test: check
	python tests/test_slots.py
	python tests/test_concurrent.py
	python tests/test_safety_bounds.py
	python tests/test_relay.py
	echo "[gate] all tests passed"
firmware:
	cd firmware && pio run -e heltec_v4_bridge
clean:
	find . -name '*.pyc' -delete
