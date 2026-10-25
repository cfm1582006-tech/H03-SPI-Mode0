"""Extract and plot a completed SPI frame from actual VCD observations.

Identifiers are resolved from $scope/$var declarations; no simulator-specific
identifier characters are assumed. Frame indices are zero based. Default index
3 is pattern_96 (TX=96/RX=C3) in the supplied regression.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import statistics
from pathlib import Path

REQUIRED = ("cs_n", "sclk", "mosi", "miso", "busy", "done", "tx_data", "rx_data")
TRACKS = ("cs_n", "sclk", "mosi", "miso", "busy", "done")


def parse_vcd(vcd: Path, requested_scope: str | None = None) -> dict:
    raw = vcd.read_text(encoding="utf-8-sig")
    header, body = re.split(r"\$enddefinitions\s+\$end", raw, maxsplit=1)
    scale = re.search(r"\$timescale\s+(\d+)\s*(fs|ps|ns|us|ms|s)\s+\$end", header)
    if not scale:
        raise ValueError("VCD timescale missing or unsupported")
    factor_ns = int(scale[1]) * dict(fs=1e-6, ps=.001, ns=1, us=1e3, ms=1e6, s=1e9)[scale[2]]
    scopes, declarations, stack = {}, {}, []
    for directive in re.finditer(r"\$(scope|upscope|var)\b(.*?)\$end", header, re.S):
        kind, args = directive[1], directive[2].split()
        if kind == "scope":
            stack.append(args[1])
        elif kind == "upscope":
            if not stack:
                raise ValueError("Unbalanced VCD $upscope declaration")
            stack.pop()
        else:
            var_type, width, code, name = args[:4]
            scope = ".".join(stack)
            scopes.setdefault(scope, {})[name] = code
            declarations[(scope, name)] = dict(code=code, width=int(width), type=var_type)
    candidates = [scope for scope, names in scopes.items() if set(REQUIRED) <= set(names)]
    if requested_scope:
        if requested_scope not in candidates:
            raise ValueError(f"Scope {requested_scope!r} lacks required SPI signals")
        scope = requested_scope
    elif candidates:
        # The testbench's top-level pin names take precedence over DUT internals.
        minimum_depth = min(name.count(".") for name in candidates)
        shallowest = [name for name in candidates if name.count(".") == minimum_depth]
        if len(shallowest) != 1:
            raise ValueError(f"Multiple SPI scopes; select --scope from {shallowest}")
        scope = shallowest[0]
    else:
        raise ValueError(f"No scope provides signals {REQUIRED}")
    signal_codes = dict(scopes[scope])
    tracked_codes = set(signal_codes.values())
    events = {code: [] for code in tracked_codes}
    time_ns = 0.0
    for source_line in body.splitlines():
        line = source_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            time_ns = int(line[1:]) * factor_ns
        elif line[0].lower() in "01xz":
            code, value = line[1:].strip(), line[0].lower()
            if code in events:
                events[code].append((time_ns, value))
        elif line[0].lower() == "b":
            value, code = line[1:].split()
            if code in events:
                events[code].append((time_ns, value.lower()))
    # Keep the final settled value at each timestamp; omit repeated dump values.
    normalized = {}
    for code, sequence in events.items():
        settled = {}
        for time, value in sequence:
            settled[time] = value
        normalized[code] = []
        for time, value in sorted(settled.items()):
            if not normalized[code] or normalized[code][-1][1] != value:
                normalized[code].append((time, value))
    return dict(scope=scope, signal_codes=signal_codes, events=normalized,
                timescale=scale[0].replace("\n", " ").replace("\t", " "),
                factor_ns=factor_ns, sha256=hashlib.sha256(vcd.read_bytes()).hexdigest())


def extract(vcd: Path, frame_index: int = 3, scope: str | None = None) -> dict:
    parsed = parse_vcd(vcd, scope)
    codes, events = parsed["signal_codes"], parsed["events"]
    event_times = {code: [pair[0] for pair in values] for code, values in events.items()}

    def value_at(name: str, time: float) -> int:
        code = codes[name]
        at = bisect.bisect_right(event_times[code], time) - 1
        if at < 0 or any(char in events[code][at][1] for char in "xz"):
            raise ValueError(f"Unknown or missing {name} at {time} ns")
        return int(events[code][at][1], 2)

    def edges(name: str, before: str, after: str) -> list[float]:
        sequence = events[codes[name]]
        return [time for index, (time, value) in enumerate(sequence)
                if index and sequence[index-1][1] == before and value == after]

    if frame_index < 0:
        raise ValueError("frame index must be nonnegative")
    starts = edges("cs_n", "1", "0")
    if frame_index >= len(starts):
        raise ValueError(f"Requested frame {frame_index}, but only {len(starts)} CS assertions exist")
    start = starts[frame_index]
    completions = [time for time in edges("cs_n", "0", "1") if time > start]
    if not completions:
        raise ValueError("Selected frame has no CS release")
    end = completions[0]
    rises_abs = [time for time in edges("sclk", "0", "1") if start < time < end]
    falls_abs = [time for time in edges("sclk", "1", "0") if start < time < end]
    if len(rises_abs) != 8 or len(falls_abs) != 8:
        raise ValueError(f"Selected frame is not complete: {len(rises_abs)} rises/{len(falls_abs)} falls")
    transitions = sorted(rises_abs + falls_abs)
    half_ns = statistics.median([right-left for left, right in zip(transitions, transitions[1:])])
    if any(abs(right-left-half_ns) > 1e-6 for left, right in zip(transitions, transitions[1:])):
        raise ValueError("Selected frame has an inconsistent SCLK half period")
    order_name = next((name for name in ("ORDER", "MSB_FIRST") if name in codes), None)
    order = value_at(order_name, start) if order_name else 1
    if order not in (0, 1):
        raise ValueError("Invalid bit-order parameter")
    tx_bits = [value_at("mosi", time) for time in rises_abs]
    rx_bits = [value_at("miso", time) for time in rises_abs]

    def assemble(bits):
        sequence = bits if order else bits[::-1]
        return int("".join(map(str, sequence)), 2)

    observed_tx, observed_rx = assemble(tx_bits), assemble(rx_bits)
    if observed_tx != value_at("tx_data", start):
        raise ValueError("Sampled MOSI differs from TX input at acceptance")
    if observed_rx != value_at("rx_data", end):
        raise ValueError("Sampled MISO differs from completed RX byte")
    if value_at("done", end) != 1 or value_at("busy", end) != 0 or value_at("sclk", end) != 0:
        raise ValueError("CS release lacks correct completion handshake")
    hc_name = next((name for name in ("HC", "HALF_CYCLES") if name in codes), None)
    half_cycles = value_at(hc_name, start) if hc_name else None
    clock_ns = half_ns / half_cycles if half_cycles else None
    margin_ns = clock_ns * 2 if clock_ns else half_ns
    window_start, window_end = max(0, start - margin_ns), end + margin_ns
    series = []
    for index, name in enumerate(TRACKS):
        offset = 10 - 2 * index
        previous = value_at(name, window_start)
        times, values = [round(window_start-start, 6)], [offset + previous*.7]
        raw_points = [[round(window_start-start, 6), previous]]
        for time, bits in events[codes[name]]:
            if window_start < time <= window_end:
                if any(char in bits for char in "xz"):
                    raise ValueError(f"Unknown {name} in plotted window")
                current = int(bits, 2)
                relative = round(time-start, 6)
                times.extend([relative, relative])
                values.extend([offset+previous*.7, offset+current*.7])
                raw_points.append([relative, current])
                previous = current
        times.append(round(window_end-start, 6))
        values.append(offset+previous*.7)
        raw_points.append([round(window_end-start, 6), previous])
        series.append(dict(name=name, xValues=times, values=values, points=raw_points))
    return dict(
        source=str(vcd.resolve()), sha256=parsed["sha256"],
        scope=parsed["scope"],
        resolved_identifiers={name: codes[name] for name in REQUIRED},
        frame_index_zero_based=frame_index, absolute_start_ns=start,
        absolute_end_ns=end, cs_low_ns=end-start, half_period_ns=half_ns,
        half_cycles=half_cycles, clock_period_ns=clock_ns, msb_first=order,
        nominal_setup_ns=half_ns,
        rise_ns=[round(time-start, 6) for time in rises_abs],
        fall_ns=[round(time-start, 6) for time in falls_abs],
        tx_hex=f"{observed_tx:02X}", rx_hex=f"{observed_rx:02X}",
        tx_bits=tx_bits, rx_bits=rx_bits,
        evidence="All plotted levels and sample bits are read from this VCD",
        series=series,
    )


def plot(result: dict, destination: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    figure, axis = plt.subplots(figsize=(14, 7))
    colors = ["#173f5f", "#0077b6", "#2a9d8f", "#e76f51", "#7b2cbf", "#bc6c25"]
    for series, color in zip(result["series"], colors):
        axis.plot(series["xValues"], series["values"], color=color, linewidth=2.1)
    for index, time in enumerate(result["rise_ns"]):
        axis.axvline(time, color="#b7c0ca", linewidth=.8, linestyle="--", zorder=0)
        axis.text(time, 9.15, str(index+1), ha="center", fontsize=9, color="#4b5563")
        axis.text(time, 6.95, str(result["tx_bits"][index]), ha="center", fontsize=10, color=colors[2])
        axis.text(time, 4.95, str(result["rx_bits"][index]), ha="center", fontsize=10, color=colors[3])
    setup = result["nominal_setup_ns"]
    axis.axvspan(0, result["rise_ns"][0], color="#cde8ff", alpha=.6, zorder=-1)
    axis.annotate("", xy=(0, 11.35), xytext=(setup, 11.35),
                  arrowprops=dict(arrowstyle="<->", color="#173f5f", linewidth=1.4))
    axis.text(setup/2, 11.57, f"nominal setup {setup:g} ns", ha="center", fontsize=10)
    end = result["cs_low_ns"]
    axis.axvline(0, color="#173f5f", linewidth=1)
    axis.axvline(end, color="#173f5f", linewidth=1)
    axis.text(0, -1.15, "CS assert", ha="center", fontsize=10)
    axis.text(end, -1.15, f"CS release / DONE\n{end:g} ns", ha="center", fontsize=10)
    last_fall = result["fall_ns"][-1]
    axis.annotate(f"final SCLK fall\n{last_fall:g} ns", xy=(last_fall, 8),
                  xytext=(last_fall-30, 9.8), fontsize=9,
                  arrowprops=dict(arrowstyle="->", color="#4b5563"), ha="right")
    axis.set_yticks([10.35, 8.35, 6.35, 4.35, 2.35, .35], TRACKS)
    axis.set_xlabel("Time relative to CS assertion (ns)")
    axis.set_xlim(result["series"][0]["xValues"][0], result["series"][0]["xValues"][-1])
    axis.set_ylim(-1.7, 12.15)
    axis.set_xticks(sorted(set([0, end] + result["rise_ns"])))
    axis.grid(axis="x", color="#e5e7eb", linewidth=.5)
    for spine in ("top", "right", "left"):
        axis.spines[spine].set_visible(False)
    axis.tick_params(axis="y", length=0, pad=10)
    order = "MSB first" if result["msb_first"] else "LSB first"
    figure.suptitle(f"SPI mode 0 — actual RTL VCD | TX 0x{result['tx_hex']} / RX 0x{result['rx_hex']}",
                    fontsize=16, fontweight="bold", x=.085, ha="left")
    axis.set_title(f"H={result['half_cycles']}  |  {order}  |  eight rising + eight falling edges",
                   loc="left", fontsize=11, color="#4b5563", pad=13)
    figure.text(.085, .025,
                f"VCD frame {result['frame_index_zero_based']} • SHA-256 {result['sha256'][:16]}…\n"
                "Setup shown is the RTL interval; pad, wire and slave timing are not included.",
                fontsize=9, color="#4b5563")
    figure.subplots_adjust(left=.085, right=.98, top=.85, bottom=.19)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=180, facecolor="white")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vcd", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frame", type=int, default=3)
    parser.add_argument("--scope")
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    result = extract(args.vcd, args.frame, args.scope)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.plot:
        plot(result, args.plot)
    print(json.dumps({key: value for key, value in result.items() if key != "series"},
                     ensure_ascii=True))


if __name__ == "__main__":
    main()

