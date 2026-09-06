"""Echoes the payload's own argv, to prove headless-run.sh forwards `-- args`."""
import os
import sys

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def main():
    import agent_runtime as rt
    rt.emit_ok("argv-echo", argv=sys.argv[1:])


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        rt.run_file(__file__, extra)
