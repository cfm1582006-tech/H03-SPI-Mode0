#!/usr/bin/env python3
"""Self-check Tiny Tapeout pad mapping and ENA behavior with Icarus."""
import argparse
import csv
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from run_regression import ROOT, run_command, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "evidence" / ("wrapper_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")))
    parser.add_argument("--iverilog", default="iverilog")
    parser.add_argument("--vvp", default="vvp")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("Output directory must be new or empty: " + str(out))
    out.mkdir(parents=True, exist_ok=True)
    iverilog, vvp = shutil.which(args.iverilog), shutil.which(args.vvp)
    if not iverilog or not vvp:
        parser.error("Both iverilog and vvp must be available")
    sources = [ROOT / "04_IMPLEMENTATION/rtl/h03_spi_master.sv",
               ROOT / "04_IMPLEMENTATION/rtl/tt_um_h03_spi_mode0.sv",
               ROOT / "verification/h03_wrapper_tb.sv"]
    summary = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
               "platform": platform.platform(), "total_cases": 0,
               "sources": {str(p.relative_to(ROOT)): sha256(p)
                           for p in sources + [Path(__file__).resolve(), ROOT / "scripts/run_regression.py"]},
               "tools": {}, "configurations": [], "failures": []}

    def save():
        (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    save()
    for name, tool in [("iverilog", iverilog), ("vvp", vvp)]:
        record, version = run_command([tool, "-V"], out, out / (name + "_version.log"))
        summary["tools"][name] = {"path": tool, "version": version, "returncode": record["returncode"]}
    all_rows = []
    for hc in [1, 4, 5]:
        for order in [0, 1]:
            name = "hc%d_order%d" % (hc, order)
            case_dir = out / name
            case_dir.mkdir(exist_ok=False)
            command = [iverilog, "-g2012", "-Wall", "-s", "h03_wrapper_tb",
                       "-Ph03_wrapper_tb.HC=%d" % hc, "-Ph03_wrapper_tb.ORDER=%d" % order,
                       "-o", "simulation.vvp"] + [str(p) for p in sources]
            compile_result, _ = run_command(command, case_dir, case_dir / "compile.log")
            record = {"name": name, "half_cycles": hc, "msb_first": order,
                      "compile": compile_result, "simulation": None, "expected_cases": 13}
            output = ""
            if compile_result["returncode"] == 0:
                sim_result, output = run_command([vvp, "simulation.vvp"], case_dir, case_dir / "simulation.log")
                record["simulation"] = sim_result
            rows = []
            if (case_dir / "cases.csv").is_file():
                with (case_dir / "cases.csv").open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.DictReader(handle))
            passed = (record["compile"]["returncode"] == 0 and record["simulation"] is not None and
                      record["simulation"]["returncode"] == 0 and
                      "WRAPPER PASS HC=%d ORDER=%d cases=13" % (hc, order) in output and
                      len(rows) == 13 and all(row.get("status") == "PASS" for row in rows))
            record.update({"observed_cases": len(rows), "status": "PASS" if passed else "FAIL"})
            summary["configurations"].append(record)
            all_rows.extend(rows)
            if not passed:
                summary["failures"].append(name)
            print("wrapper_%s %s (%d/13 cases)" % (name, record["status"], len(rows)), flush=True)
            save()
    if all_rows:
        with (out / "test_results.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
            writer.writeheader()
            writer.writerows(all_rows)
    summary.update({"status": "FAIL" if summary["failures"] else "PASS",
                    "total_cases": len(all_rows), "finished_utc": datetime.now(timezone.utc).isoformat()})
    save()
    print("WRAPPER REGRESSION %s: %d cases; %s" % (summary["status"], len(all_rows), out))
    return 1 if summary["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
