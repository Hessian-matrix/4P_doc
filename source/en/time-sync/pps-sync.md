# PPS Sync

## Independent V2 PPS Input

On UART7 connector CN2 (GH1.25 5-pin), **pin 4 is PPS input and pin 5 is GND**; see the {ref}`Interface Wiring Diagram <wiring-diagram>`. The factory system configures PPS input by default.

```{warning}
PPS uses **3.3V logic** and requires common ground. Translate 1.8V, 5V TTL, or RS-232 outputs with a suitable level converter before connecting them. 3.3V is the nominal logic level, not an overvoltage allowance or 5V tolerance.

Disable or isolate the source output and external pull-up before wiring with power off; enable PPS only after board power is stable. Prevent back-feed while the board is unpowered or asleep. Stopping pulses while holding a high level is not isolation. Pin numbers do not indicate left-to-right order in a mating-face view: check the diagram and physical labels.
```

## Usage Example: Receive External 1 Hz PPS

This example checks that external pulses reach Linux PPS. It does not change the system clock or configure camera/IMU triggers.

### 1. Wiring and Preparation

1. Prepare an external device with a 1 Hz PPS output, such as a GNSS receiver or signal generator. Confirm compatibility with the 3.3V logic input above, using level conversion first if needed.
2. First disable or isolate the source output and external pull-up, then wire with power off: connect PPS output to pin 4 of UART7 connector CN2, and common GND to pin 5. Do not connect unconfirmed power pins.
3. Once board power is stable, enable the source's 1 Hz output and log into the X5 as `root`. Check whether the image provides `ppstest`:

```bash
command -v ppstest
```

If the command is missing, obtain a matching system image with `pps-tools` or contact product support. Do not substitute a virtual PPS provider for the external input.

### 2. Identify the PPS Device

Enumerate the providers registered by the installed image rather than assuming a device number:

```bash
for p in /sys/class/pps/pps*; do
  [ -d "$p" ] || continue
  printf '%s: ' "$p"
  cat "$p/name"
  cat "$p/path"
done
```

Use `name`, `path`, and the matching image's hardware documentation to identify the provider for the external independent PPS IO. `path` may be empty; a number or `pps` in a name is not sufficient identification. If the provider is missing or its mapping is unclear, contact product support.

### 3. Observe Input Events

Replace `N` below with the number confirmed in the previous step, then run:

```bash
PPS_DEV=/dev/ppsN
ppstest "$PPS_DEV"
```

The following output-format example is quoted from the [official LinuxPPS documentation](https://docs.kernel.org/driver-api/pps.html) for field interpretation, not a measurement from this product. Actual timestamps and sequences will differ:

```text
source 0 - assert 1186592699.388832443, sequence: 364 - clear  0.000000000, sequence: 0
source 0 - assert 1186592700.388931295, sequence: 365 - clear  0.000000000, sequence: 0
source 0 - assert 1186592701.389032765, sequence: 366 - clear  0.000000000, sequence: 0
```

- `source 0` is the first input passed to `ppstest`; it does not imply `/dev/pps0`.
- `assert` is the captured event timestamp in seconds.nanoseconds. The number of decimal places does not establish UTC synchronization accuracy.
- With a known 1 Hz input, assert sequences should keep advancing, and successive event timestamps should be approximately one second apart while the system clock is stable. The sequence need not start at 1.
- For a provider capturing only assert events, the `clear` timestamp and sequence may stay at 0; this alone does not indicate missing input.

Leave wiring unchanged and stop PPS output at the signal source. Assert sequences should stop advancing, and `ppstest` may report a wait timeout; they should resume when output resumes. A device node, repeated copies of the same timestamp, or a periodically advancing virtual provider alone does not prove external pulse reception. Power off before changing wiring.

Press `Ctrl+C` to exit `ppstest`. Exiting stops observation, not the PPS input configuration. For persistent missing events or wait timeouts, check the selected provider, source enable state, voltage compatibility, common ground, and official PPS wiring labels.

## Synchronization Boundary

PPS provides edge events, not a date or second number, and does not automatically discipline the system clock. See [Time Synchronization](system-time-sync.md) for NTP/PPS/PTP combinations. The shared camera/IMU LPWM trigger net and this external 1Hz PPS input have separate contracts; successful PPS reception does not prove camera/IMU sample alignment.
