"""Compare a VCD-derived completed frame to the independent event oracle."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("waveform", type=Path)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
model_path = ROOT / "05_VERIFICATION/golden_model/reference_model.py"
spec = importlib.util.spec_from_file_location("h03_oracle", model_path)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
actual = json.loads(args.waveform.read_text(encoding="utf-8"))
expected = model.expected_frame(int(actual["tx_hex"], 16), int(actual["rx_hex"], 16),
                                actual["half_cycles"], bool(actual["msb_first"]),
                                actual["clock_period_ns"])
checks = {
    "tx_pin_samples": actual["tx_bits"] == expected["tx_bits"],
    "rx_pin_samples": actual["rx_bits"] == expected["rx_bits"],
    "rising_edge_times": actual["rise_ns"] == [e["time_ns"] for e in expected["events"] if e["kind"] == "rise"],
    "falling_edge_times": actual["fall_ns"] == [e["time_ns"] for e in expected["events"] if e["kind"] == "fall"],
    "cs_release_and_done": actual["cs_low_ns"] == expected["done_cycle"] * expected["clock_period_ns"],
}
result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
          "vcd_sha256": actual["sha256"], "waveform_json_sha256": hashlib.sha256(args.waveform.read_bytes()).hexdigest(),
          "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
          "scope": "One selected completed VCD frame; broader coverage is in the RTL regression", "oracle": expected}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("VCD ORACLE", result["status"], len(checks), "checks")
raise SystemExit(0 if result["status"] == "PASS" else 1)
