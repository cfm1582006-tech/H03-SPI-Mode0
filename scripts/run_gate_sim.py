#!/usr/bin/env python3
"""Pin-level functional regression of a mapped sky130 netlist (no SDF)."""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--pdk-root", type=Path, required=True,
                        help="Version directory containing sky130A")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top", choices=["core", "wrapper"], default="core")
    parser.add_argument("--timeout", type=int, default=180,
                        help="Timeout per compiler/simulator command, in seconds")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("Output must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    top = "h03_spi_regression_tb" if args.top == "core" else "h03_wrapper_tb"
    tb_name = "h03_spi_regression_tb.sv" if args.top == "core" else "h03_wrapper_tb.sv"
    expected = 532 if args.top == "core" else 13
    marker = ("REGRESSION" if args.top == "core" else "WRAPPER") + " PASS HC=4 ORDER=1 cases=%d" % expected
    summary = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
               "scope": "Zero-delay functional gate simulation; no SDF annotation",
               "top": args.top, "half_cycles": 4, "msb_first": 1,
               "expected_cases": expected, "total_cases": 0,
               "sources": {}, "commands": [], "failures": []}

    def save():
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    def fail(reason):
        summary["status"] = "FAIL"
        summary["failures"].append(reason)

    def run_stage(name, cmd):
        timed_out = False
        try:
            proc = subprocess.run(cmd, cwd=out, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True,
                                  errors="replace", timeout=args.timeout)
            code, output = proc.returncode, proc.stdout
        except subprocess.TimeoutExpired as exc:
            code, timed_out = 124, True
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            output += "\nTIMEOUT after %d seconds\n" % args.timeout
        except OSError as exc:
            code, output = 127, str(exc) + "\n"
        (out / (name + ".log")).write_text(output, encoding="utf-8")
        summary["commands"].append({"stage": name, "command": cmd,
                                    "returncode": code, "timed_out": timed_out})
        save()
        return code, output

    save()
    libdir = args.pdk_root.resolve() / "sky130A/libs.ref/sky130_fd_sc_hd/verilog"
    sources = [libdir / "primitives.v", libdir / "sky130_fd_sc_hd.v",
               args.netlist.resolve(), ROOT / "verification" / tb_name]
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        fail("Missing input: " + str(missing))
    else:
        try:
            summary["sources"] = {str(p): digest(p) for p in sources + [Path(__file__).resolve()]}
        except OSError as exc:
            fail("Cannot read source: " + str(exc))
    if args.timeout < 1:
        fail("Timeout must be at least one second")
    compiler, simulator = shutil.which("iverilog"), shutil.which("vvp")
    if not compiler or not simulator:
        fail("iverilog and vvp must be on PATH")
    if summary["status"] != "FAIL":
        command = [compiler, "-g2012", "-DFUNCTIONAL", "-DGATE_LEVEL",
                   "-s", top, "-P%s.HC=4" % top,
                   "-P%s.ORDER=1" % top, "-o", "simulation.vvp"]
        command += [str(p) for p in sources]
        compile_code, _ = run_stage("compile", command)
        if compile_code:
            fail("Compiler returned %d; simulation was not run" % compile_code)
        else:
            sim_code, sim_output = run_stage("simulation", [simulator, "simulation.vvp"])
            if sim_code:
                fail("Simulator returned %d" % sim_code)
            else:
                try:
                    with (out / "cases.csv").open(newline="", encoding="utf-8") as stream:
                        rows = list(csv.DictReader(stream))
                    summary["total_cases"] = len(rows)
                    passed = (len(rows) == expected and all(
                        row.get("status") == "PASS" and row.get("half_cycles") == "4" and
                        row.get("msb_first") == "1" for row in rows))
                    passed = passed and marker in sim_output.splitlines()
                    if not passed:
                        fail("Case count, status, configuration or completion marker mismatch")
                except (OSError, UnicodeError, csv.Error) as exc:
                    fail("Cannot read case results: " + str(exc))
    if summary["status"] != "FAIL":
        summary["status"] = "PASS"
    summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save()
    print("GATE SIM", args.top, summary["status"], summary["total_cases"], "cases")
    for reason in summary["failures"]:
        print(" -", reason)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
