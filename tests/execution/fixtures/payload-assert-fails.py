"""Payload whose declared requirement fails: AGENT_FAIL + exit 1 (not 3)."""
import os
import sys

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def main():
    measured_mm = 41.0
    assert measured_mm == 40.0, "width %.1f mm outside tolerance" % measured_mm


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        rt.run_file(__file__)
