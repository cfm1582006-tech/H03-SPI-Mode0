# Physical implementation and timing assumptions

`config_core.json` hardens `h03_spi_master` with `HALF_CYCLES=4` and
`MSB_FIRST=1`. `config_wrapper.json` hardens `tt_um_h03_spi_mode0`, including
the core and the wrapper RTL. These are separate experiments; metrics and
artifacts must retain their top-module and run labels.

The configurations target the LibreLane Classic flow with sky130A and
`sky130_fd_sc_hd`. CTS, routing, multi-corner STA, SPEF extraction, Magic DRC,
KLayout DRC, LVS and Magic/KLayout streamout comparison remain enabled. Timing
violation checks cover all available process/voltage/temperature and RC corners,
not only the typical corner. A nonzero tool exit or violation is a failure.
The full-flow runner requires EQY formal equivalence between the RTL and the
mapped final netlist using scripts/run_equivalence.py and processed sky130A
models. The built-in LibreLane EQY step is disabled because its generic script
fails on this design; the separate proof remains mandatory for pipeline PASS.

## Reproduce with an existing PDK

From the project root, inside the installed LibreLane development environment:

```bash
python3 scripts/run_full_flow.py --pdk-root "$PDK_ROOT" \
  --tag my_new_run --jobs 4 --tops both --out evidence/my_new_run
```

The portable standard-library runner first executes the RTL regression with
mutation checks and the wrapper regression when its runner is available, then
runs the selected core/wrapper physical configurations sequentially. It refuses
nonempty output directories and existing physical run tags. It records exact
commands, exits, tool versions, input hashes/snapshots, final metric hashes and
artifact hashes. Missing required metrics fail the check; the presence of a GDS
file alone never produces a PASS.

Use `--tops core` or `--tops wrapper` to select one physical top. Standalone
physical invocations, useful while debugging a failed stage, are:

```bash
librelane --manual-pdk --pdk-root "$PDK_ROOT" --jobs 4 --condensed \
  --run-tag my_new_core flow/config_core.json
librelane --manual-pdk --pdk-root "$PDK_ROOT" --jobs 4 --condensed \
  --run-tag my_new_wrapper flow/config_wrapper.json
```

`PDK_ROOT` is the directory containing `sky130A`, not `sky130A` itself. The
local PDK used for this work has Ciel revision
`8afc8346a57fe1ab7934ba5a6056ea8b43078e71`. Record the actual LibreLane and
tool versions from each run. The archived input runs used LibreLane 3.0.14;
reruns use the available 3.0.16 environment. Their values need not match.

The relative paths use the configuration directory (`flow`) as their base.
LibreLane stores the run under that design directory unless a run directory
is explicitly supplied. Capture its actual run path rather than selecting an
unrelated newest run from another directory.

## Declared timing and electrical envelope

| Item | Value |
|---|---:|
| System clock period | 10 ns (100 MHz analysis target) |
| Clock uncertainty | 0.25 ns |
| Ideal clock transition before CTS | 0.15 ns |
| Input delay relative to system clock | min 0.20 ns, max 1.00 ns |
| Input transition | 0.15 ns |
| Output delay relative to system clock | min 0.20 ns, max 1.00 ns |
| Per-output capacitive load | 0.033442 pF = 33.442 fF |
| Maximum transition target | 0.75 ns |

All constraints are block-level assumptions. They are not derived from a
specified board or slave IC. The capacitance matches the sky130 HD default
`OUTPUT_CAP_LOAD` value of 33.442 fF, while the custom SDC writes the same
quantity in the Liberty capacitance unit pF. The input slew and uncertainty
are explicit engineering assumptions. The min/max values avoid silently
using one delay for both setup and hold. Synchronous `rst_n` is timed; no reset
false path is introduced. There are no multicycle exceptions or waived paths.

The historical SDC used 1 ns for both minimum and maximum I/O delay and did not
declare slew, load, or uncertainty. New results are therefore a fresh analysis
under a stronger and different envelope, not an apples-to-apples PPA reduction.

## Repairing the first fresh run

The first fresh `core_20261025` iteration completed layout and reported clean
DRC, LVS, antenna and setup/hold counts, but failed the electrical slew target.
At `max_ss_100C_1v60`, 30 pins on the buffered synchronous reset distribution
net had transitions slightly over 0.750 ns. The worst reported transition was
0.751037 ns at `_170_/C`; reset input buffer `input2/X` reported 0.750653 ns.
The original run and reports are retained as a failed iteration.

The subsequent configurations retain the same I/O load, transition target,
delays and uncertainty. Placement/resizing use typical, fast/min-RC and
slow/max-RC corners explicitly, and post-global-route design/timing repair is
enabled. The max-slew and max-cap corner selectors are explicitly `*`, so
electrical violations are fatal. These changes optimize the reset distribution
instead of relaxing the target or excluding reset from analysis. The final
result remains subject to the new run logs and checks.

## SPI interface limitation

The core launches SCLK/MOSI with system-clocked registers and captures MISO at
the system clock event that commands each SCLK rising edge. SCLK is a burst
output, not an internal clock domain. With H=4, its nominal frequency is
12.5 MHz at a 100 MHz system clock. A mode-0 slave launches MISO on falling
SCLK edges, leaving roughly H system-clock cycles until the next capture.

The single-clock block SDC constrains every functional input/output relative to
`clk`; it does not prove the complete external round-trip timing between SCLK,
the slave, PCB traces, and MISO. Before hardware integration, select the slave
datasheet, include its SCLK-to-MISO delay, PCB skew, input setup/hold, MOSI and CS
requirements, and constrain the forwarded-clock interface or perform explicit
budget checks. Add host-side synchronizers if `start` or other host inputs are
asynchronous to `clk`; a synchronizer on MISO must be considered with the SPI
phase/latency and divider rather than added blindly.

The relative floorplan starts at 40% core utilization and 45% placement target
density, following a previously completed archived run. The resulting macro
does not establish a fixed Tiny Tapeout tile size, a harness-compatible pin
placement, padframe closure, or fabrication signoff. A Tiny Tapeout submission
requires its current harness/template constraints and separate integration.

## Official references

- [LibreLane configuration variables](https://librelane.readthedocs.io/en/latest/reference/common_flow_vars.html)
- [LibreLane steps, SDC paths and synthesis parameters](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html)
- [LibreLane Classic flow](https://librelane.readthedocs.io/en/latest/reference/flows.html)

Run logs and measured result summaries are authoritative for completion. This
configuration document alone makes no claim that a flow has passed.

For GitHub self-hosted CI on this machine, physical.yml calls the AppImage
explicitly. Set repository Actions variables LIBRELANE_APPIMAGE and PDK_ROOT;
registering a runner alone does not add LibreLane or EQY to the runner's PATH.

## Final closure and equivalence integration

Corner selection and post-GRT repair alone left the same 30 reset slew violations. Final configurations also enforce max fanout 8 in JSON and SDC; this changes buffering while retaining the 0.75 ns transition limit and output load. The final measured counts are recorded in docs/RESULTS.md.

The generic LibreLane 3.0.16 EQY script failed in its combine phase because unused Liberty blackboxes remained in gold. RUN_EQY is false in Classic configs; run_full_flow.py instead requires scripts/run_equivalence.py after each physical run, using that exact final netlist and formal sky130 models, with no imported gold blackbox library. An EQY PASS marker and success log are mandatory. The full runner then requires functional gate simulation. Running Classic alone does not complete this project's full pipeline.

