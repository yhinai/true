PYTHON=.venv/bin/python

.PHONY: install test demo-smoke demo demo-falsified demo-unproven demo-non-contradiction demo-identity verify-crosshair verify-acp

install:
	$(PYTHON) -m pip install -e .

test:
	PYTHONPATH=src $(PYTHON) -m pytest

demo-smoke:
	@set -e; \
	output=$$(PYTHONPATH=src $(PYTHON) -m pytest demo_repo/tests/test_discount.py -q 2>&1 || true); \
	printf "%s\n" "$$output"; \
	echo "$$output" | grep -q "failed" || (echo "Expected the demo bug test to fail before patching." >&2; exit 1)
	PYTHONPATH=src $(PYTHON) -m axiom.cli --bug demo_repo/checkout/discount.py --test demo_repo/tests/test_discount.py

demo:
	PYTHONPATH=src $(PYTHON) -m axiom.cli --bug demo_repo/checkout/discount.py --test demo_repo/tests/test_discount.py

demo-falsified:
	PYTHONPATH=src $(PYTHON) -m axiom.cli --bug demo_repo/checkout/discount.py --test demo_repo/tests/test_discount.py --verify-original

demo-unproven:
	PYTHONPATH=src $(PYTHON) -m axiom.cli --bug demo_repo/checkout/discount.py --test demo_repo/tests/test_discount.py --force-unproven

demo-non-contradiction:
	PYTHONPATH=src $(PYTHON) -m axiom.cli --bug demo_repo/checkout/order.py --test demo_repo/tests/test_checkout_state.py

demo-identity:
	PYTHONPATH=src $(PYTHON) -m axiom.cli --bug demo_repo/checkout/fulfillment.py --test demo_repo/tests/test_identity.py

verify-crosshair:
	bash scripts/smoke_crosshair.sh

verify-acp:
	bash scripts/smoke_acp.sh
