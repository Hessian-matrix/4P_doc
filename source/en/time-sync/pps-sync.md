# PPS Sync

The factory default does not expose the PPS interface; you need to switch the default **UART7 RX** pin to Linux PPS input. The switch tool is `x5-pps-pin.sh` in the non-ROS demo repository, with the matching kernel module `x5pps.ko`.

## 1. Files, Version, and Prerequisites

Get from the public non-ROS demo repository:

```text
scripts/env_setup/x5-pps-pin.sh
scripts/env_setup/x5pps.ko
```

Current matching module information:

| Item | Value |
|---|---|
| Module file | `x5pps.ko` |
| File size | `13160` bytes |
| SHA-256 | `50337d81b40a62c9bfb5d1b81a55b931a87138a276136f11a130b8056521797f` |
| vermagic | `6.1.83-DR-PL5.1_V1.1.2 SMP preempt mod_unload aarch64` |
| PPS input | default UART7 RX, GPIO `379`, on-board `pin10` |
| Linux PPS device | `/dev/pps2` |
| Default edge | `rising` |

`x5pps.ko` must match the device `uname -r`. The script registers the Linux PPS device with a fixed `pps_id=2`; if `/dev/pps2` is already occupied by another provider, the switch should fail — do not use `--force` to bypass a device conflict.

It is recommended to place the script and module in the `/userdata` partition that survives reboot, e.g. `/userdata/x5-pps/`. The script's persistent mode file, boot log, and disable switch are also located in the script's directory.

Upload from the host:

```bash
X5_IP=192.168.1.12  # change to the actual board address
cd /path/to/RoboBaton_4p_demo
ssh root@${X5_IP} "mkdir -p /userdata/x5-pps"
scp scripts/env_setup/x5-pps-pin.sh scripts/env_setup/x5pps.ko \
  root@${X5_IP}:/userdata/x5-pps/
ssh root@${X5_IP} "chmod 755 /userdata/x5-pps/x5-pps-pin.sh && chmod 644 /userdata/x5-pps/x5pps.ko"
```

Confirm on-device:

```bash
cd /userdata/x5-pps
uname -r
sha256sum x5pps.ko
```

## 2. Switch to PPS

First stop serial programs using UART7 and prepare a reliable SSH or other recovery entry. Then run on the X5 device:

```bash
cd /userdata/x5-pps
./x5-pps-pin.sh --check
./x5-pps-pin.sh pps
./x5-pps-pin.sh status
```

The script:

1. Checks `x5pps.ko` and kernel vermagic;
2. Checks UART7 resource and console occupancy;
3. Unbinds the UART7 platform device;
4. Switches the default UART7 RX mux to GPIO/PPS function;
5. Loads `x5pps.ko` with parameters `gpio=379 pps_id=2 edge=rising`;
6. Creates the real PPS device `/dev/pps2`;
7. Tries to save the persistent mode and maintain the `/userdata/startup.sh` boot hook.

The runtime mux/module-load and persistence are two phases. The script may have completed this run's PPS runtime switch but then failed to establish reboot persistence due to a `mode`-file or `/userdata/startup.sh` write failure. After the command, you must inspect the full output and run `status` to separately confirm the current mux/provider and the persistent mode/boot hook.

After switching, use `status` to confirm:

```text
x5pps loaded: gpio=379 ... pps_id=2 ...
pps2 name=x5pps ...
```

A virtual/pseudo PPS provider named `hobot-pps` may also exist in the system. Acceptance must confirm that `/dev/pps2` has `name` equal to `x5pps`, not just that the device node exists.

## 3. Verify PPS Input

After connecting the external PPS signal to the default UART7 RX PPS input, run:

```bash
./x5-pps-pin.sh test --secs 10
```

The script compares before/after:

- `x5pps` GPIO IRQ count;
- PPS assert count;
- `/dev/pps2` PPS sequence count.

The normal result is about 1 Hz events received within about 10 seconds. `test` passing only proves the external edge reached the current GPIO/PPS provider, not that NTP/PTP is locked, nor that camera/IMU time is synchronized.

The PPS input must meet the electrical conditions specified in the product hardware documentation. The current input domain is treated as 3.3V; a 1.8V PPS source cannot be connected directly and must use proper level shifting. The signal source and X5 must share ground.

