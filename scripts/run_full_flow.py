#!/usr/bin/env python3
"""Run strict functional verification followed by fresh LibreLane Classic runs.

Requires Python >= 3.9, librelane, iverilog and vvp on PATH and a local PDK.
No third-party Python packages are needed by this orchestration script.
Never resumes an existing run, overwrites evidence, or substitutes old metrics.
"""
import argparse
import hashlib
import json
import math
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP_NAMES = {"core": "h03_spi_master", "wrapper": "tt_um_h03_spi_mode0"}
ZERO_METRICS = (
    "magic__drc_error__count", "klayout__drc_error__count",
    "route__drc_errors", "design__lvs_error__count",
    "design__lvs_unmatched_device__count", "design__lvs_unmatched_net__count",
    "design__lvs_unmatched_pin__count", "design__xor_difference__count",
    "antenna__violating__nets", "antenna__violating__pins",
    "route__antenna_violation__count", "design__power_grid_violation__count",
    "timing__setup_vio__count", "timing__hold_vio__count",
    "design__max_slew_violation__count", "design__max_cap_violation__count",
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                     allow_nan=False) + "\n", encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def execute(command, cwd, log_path, timeout=None):
    """Preserve exact argv, process exit and a complete combined output log."""
    started = utc_now()
    print("RUN " + " ".join(str(part) for part in command), flush=True)
    try:
        with Path(log_path).open("w", encoding="utf-8") as log:
            process = subprocess.run(command, cwd=str(cwd), stdout=log,
                                     stderr=subprocess.STDOUT, timeout=timeout)
        code, error = process.returncode, None
    except subprocess.TimeoutExpired:
        code, error = 124, "Command timed out"
    except OSError as exc:
        code, error = 127, str(exc)
    if error:
        with Path(log_path).open("a", encoding="utf-8") as log:
            log.write("\n" + error + "\n")
    print("EXIT %s; log %s" % (code, log_path), flush=True)
    return {"command": [str(part) for part in command], "cwd": str(cwd),
            "returncode": code, "log": str(Path(log_path).resolve()),
            "started_utc": started, "finished_utc": utc_now(), "error": error}


