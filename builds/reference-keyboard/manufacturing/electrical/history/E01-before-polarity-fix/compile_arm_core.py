#!/usr/bin/env python3
"""Compile the portable CK-001 control core as a real ARMv6-M relocatable object."""
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--object", type=Path, default=FW / "ck001_logic-armv6m.o")
    ap.add_argument("--report", type=Path, default=HERE / "arm-core-build.json")
    args = ap.parse_args()
    obj, report = args.object.resolve(), args.report.resolve()
    if not obj.is_relative_to(HERE) or not report.is_relative_to(HERE): raise ValueError("outputs must stay in electrical namespace")
    if obj.exists() or report.exists(): raise FileExistsError("refuse overwrite of ARM evidence")
    compiler = Path("/usr/bin/clang")
    source = FW / "ck001_logic.c"
    command = [str(compiler), "--target=arm-none-eabi", "-mcpu=cortex-m0plus", "-mthumb", "-ffreestanding",
               "-fno-builtin", "-Wall", "-Wextra", "-Werror", "-c", str(source), "-o", str(obj)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    kind = subprocess.run(["/usr/bin/file", str(obj)], check=True, capture_output=True, text=True).stdout.strip()
    if "ELF 32-bit LSB relocatable, ARM, EABI5" not in kind: raise RuntimeError(kind)
    result = {"schema_version":1,"design_id":"CK-001-E01","status":"PASS_ARMV6M_CORE_OBJECT",
              "compiler":str(compiler),"compiler_version":subprocess.run([str(compiler),"--version"],check=True,capture_output=True,text=True).stdout.splitlines()[0],
              "command":command,"source":{"path":str(source.relative_to(HERE)),"sha256":sha(source)},
              "object":{"path":str(obj.relative_to(HERE)),"sha256":sha(obj),"file_type":kind},
              "limits":["Relocatable Cortex-M0+ control-core object only; no RP2040 SDK/QMK link, USB firmware, startup code, UF2, timing or hardware execution proof."]}
    with report.open("x",encoding="utf-8") as handle: json.dump(result,handle,indent=2,allow_nan=False); handle.write("\n")
    print(json.dumps({"status":result["status"],"object_sha256":result["object"]["sha256"],"report":str(report)}))


if __name__ == "__main__": main()