If `test` fails, check in order:

1. The external signal is actually connected to the default UART7 RX PPS pin;
2. The mux has been switched to GPIO/PPS;
3. The signal edge matches the `rising` configuration;
4. Level, common ground, and wiring are correct;
5. The provider name of `/dev/pps2` in `status` is `x5pps`;
6. Whether the corresponding IRQ in `/proc/interrupts` is growing.

When re-running a short test after disconnecting the external PPS signal, the `x5pps` event count should stop growing; this step rules out false positives from the virtual PPS source.

## 4. Restore UART7

To restore normal UART7 function, run on-device:

```bash
cd /userdata/x5-pps
./x5-pps-pin.sh uart
./x5-pps-pin.sh status
ls -l /dev/ttyS7
```

The script unloads `x5pps`, tries to restore the UART7 RX/TX mux, and rebinds the UART7 platform device. Mux or tty warnings in the restore log cannot be treated as success; before running `serial_port_demo` again after restore, you must confirm both RX/TX mux are UART function, `/dev/ttyS7` exists, the persistent mode/boot hook are as expected, and no other program holds the resource.

Restore only this run without changing the existing reboot mode:

```bash
./x5-pps-pin.sh uart --once
```

To keep normal UART7 on every future reboot, run `uart` without `--once`.

## 5. UART7 TX as Programmable GPIO/IO

PPS mode uses UART7 RX as the `/dev/pps2` input; the script also releases the UART7 TX GPIO mux so TX can be used as ordinary GPIO/IO by later applications. In the current X5 device tree, UART7 TX corresponds to GPIO global number `380`, line offset `1` within the LSIO GPIO0 controller; the GPIO chip device number may vary with system enumeration order and cannot be assumed to be `/dev/gpiochip0`.

After switching PPS, first confirm the script status:

```bash
./x5-pps-pin.sh status
```

You should see something like:

```text
UART7 TX IO mux: GPIO380 LSIO_UART7_TX = ALT2 (pin8)
```

Then use `gpioinfo` on the target board to find the GPIO chip representing LSIO GPIO0 and confirm line offset `1` is not occupied by another consumer:

```bash
gpioinfo
```

The examples below use a variable for the confirmed chip; do not assume `gpiochip0` before confirming with `gpioinfo`:

```bash
GPIOCHIP=/dev/gpiochip0   # replace with the LSIO GPIO0 chip confirmed by gpioinfo
GPIO_LINE=1               # GPIO global 380 - GPIO0 base 379
```

### 5.1 Software 1Hz Test Pulse

Confirm `gpioset` exists:

```bash
command -v gpioset
```

Output a single high pulse of about 100 ms:

```bash
gpioset --chip "$GPIOCHIP" \
  --consumer pps-io-test \
  --hold-period 100ms \
  "$GPIO_LINE"=1
```

Loop to output an approximate 1 Hz software pulse:

```bash
while :; do
  gpioset --chip "$GPIOCHIP" \
    --consumer pps-io-test \
    --hold-period 100ms \
    "$GPIO_LINE"=1
  sleep 0.900
done
```

This example verifies the TX line's GPIO output capability and the external receiver, not a precise PPS output produced by a hardware timer/PHC/MCU. User-space process startup, scheduling, and GPIO request/release all introduce edge jitter; do not use it as an NTP/PTP reference pulse or a camera/IMU sync source.

### 5.2 Input Capture and IO State Identification

After confirming `gpiomon` exists, capture rising, falling, or both edges on the TX line:

```bash
command -v gpiomon
gpiomon --chip "$GPIOCHIP" \
  --consumer pps-io-capture \
  --edges both \
  --event-clock monotonic \
  --num-events 10 \
  "$GPIO_LINE"
```

Ordinary IO identification should also use an explicit GPIO consumer and first confirm no other program occupies that line. Input capture gives the time and edge of the Linux GPIO event, not the physical sampling time of the external signal; for stricter edge precision, add hardware capture or scope/logic-analyzer verification.

### 5.3 Ownership and Recovery