def finite_number(metrics, key, failures):
    if key not in metrics:
        failures.append("Missing metric: " + key)
        return None
    value = metrics[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        failures.append("Metric is not a finite number: %s = %r" % (key, value))
        return None
    return value


def inspect_physical_run(run_dir, top_name):
    """Validate final artifacts and all configured timing corners explicitly."""
    run_dir = Path(run_dir)
    final = run_dir / "final"
    failures, selected, artifacts = [], {}, {}
    metrics_path, resolved_path = final / "metrics.json", run_dir / "resolved.json"
    result = {"run_path": str(run_dir.resolve()), "top_module": top_name,
              "metrics_path": str(metrics_path.resolve()), "failures": failures,
              "metrics": selected, "artifacts_sha256": artifacts}
    for path in [metrics_path, resolved_path]:
        if not path.is_file():
            failures.append("Required run file is missing: " + str(path))
    if failures:
        result["status"] = "FAIL"
        return result
    try:
        metrics, config = load_json(metrics_path), load_json(resolved_path)
    except (ValueError, OSError) as exc:
        failures.append("Cannot read run JSON: " + str(exc))
        result["status"] = "FAIL"
        return result
    result["resolved_config_sha256"] = sha256(resolved_path)
    result["final_metrics_sha256"] = sha256(metrics_path)
    result["librelane_version"] = config.get("meta", {}).get("librelane_version")
    if config.get("DESIGN_NAME") != top_name:
        failures.append("Resolved DESIGN_NAME does not match requested top")

    for key in ZERO_METRICS:
        value = finite_number(metrics, key, failures)
        if value is not None:
            selected[key] = value
            if value != 0:
                failures.append("Nonzero violation metric: %s = %s" % (key, value))

    corners = config.get("STA_CORNERS")
    result["sta_corners"] = corners
    if not isinstance(corners, list) or not corners:
        failures.append("Resolved configuration has no STA_CORNERS")
        corners = []
    for corner in corners:
        for kind in ["setup", "hold"]:
            key = "timing__%s_vio__count__corner:%s" % (kind, corner)
            value = finite_number(metrics, key, failures)
            if value is not None:
                selected[key] = value
                if value != 0:
                    failures.append("Timing violation: %s = %s" % (key, value))
    for key in ["timing__setup__ws", "timing__hold__ws"]:
        value = finite_number(metrics, key, failures)
        if value is not None:
            selected[key] = value
            if value < 0:
                failures.append("Negative slack: %s = %s" % (key, value))
    for key in ["design__die__area", "design__core__area",
                "design__instance__area__stdcell", "design__instance__count__stdcell"]:
        value = metrics.get(key)
        if isinstance(value, (int, float)) and math.isfinite(value):
            selected[key] = value
    for key, value in metrics.items():
        if key.startswith("power__") and isinstance(value, (int, float)) and math.isfinite(value):
            selected[key] = value

    required_artifacts = [final / "gds" / (top_name + ".gds"),
                          final / "nl" / (top_name + ".nl.v"),
                          final / "def" / (top_name + ".def"),
                          final / "sdc" / (top_name + ".sdc")]
    for path in required_artifacts:
        if not path.is_file() or path.stat().st_size == 0:
            failures.append("Required final artifact is missing or empty: " + str(path))
    for directory in ["spef", "sdf"]:
        files = list((final / directory).rglob("*")) if (final / directory).is_dir() else []
        if not any(path.is_file() and path.stat().st_size > 0 for path in files):
            failures.append("No extracted final %s artifact" % directory.upper())
    for path in sorted(final.rglob("*")):
        if path.is_file():
            artifacts[str(path.relative_to(run_dir))] = sha256(path)
    result["status"] = "FAIL" if failures else "PASS"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdk-root", type=Path, required=True,
                        help="Directory containing the installed sky130A directory")
    parser.add_argument("--tag", default="h03_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--tops", choices=["core", "wrapper", "both"], default="both")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/full_flow")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,80}", args.tag):
        parser.error("tag must contain 1-81 ASCII letters, digits, dots, dashes or underscores")
    if args.jobs < 1:
        parser.error("jobs must be positive")
    pdk_root, out = args.pdk_root.resolve(), args.out.resolve()
    if not (pdk_root / "sky130A").is_dir():
        parser.error("pdk-root must contain an installed sky130A directory")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("Output path must be a new or empty directory: " + str(out))
    tops = ["core", "wrapper"] if args.tops == "both" else [args.tops]
    plans = [{"top": top, "config": ROOT / "flow" / ("config_%s.json" % top),
              "run_tag": args.tag + "_" + top,
              "run_path": ROOT / "flow/runs" / (args.tag + "_" + top)} for top in tops]
    for plan in plans:
        if not plan["config"].is_file():
            parser.error("Configuration is missing: " + str(plan["config"]))
        if plan["run_path"].exists():
            parser.error("Run already exists; choose a new tag: " + str(plan["run_path"]))
    for tool in ["librelane", "iverilog", "vvp"]:
        if not shutil.which(tool):
            parser.error("Required executable is not on PATH: " + tool)
    regression_script = ROOT / "scripts/run_regression.py"
    if not regression_script.is_file():
        parser.error("Core regression runner is missing")

    out.mkdir(parents=True, exist_ok=True)
    report = {"status": "RUNNING", "started_utc": utc_now(), "root": str(ROOT),
              "platform": platform.platform(), "python": sys.version,
              "pdk_root": str(pdk_root), "tag": args.tag, "tops": tops,
              "tool_versions": {}, "source_sha256": {}, "stages": [], "failures": []}
    report_path = out / "summary.json"

    def save():
        write_json(report_path, report)

    def checked_test(name, script, extra):
        target = out / name
        record = execute([sys.executable, str(script), "--out", str(target)] + extra,
                         ROOT, out / (name + ".log"))
        summary_path = target / "summary.json"
        record.update({"name": name, "summary_path": str(summary_path)})
        record["status"] = "FAIL"
        if summary_path.is_file():
            try:
                test_summary = load_json(summary_path)
                record["test_status"] = test_summary.get("status")
                record["total_cases"] = test_summary.get("total_cases")
                if record["returncode"] == 0 and test_summary.get("status") == "PASS":
                    record["status"] = "PASS"
            except (OSError, ValueError) as exc:
                record["summary_error"] = str(exc)
        report["stages"].append(record)
        save()
        if record["status"] != "PASS":
            raise RuntimeError(name + " failed; inspect its process log and summary")

    save()
    try:
        inputs = sorted(set(
            list((ROOT / "04_IMPLEMENTATION/rtl").glob("*.sv")) +
            list((ROOT / "flow").glob("*.json")) + list((ROOT / "flow").glob("*.sdc")) +
            list((ROOT / "scripts").glob("*.py")) + list((ROOT / "verification").glob("*.sv"))))
        for path in inputs:
            relative = path.relative_to(ROOT)
            report["source_sha256"][str(relative)] = sha256(path)
            snapshot = out / "inputs" / relative
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, snapshot)
        for name, command in [
            ("librelane", ["librelane", "--version"]),
            ("iverilog", ["iverilog", "-V"]), ("vvp", ["vvp", "-V"]),
            ("yosys", ["yosys", "-V"]), ("openroad", ["openroad", "-version"]),
            ("magic", ["magic", "--version"]), ("klayout", ["klayout", "-v"]),
        ]:
            record = execute(command, ROOT, out / (name + "_version.log"), timeout=30)
            record["executable"] = shutil.which(command[0])
            report["tool_versions"][name] = record
        save()
        checked_test("rtl_regression", regression_script, ["--mutations"])
        wrapper_script = ROOT / "scripts/run_wrapper_test.py"
        if wrapper_script.is_file():
            checked_test("wrapper_regression", wrapper_script, [])
        else:
            report["stages"].append({"name": "wrapper_regression", "status": "NOT_AVAILABLE",
                                     "reason": "Optional wrapper runner is absent"})
            save()
        for plan in plans:
            if plan["run_path"].exists():
                raise RuntimeError("Run path was created during preflight; refusing reuse")
            name = "physical_" + plan["top"]
            command = ["librelane", "--manual-pdk", "--pdk-root", str(pdk_root),
                       "--run-tag", plan["run_tag"], "--jobs", str(args.jobs),
                       "--condensed", str(plan["config"])]
            record = execute(command, ROOT, out / (name + ".log"))
            record.update({"name": name, "run_tag": plan["run_tag"],
                           "run_path": str(plan["run_path"]),
                           "config_sha256": sha256(plan["config"])})
            physical = inspect_physical_run(plan["run_path"], TOP_NAMES[plan["top"]])
            write_json(out / (name + "_metrics.json"), physical)
            record["physical_check"] = physical
            record["status"] = "PASS" if record["returncode"] == 0 and physical["status"] == "PASS" else "FAIL"
            report["stages"].append(record)
            save()
            if record["status"] != "PASS":
                raise RuntimeError(name + " failed; no later physical stage was started")
            netlist = plan["run_path"] / "final/nl" / (TOP_NAMES[plan["top"]] + ".nl.v")
            common = ["--netlist", str(netlist), "--pdk-root", str(pdk_root),
                      "--top", plan["top"]]
            checked_test("equivalence_" + plan["top"], ROOT / "scripts/run_equivalence.py", common)
            checked_test("gate_sim_" + plan["top"], ROOT / "scripts/run_gate_sim.py", common)
        changed = [str(path.relative_to(ROOT)) for path in inputs
                   if not path.is_file() or sha256(path) != report["source_sha256"][str(path.relative_to(ROOT))]]
        if changed:
            report["changed_inputs"] = changed
            raise RuntimeError("Inputs changed during the flow; results are not reproducible")
        report["status"] = "PASS"
    except (RuntimeError, OSError, ValueError, KeyboardInterrupt) as exc:
        report["status"] = "FAIL"
        report["failures"].append(str(exc) or "Interrupted by user")
    finally:
        report["finished_utc"] = utc_now()
        save()
    print("FULL FLOW %s: %s" % (report["status"], report_path), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
