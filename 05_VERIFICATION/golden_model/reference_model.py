"""Mathematical event oracle for one 8-bit SPI mode-0 frame.

This model describes the interface contract, not the DUT's FSM. Running its
self-check alone does not verify RTL. Compare the generated events with actual
RTL/VCD observations to obtain DUT evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _integer(name: str, value: int, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        limit = f"{minimum}..{maximum}" if maximum is not None else f">={minimum}"
        raise ValueError(f"{name} must be {limit}")
    return value


def serial_bits(byte: int, msb_first: bool = True) -> list[int]:
    """Return the eight pin values in wire order; reject out-of-range bytes."""
    _integer("byte", byte, 0, 255)
    if msb_first not in (False, True, 0, 1):
        raise ValueError("msb_first must be 0 or 1")
    positions = range(7, -1, -1) if msb_first else range(8)
    return [(byte // (2 ** position)) % 2 for position in positions]


def decode_bits(bits: list[int], msb_first: bool = True) -> int:
    """Assemble exactly eight observed pin samples into a normal byte."""
    if len(bits) != 8 or any(bit not in (0, 1) for bit in bits):
        raise ValueError("exactly eight binary samples are required")
    if msb_first not in (False, True, 0, 1):
        raise ValueError("msb_first must be 0 or 1")
    text = "".join(str(int(bit)) for bit in bits)
    return int(text if msb_first else text[::-1], 2)


def expected_frame(
    tx: int = 0x96,
    rx: int = 0xC3,
    half_cycles: int = 4,
    msb_first: bool = True,
    clock_period_ns: float = 10.0,
    previous_rx: int = 0,
) -> dict:
    """Predict pin-level snapshots at acceptance, every edge, DONE and clear.

    cycle=0 is the accepting rising clk edge, after registered outputs settle.
    MISO is a compliant ideal slave: bit 0 is preloaded at CS assertion, and
    subsequent bits change on SCLK falling edges. The final falling edge does
    not advance beyond the eighth bit. rx_data holds previous_rx until DONE.
    """
    _integer("half_cycles", half_cycles, 1)
    _integer("previous_rx", previous_rx, 0, 255)
    if clock_period_ns <= 0:
        raise ValueError("clock_period_ns must be positive")
    tx_bits, rx_bits = serial_bits(tx, msb_first), serial_bits(rx, msb_first)
    state = dict(cs_n=0, sclk=0, mosi=tx_bits[0], miso=rx_bits[0],
                 busy=1, done=0, rx_data=previous_rx)
    events = []

    def record(kind: str, cycle: int, bit_index: int | None = None,
               sampled_miso: int | None = None) -> None:
        events.append(dict(kind=kind, cycle=cycle,
                           time_ns=cycle * clock_period_ns,
                           bit_index=bit_index, sampled_miso=sampled_miso, **state))

    record("accept", 0)
    for bit_index in range(8):
        state["sclk"] = 1
        record("rise", (2 * bit_index + 1) * half_cycles,
               bit_index, rx_bits[bit_index])
        state["sclk"] = 0
        if bit_index < 7:
            state["mosi"] = tx_bits[bit_index + 1]
            state["miso"] = rx_bits[bit_index + 1]
        record("fall", (2 * bit_index + 2) * half_cycles, bit_index)
    state.update(cs_n=1, busy=0, done=1, rx_data=decode_bits(rx_bits, msb_first))
    record("done", 16 * half_cycles + 1)
    state["done"] = 0
    record("idle", 16 * half_cycles + 2)
    return dict(
        model="ideal_pin_event_oracle",
        scope="One completed frame; this model alone does not test RTL",
        tx_hex=f"{tx:02X}", rx_hex=f"{rx:02X}", previous_rx_hex=f"{previous_rx:02X}",
        half_cycles=half_cycles, msb_first=int(bool(msb_first)),
        clock_period_ns=clock_period_ns, tx_bits=tx_bits, rx_bits=rx_bits,
        nominal_setup_ns=half_cycles * clock_period_ns,
        done_cycle=16 * half_cycles + 1, events=events,
    )


def self_check() -> dict:
    """Check interface properties and all byte encodings against string oracles."""
    frames = 0
    for order in (False, True):
        for byte in range(256):
            oracle = [int(bit) for bit in f"{byte:08b}"]
            if not order:
                oracle.reverse()
            if serial_bits(byte, order) != oracle:
                raise AssertionError("wire ordering differs from byte string oracle")
            if decode_bits(oracle, order) != byte:
                raise AssertionError("sample decoding differs from expected byte")
            # Odd multiplier is a byte permutation: every RX value appears once,
            # independently from its paired TX value.
            rx = (73 * byte + 41) % 256
            for h in (1, 2, 3, 4, 5, 8):
                frame = expected_frame(byte, rx, h, order, previous_rx=0x5A)
                rises = [event for event in frame["events"] if event["kind"] == "rise"]
                falls = [event for event in frame["events"] if event["kind"] == "fall"]
                if len(rises) != 8 or len(falls) != 8:
                    raise AssertionError("a frame needs eight full SCLK pulses")
                if [event["mosi"] for event in rises] != oracle:
                    raise AssertionError("sampled MOSI differs from TX ordering oracle")
                rx_oracle = [int(bit) for bit in f"{rx:08b}"]
                if not order:
                    rx_oracle.reverse()
                if [event["sampled_miso"] for event in rises] != rx_oracle:
                    raise AssertionError("MISO samples differ from independent RX oracle")
                edge_cycles = [event["cycle"] for event in frame["events"]
                               if event["kind"] in ("rise", "fall")]
                if any(b - a != h for a, b in zip(edge_cycles, edge_cycles[1:])):
                    raise AssertionError("SCLK half-period changed")
                if frame["events"][0]["cycle"] >= rises[0]["cycle"]:
                    raise AssertionError("CS assertion must precede first sample")
                done = next(e for e in frame["events"] if e["kind"] == "done")
                if not falls[-1]["cs_n"] == 0 or not done["cycle"] > falls[-1]["cycle"]:
                    raise AssertionError("CS must include the final falling edge")
                if any(e["rx_data"] != 0x5A for e in frame["events"][:-2]):
                    raise AssertionError("RX result changed before DONE")
                if done["rx_data"] != rx or not done["done"] or done["busy"]:
                    raise AssertionError("completion handshake or RX differs")
                if frame["events"][-1]["done"]:
                    raise AssertionError("DONE pulse did not clear")
                frames += 1
    rejected = 0
    for bad in (0, -1, -32, 1.5, True):
        try:
            expected_frame(half_cycles=bad)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(f"invalid H accepted: {bad!r}")
    return dict(status="PASS", byte_values=256, bit_orders=2,
                half_cycle_values=[1, 2, 3, 4, 5, 8],
                model_frames_checked=frames, invalid_h_rejected=rejected,
                verifies_rtl=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tx", type=lambda value: int(value, 0), default=0x96)
    parser.add_argument("--rx", type=lambda value: int(value, 0), default=0xC3)
    parser.add_argument("--half-cycles", type=int, default=4)
    parser.add_argument("--order", choices=(0, 1), type=int, default=1)
    parser.add_argument("--clock-period-ns", type=float, default=10.0)
    parser.add_argument("--previous-rx", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--json", type=Path, help="Write oracle metadata and events as JSON")
    parser.add_argument("--csv", type=Path, help="Write oracle event table as CSV")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    try:
        frame = expected_frame(args.tx, args.rx, args.half_cycles, bool(args.order),
                               args.clock_period_ns, args.previous_rx)
    except ValueError as error:
        parser.error(str(error))
    if args.self_check:
        frame["model_self_check"] = self_check()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(frame, indent=2), encoding="utf-8")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(frame["events"][0]))
            writer.writeheader()
            writer.writerows(frame["events"])
    if args.json or args.csv:
        print(json.dumps({key: value for key, value in frame.items() if key != "events"}))
    else:
        print(json.dumps(frame, indent=2))


if __name__ == "__main__":
    main()

