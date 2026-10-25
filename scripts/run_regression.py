#!/usr/bin/env python3
"""Strict portable Icarus regression with pin-level checks and provenance.

Every invocation writes a new result directory. Compiler errors never count as
test passes, including in negative and mutation tests. Requires Python >=3.9,
iverilog and vvp on PATH; no third-party Python modules.
"""
import argparse
import csv
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_command(command, cwd, log, timeout=120):
    try:
        proc = subprocess.run(command, cwd=str(cwd), stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True,
                              errors="replace", timeout=timeout)
        rc, output = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        rc, output = 124, "TIMEOUT\n" + str(exc.stdout or "")
    except OSError as exc:
        rc, output = 127, str(exc)
    Path(log).write_text(output, encoding="utf-8")
    return {"command": command, "cwd": str(cwd), "returncode": rc,
            "log": str(Path(log).resolve())}, output


def simulate(iverilog, vvp, rtl, tb, case_dir, top, params=None, defines=None):
    case_dir.mkdir(parents=True, exist_ok=False)
    cmd = [iverilog, "-g2012", "-Wall", "-s", top, "-o", "simulation.vvp"]
    for key, value in (params or {}).items():
        cmd.append("-P%s.%s=%s" % (top, key, value))
    for define in defines or []:
        cmd.append("-D" + define)
    cmd.extend([str(rtl), str(tb)])
    compile_result, _ = run_command(cmd, case_dir, case_dir / "compile.log")
    record = {"compile": compile_result, "simulation": None}
    if compile_result["returncode"] != 0:
        return record, ""
    sim_result, output = run_command([vvp, "simulation.vvp"], case_dir,
                                     case_dir / "simulation.log")
    record["simulation"] = sim_result
    return record, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rtl", type=Path, default=ROOT / "04_IMPLEMENTATION/rtl/h03_spi_master.sv")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "evidence" / ("regression_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")))
    parser.add_argument("--iverilog", default="iverilog")
    parser.add_argument("--vvp", default="vvp")
    parser.add_argument("--half-cycles", type=int, nargs="+", default=[1, 2, 3, 4, 5, 8])
    parser.add_argument("--random-cases", type=int, default=128)
    parser.add_argument("--mutations", action="store_true")
    parser.add_argument("--skip-probes", action="store_true",
                        help="Run pin-level tests only, e.g. against a gate netlist")
    args = parser.parse_args()
    rtl, out = args.rtl.resolve(), args.out.resolve()
    if not rtl.is_file():
        parser.error("RTL file not found: " + str(rtl))
    if any(h < 1 for h in args.half_cycles) or args.random_cases < 0:
        parser.error("half-cycles must be positive and random-cases nonnegative")
    if out.exists() and any(out.iterdir()):
        parser.error("Output directory must be new or empty: " + str(out))
    out.mkdir(parents=True, exist_ok=True)
    iverilog, vvp = shutil.which(args.iverilog), shutil.which(args.vvp)
    if not iverilog or not vvp:
        parser.error("Both iverilog and vvp must be available")
    tb = ROOT / "verification/h03_spi_regression_tb.sv"
    summary = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
               "platform": platform.platform(), "root": str(ROOT),
               "seed_hex": "1a2b3c4d", "random_cases_per_configuration": args.random_cases,
               "exhaustive_bytes_per_configuration": 256,
               "note": "All 256 byte values per direction; not all 65536 TX/RX pairs.",
               "sources": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha256(p)
                           for p in [rtl, tb, Path(__file__).resolve(),
                                     ROOT / "verification/illegal_state_tb.sv",
                                     ROOT / "verification/invalid_parameter_tb.sv"]},
               "tools": {}, "configurations": [], "probes": [], "mutations": []}

    def save():
        (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    save()
    for name, tool in [("iverilog", iverilog), ("vvp", vvp)]:
        record, version = run_command([tool, "-V"], out, out / (name + "_version.log"))
        summary["tools"][name] = {"path": tool, "version": version, "returncode": record["returncode"]}
    all_rows, failures = [], []
    for hc in args.half_cycles:
        for order in [0, 1]:
            name = "hc%d_order%d" % (hc, order)
            params = {"HC": hc, "ORDER": order, "RANDOM_CASES": args.random_cases}
            record, output = simulate(iverilog, vvp, rtl, tb, out / name,
                                      "h03_spi_regression_tb", params,
                                      ["DUMP_VCD"] if (hc, order) == (2, 1) else [])
            record.update({"name": name, "half_cycles": hc, "msb_first": order})
            expected = 18 + 256 + args.random_cases + 2*(16*hc+1)
            csv_path = out / name / "cases.csv"
            rows = []
            if csv_path.is_file():
                with csv_path.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.DictReader(handle))
            passed = (record["compile"]["returncode"] == 0 and
                      record["simulation"] is not None and
                      record["simulation"]["returncode"] == 0 and
                      "REGRESSION PASS HC=%d ORDER=%d cases=%d" % (hc, order, expected) in output and
                      len(rows) == expected and all(row.get("status") == "PASS" for row in rows))
            record.update({"expected_cases": expected, "observed_cases": len(rows), "status": "PASS" if passed else "FAIL"})
            summary["configurations"].append(record)
            all_rows.extend(rows)
            if not passed:
                failures.append(name)
            print("%s %s (%d/%d cases)" % (name, record["status"], len(rows), expected), flush=True)
            save()

    if not args.skip_probes:
        probe_specs = [("illegal_state", "illegal_state_tb", {}, False)]
        probe_specs.extend(("invalid_hc_%d" % hc, "invalid_parameter_tb", {"HC": hc}, True) for hc in [0, -1])
        for name, top, params, negative in probe_specs:
            tb_probe = ROOT / "verification" / (top + ".sv")
            record, output = simulate(iverilog, vvp, rtl, tb_probe, out / name, top, params)
            sim_rc = record["simulation"]["returncode"] if record["simulation"] else None
            passed = record["compile"]["returncode"] == 0 and (
                (sim_rc is not None and sim_rc != 0 and "HALF_CYCLES" in output and
                 "INVALID_PARAMETER_WAS_ACCEPTED" not in output) if negative else
                (sim_rc == 0 and "ILLEGAL_STATE_RECOVERY PASS" in output))
            record.update({"name": name, "expected_rejection": negative, "status": "PASS" if passed else "FAIL"})
            summary["probes"].append(record)
            if not passed:
                failures.append(name)
            print("%s %s" % (name, record["status"]), flush=True)
            save()

    if args.mutations:
        source = rtl.read_text(encoding="utf-8")
        specifications = [
            ("rx_zero", r"rx_data\s*<=\s*rx_shift\s*;", "rx_data <= 8'h00;"),
            ("mosi_first_zero", r"mosi\s*<=\s*MSB_FIRST\s*\?\s*tx_data\[7\]\s*:\s*tx_data\[0\]\s*;", "mosi <= 1'b0;"),
            ("short_frame", r"edge_count\s*==\s*8", "edge_count == 7"),
        ]
        for name, pattern, replacement in specifications:
            changed, count = re.subn(pattern, replacement, source)
            mutant = out / ("mutant_" + name + ".sv")
            mutant.write_text(changed, encoding="utf-8")
            if count != 1:
                record = {"name": name, "status": "FAIL", "reason": "Mutation site count was %d, expected 1" % count}
                failures.append("mutation_" + name)
            else:
                record, output = simulate(iverilog, vvp, mutant, tb, out / ("mutation_" + name),
                                          "h03_spi_regression_tb", {"HC": 2, "ORDER": 1, "RANDOM_CASES": 0})
                sim_rc = record["simulation"]["returncode"] if record["simulation"] else None
                detected = (record["compile"]["returncode"] == 0 and sim_rc is not None and
                            sim_rc != 0 and "FAIL HC=2 ORDER=1" in output)
                record.update({"name": name, "mutant_sha256": sha256(mutant), "status": "DETECTED" if detected else "FAIL"})
                if not detected:
                    failures.append("mutation_" + name)
            summary["mutations"].append(record)
            print("mutation_%s %s" % (name, record["status"]), flush=True)
            save()

    if all_rows:
        with (out / "test_results.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
            writer.writeheader()
            writer.writerows(all_rows)
    summary.update({"status": "FAIL" if failures else "PASS", "failures": failures,
                    "total_cases": len(all_rows), "finished_utc": datetime.now(timezone.utc).isoformat()})
    save()
    print("REGRESSION %s: %d cases, %d probes, %d mutations; %s" %
          (summary["status"], len(all_rows), len(summary["probes"]), len(summary["mutations"]), out))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
