#!/usr/bin/env python3
"""Prove default H03 RTL vs mapped netlist using EQY and sky130 formal models.

Avoids importing unused Liberty blackboxes into the gold design. That import
causes LibreLane 3.0.16's generic EQY script to fail while combining designs.
No output signals or proof partitions are excluded.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--pdk-root", type=Path, required=True)
    parser.add_argument("--top", choices=["core", "wrapper"], default="core")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("Output must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    top = "h03_spi_master" if args.top == "core" else "tt_um_h03_spi_mode0"
    sources = [ROOT / "04_IMPLEMENTATION/rtl/h03_spi_master.sv"]
    if args.top == "wrapper":
        sources.append(ROOT / "04_IMPLEMENTATION/rtl/tt_um_h03_spi_mode0.sv")
    models = args.pdk_root.resolve() / "sky130A/libs.ref/sky130_fd_sc_hd/verilog"
    inputs = sources + [args.netlist.resolve(), models / "primitives.v", models / "sky130_fd_sc_hd.v"]
    summary = {"status": "RUNNING", "top": top, "half_cycles": 4, "msb_first": 1,
               "started_utc": datetime.now(timezone.utc).isoformat(), "commands": [],
               "proof_scope": "Sequential RTL equivalence to the selected netlist; no timing delays",
               "failures": []}
    def save():
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    def execute(cmd, name, timeout=300):
        result = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace", timeout=timeout)
        (out / (name + ".log")).write_text(result.stdout, encoding="utf-8")
        summary["commands"].append({"command": cmd, "returncode": result.returncode})
        save()
        if result.returncode:
            raise RuntimeError(name + " exited " + str(result.returncode))
    try:
        for tool in ["eqy", "eqy.formal_pdk_proc"]:
            if not shutil.which(tool):
                raise RuntimeError("Missing executable: " + tool)
        summary["sources_sha256"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
        processed = out / "formal_pdk.v"
        execute(["eqy.formal_pdk_proc", "--output", str(processed)] + [str(p) for p in inputs[-2:]], "formal_models")
        # Yosys accepts quoted paths, including spaces. Backslashes are escaped.
        def quoted(path):
            return '"' + str(path).replace("\\", "\\\\").replace('"', '\\"') + '"'
        script = ("[gold]\nread_verilog -formal -sv " + " ".join(map(quoted, sources)) +
                  "\nchparam -set HALF_CYCLES 4 -set MSB_FIRST 1 " + top +
                  "\n[gate]\nread_verilog -formal -sv " + quoted(processed) + " " + quoted(args.netlist.resolve()) +
                  "\n[script]\nhierarchy -top " + top + " -purge_lib\nproc\nprep -top " + top +
                  " -flatten\nmemory -nomap\nasync2sync\ncheck -assert\n" +
                  "[strategy sat]\nuse sat\ndepth 10\n" +
                  "[strategy pdr]\nuse sby\nengine abc pdr\n")
        script_path = out / (top + ".eqy")
        script_path.write_text(script, encoding="utf-8")
        execute(["eqy", "-f", str(script_path), "-d", str(out / "proof")], "equivalence", timeout=600)
        status_path = out / "proof/PASS"
        proof_log = (out / "equivalence.log").read_text(encoding="utf-8")
        summary["proof_status"] = "PASS" if status_path.is_file() and "DONE (PASS, rc=0)" in proof_log else "FAIL"
        if summary["proof_status"] != "PASS":
            raise RuntimeError("EQY did not report PASS")
        summary["status"] = "PASS"
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        summary["status"] = "FAIL"
        summary["failures"].append(str(exc))
    summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save()
    print("EQUIVALENCE", top, summary["status"])
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