- In PPS mode, do not run `serial_port_demo` or other UART7 programs simultaneously;
- Do not let two GPIO tools request the same line at the same time;
- Whether `gpioset`/`gpiomon` hold the level after exit depends on the GPIO tool and kernel implementation; business programs must design their own safe default level;
- To restore normal UART7, run `./x5-pps-pin.sh uart`; the script restores both UART7 RX/TX mux to normal UART function;
- After restore, re-check `/dev/ttyS7` and do not leave a GPIO consumer holding the line.

## 6. Reboot Persistence

`pps`/`uart` commands without `--once` try to write the mode to the `mode` file in the script's directory and maintain a bounded-marker boot hook in `/userdata/startup.sh`. Existing `startup.sh` content is not overwritten. Only when the command reports no persistence error and `status` shows both the expected `mode` and an installed, executable boot hook can you judge subsequent reboot behavior per the table below.

| Operation | Current runtime | Subsequent reboot |
|---|---|---|
| `pps` | UART7 RX switched to PPS | Auto-switch to PPS and register `/dev/pps2` |
| `uart` | Restore normal UART7 | Keep normal UART7 |
| `pps --once` | Switch to PPS this run | Keep existing persistent mode |
| `uart --once` | Restore UART7 this run | Keep existing persistent mode |
| `uninstall` | No change to current runtime | Remove boot hook and persistent mode |

View status:

```bash
./x5-pps-pin.sh status
```

Emergency-disable the boot hook:

```bash
touch /userdata/x5-pps/DISABLE
```

Re-enable the boot hook:

```bash
rm -f /userdata/x5-pps/DISABLE
```

Remove this script's boot hook and persistent mode:

```bash
./x5-pps-pin.sh uninstall
```

`uninstall` does not change the current switched runtime state. To restore UART7 immediately, run:

```bash
./x5-pps-pin.sh uart --once
./x5-pps-pin.sh uninstall
```

## 7. `--force` and `--keep-uart`

If UART7 is occupied by the Linux console, the script refuses to unbind by default. Only when you have prepared an SSH or other recovery path and explicitly accept the risk of losing the console, consider:

```bash
./x5-pps-pin.sh pps --force
```

`--force` also bypasses the module-vermagic-mismatch refusal; it is not a solution for a kernel version mismatch. `--keep-uart` keeps the UART driver but borrows the mux, which may cause serial/console output loss or be reclaimed by the UART driver on power-management resume. Do not use it for normal switching:

```bash
./x5-pps-pin.sh pps --keep-uart
```

## 8. Common Issues

### Module Not Found or vermagic Mismatch

```bash
./x5-pps-pin.sh --check
uname -r
sha256sum /userdata/x5-pps/x5pps.ko
```

Do not use `--force` instead of a matching kernel module.

### `/dev/pps2` Missing or Wrong Name

Run:

```bash
./x5-pps-pin.sh status
cat /sys/module/x5pps/parameters/gpio
cat /sys/module/x5pps/parameters/pps_id
cat /proc/interrupts
```

Only when the sysfs `name` of `/dev/pps2` is `x5pps` can it be treated as this script's real PPS source. A periodically growing `hobot-pps` does not mean the external UART7 RX has received PPS.

### UART7 Unusable After Restore

Confirm the `uart` rebind log, mux state, and device node:

```bash
./x5-pps-pin.sh uart
./x5-pps-pin.sh status
ls -l /dev/ttyS7
```

Do not manually unbind other platform devices before confirming resource ownership.

## 9. Relationship to Other Time-Sync Methods

- **PPS**: brings an external PPS edge into Linux `/dev/pps2`; this script and `x5pps.ko` handle the mux, module, and event counting.
- **NTP**: disciplines the system time through network NTP servers; see [Time Synchronization](system-time-sync.md).
- **PTP**: establishes a time relationship with an external PTP peer through LinuxPTP/PHC; see the PTP example in the Time Synchronization chapter.
- **Camera/IMU sampling sync**: requires independent trigger, sampling identity, and timestamp contracts; passing the PPS `test` does not mean the camera/IMU are hardware-synchronized.

The current PTP master example drives the PHC from `CLOCK_REALTIME`; NTP can be the upstream of that system clock, but the current NTP script stops `phc2sys`. Before combining, re-establish and verify the PHC/PTP link per [Time Synchronization](system-time-sync.md). PPS input does not automatically replace NTP/PTP.
