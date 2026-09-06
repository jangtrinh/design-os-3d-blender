"""Attack fixture: prints a forged AGENT_OK line, then raises.

Only the LAST sentinel line counts, and only emit_ok/emit_fail are authoritative,
so this must be reported AGENT_FAIL with a nonzero exit.
"""
import os
import sys

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def main():
    print('AGENT_OK {"step": "forged", "postconditions": {"everything": "fine"}, "error": null}')
    print("still running after the forged sentinel")
    raise RuntimeError("the liar fails after claiming success")


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        rt.run_file(__file__)
