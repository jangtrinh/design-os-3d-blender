#!/usr/bin/env python3
"""Compile and run host-testable CK-001 firmware logic without target toolchains."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
FW = HERE / "firmware"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--report", type=Path, required=True); args = ap.parse_args()
    compiler = Path("/usr/bin/gcc")
    if not compiler.is_file(): raise FileNotFoundError(compiler)
    binary = FW / ".ck001_logic_test.tmp"
    if binary.exists(): raise FileExistsError(binary)
    command = [str(compiler), "-std=c11", "-Wall", "-Wextra", "-Werror",
               str(FW/"ck001_logic.c"), str(FW/"test_logic.c"), "-o", str(binary)]
    try:
        build = subprocess.run(command, check=True, capture_output=True, text=True)
        run = subprocess.run([str(binary)], check=True, capture_output=True, text=True)
        version = subprocess.run([str(compiler), "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0]
    finally:
        binary.unlink(missing_ok=True)
    result = {"schema_version":1,"design_id":"CK-001-E01","status":"PASS_HOST_C_LOGIC",
              "compiler":str(compiler),"compiler_version":version,"compile_flags":["-std=c11","-Wall","-Wextra","-Werror"],
              "compile_stderr":build.stderr,"test_stdout":run.stdout.strip(),
              "sources":{"logic_c":{"path":"firmware/ck001_logic.c","sha256":sha(FW/"ck001_logic.c")},
                         "test_c":{"path":"firmware/test_logic.c","sha256":sha(FW/"test_logic.c")}},
              "scope":["quadrature Gray decoding including bounce and invalid transition", "58-key logical matrix indexing"],
              "limits":["Host C logic only; not an RP2040/QMK target build, USB stack test, GPIO timing test or hardware bench test."]}
    path = args.report.resolve()
    if not path.is_relative_to(HERE): raise ValueError("report must stay in electrical namespace")
    with path.open("x", encoding="utf-8") as handle: json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({"status":result["status"],"output":result["test_stdout"],"report":str(path)}))


if __name__ == "__main__": main()
