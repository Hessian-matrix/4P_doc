# PPS Sync

## Independent V2 PPS Input

The V2 UART7 connector has 5 pins, including an independent PPS input IO. The factory system configures this IO as a PPS input by default. No UART7 RX/TX mux switch, serial-driver unbind, legacy module, or startup hook is required. UART7 serial operation and the independent PPS input do not share a pin.

```{warning}
The V1 UART7-to-PPS switching procedure does not apply to V2. Do not run the old pin-switching tool or wire by V1 GPIO numbers, `/dev/pps2`, or 4-pin photographs. Product and interface visuals must be replaced with actual V2 material before release. Identify the independent PPS IO from the official 5-pin labeling; do not guess a pin number.
```

Serial logic levels are unchanged: UART1/UART7 use `3.3V`; DEBUG_UART uses `1.8V`. See [Hardware and Safety](../getting-started/hardware-and-safety.md) for PPS wiring, level conversion, and common ground. Never apply 5V TTL or RS-232 levels.

## Check Input Events

Identify the PPS provider registered by the installed image rather than assuming a device number:

```bash
for p in /sys/class/pps/pps*; do
  [ -d "$p" ] || continue
  printf '%s: ' "$p"
  cat "$p/name"
  cat "$p/path"
done
```

After confirming the provider corresponds to the external independent PPS IO, observe its device node (`N` below must be replaced with the confirmed number):

```bash
ppstest /dev/ppsN
```

With a known 1Hz source connected, assert sequences should advance continuously at approximately one-second intervals and stop when disconnected. A device node or a periodically advancing virtual provider alone does not prove reception of external pulses. If the expected provider is missing, check the matching V2 image and wiring and contact support; do not revert to V1 UART mux switching.

## Synchronization Boundary

PPS provides edge events, not a date or second number, and does not automatically discipline the system clock. See [Time Synchronization](system-time-sync.md) for NTP/PPS/PTP combinations. The shared camera/IMU LPWM trigger net and this external 1Hz PPS input have separate contracts; successful PPS reception does not prove camera/IMU sample alignment.
