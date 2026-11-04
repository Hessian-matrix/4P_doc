# non-ROS Demo Usage

[`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo) is the public V2 non-ROS source repository, providing four-camera SC132 RTSP, four-channel mosaic RTSP, ICM-42670-P IMU, UART, and SocketCAN CAN examples.

Accepted parameters do not guarantee sustained throughput or zero loss for every path/load. Evaluate current contracts, terminal health, and actual payloads separately; old compositions do not certify IIO. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

## 1. Directory and Runtime Package

Common entries:

```text
<non-ros-demo-root>/
├── demo/                    # runtime package that can be deployed directly to X5 /root/demo
│   ├── cam_demo
│   ├── sensor_demo
│   ├── mosaic_rtsp_demo
│   ├── imu_reader_demo
│   ├── serial_port_demo
│   ├── can_demo
│   ├── start_sensor_demo.sh     # sensor_demo boot-autostart management script
│   ├── env.sh
│   ├── config/sensor_config.yaml
│   ├── bin/
│   └── lib/
├── config/sensor_config.yaml
├── include/
├── lib/
├── scripts/
└── src/
```

Deploy the full contents of `demo/`. The top-level `cam_demo`, `sensor_demo`, `mosaic_rtsp_demo`, `imu_reader_demo`, `serial_port_demo`, and `can_demo` are launcher scripts that set the required `LD_LIBRARY_PATH`; the real ELFs are under `bin/`.

## 2. Run the Combined Entry `sensor_demo`

`sensor_demo` runs simultaneously:

- Four SC132 cameras;
- PRRTSP v2 H.264/H.265 RTSP streaming;
- ICM-42670-P kernel IIO capture with startup-selectable host or tmst timestamps; both modes preserve MONOTONIC host estimates and independent RAW burst observations, with SPI/INT1 owned by the same kernel driver.

```bash
cd /root/demo
./sensor_demo
```

Common overrides:

```bash
./sensor_demo --sample-rate-hz 1600
./sensor_demo --print-rate-hz 50 --print-metrics
./sensor_demo --diagnostics
```

On exit it prints an IMU summary:

```text
SENSOR_IMU_RESULT samples=... invalid=... timestamp_duplicates=... timestamp_regressions=... set_odr_hz=... timestamp_hz=... acquisition_hz=... acquisition_valid=...
```
Camera realtime and saving/ROS2 bridges follow wall-clock steps; standalone IMU CLI statistics use native MONOTONIC. Do not mix these contracts. Inspect sequences, final IIO health, and actual payloads; assigned-timestamp frequency is not acquisition/integrity proof.

`--imu-sample-drop-policy allow-counted` is the default: invalid six-axis payloads are counted and dropped while acquisition continues; `strict` fails on invalid payloads. Inconsistent identity, scan, timing evidence, or hardware errors stop both policies. Host has no physical-error bound; tmst applies a `200µs` computational mapping-admission limit, not a physical-accuracy guarantee. `--imu-start-order camera-first|imu-first` controls startup order, default `camera-first`, without changing the timestamp contract.

(non-ros-yaml)=
## 3. YAML Configuration

`sensor_demo` reads `${DEMO_DIR:-current directory}/config/sensor_config.yaml` at startup. Command-line arguments take precedence over YAML.

Default configuration structure:

```yaml
camera_timestamp_path: observer
imu_timestamp_mode: host
camera:
  # width/height: 1280x1088 (default), 640x480, 720x480, or 1280x720, either axial orientation
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
  auto_exposure: true
  exposure_time_us: 2000
  test_exposure_midpoint: false
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 1600
  print_rate_hz: 10
  print_metrics: false
save_data:
  save: false
  format: mp4
  save_path: /root/demo/save_mp4/
  skip: false
```

Boundaries:

- Top-level `camera_timestamp_path` accepts `observer` (default) or `official`; top-level `imu_timestamp_mode` accepts `host` (default) or `tmst`. They are not fields under `camera`/`imu`. CLI `--camera-timestamp-path` and `--imu-timestamp-mode` override YAML. Stop and restart to change them; invalid values are rejected before hardware startup.

- `camera.width` / `camera.height` support `1280x1088` (default), `640x480`, `720x480`, `1280x720`, either axial orientation; other values are rejected before the camera starts.
- The full four-camera path is fixed to four channels; single-sensor diagnostics use `cam_demo --camera-id`.
- The non-ROS public frame-rate set is 25/30/40/50/60fps; default `30`, other values rejected before the camera starts.
- `camera.auto_exposure` is a boolean, default `true`: ignore the exposure duration and preserve the SDK tuning's automatic-exposure policy. Set `false` to use `camera.exposure_time_us` (default `2000`): each enabled camera enters ISP `HBN_ISP_MODE_MANUAL`, with analog, sensor digital, and ISP gains fixed to `1x` for repeatable calibration.
- `camera.exposure_time_us` must be an integer in `1..4294967295` microseconds; zero, negatives, fractions, overflow, and trailing text are rejected. Divide by `1000000` for SDK seconds; the SDK/profile limits the usable range, and configuration failure fails startup without silently reverting to auto. Settings are startup-only: stop and restart after changes, and rebuild both the application and a supporting `libsc132.so`.
- `camera.test_exposure_midpoint` defaults to `false`; set `true` and restart `sensor_demo` to use estimated exposure-midpoint image timestamps: trigger time plus half exposure duration. An explicit YAML value overrides `SC132_TEST_EXPOSURE_MIDPOINT`; older files omitting the field preserve the environment setting (off when unset). Rebuild both the application and a supporting `libsc132.so`. IMU stamps and bag record time are unchanged. Use the image `header.stamp` for ROS1 bag alignment; do not add half exposure again. Unavailable exposure stops acquisition; this is not a calibrated actual midpoint. See {ref}`Data Contracts <test-exposure-midpoint>`.
- `rtsp.codec` supports `h264` and `h265`.
- IMU native sample rates are `25/50/100/200/400/800/1600Hz`, default `800Hz`; other values are rejected, not resampled.
- `save_data.format` defaults to `mp4` and also supports `rosbag`; the save path must be an absolute path.

### Manual Exposure Example

Change these two fields in the existing `camera` section, then restart `sensor_demo`. Set `auto_exposure: true` to restore automatic exposure:

```yaml
camera:
  auto_exposure: false
  exposure_time_us: 2000
```

The library reads `SC132_AUTO_EXPOSURE=1|0` and decimal `SC132_EXPOSURE_TIME_US` at frame-set startup. Explicit or default `sensor_demo` YAML options always override inherited environment values. Manual exposure is independent of `camera.test_exposure_midpoint`: timestamp formulas and the C ABI are unchanged, without certifying applied-frame identity or a physical exposure midpoint. No board deployment or verification has been performed for this feature. See the {ref}`Manual Exposure Contract <manual-exposure>`.

### Four Timestamp Combinations

The same binary and the same kernel IIO reads/owner serve all four combinations; only the timestamp axes change. Run one command at a time and exit normally before selecting another:

```bash
./sensor_demo --camera-timestamp-path observer --imu-timestamp-mode host
./sensor_demo --camera-timestamp-path observer --imu-timestamp-mode tmst
./sensor_demo --camera-timestamp-path official --imu-timestamp-mode host
./sensor_demo --camera-timestamp-path official --imu-timestamp-mode tmst
```

For YAML use, choose one row and set the two top-level keys in `config/sensor_config.yaml`, then run `./sensor_demo` without selector overrides:

| Combination | `camera_timestamp_path` | `imu_timestamp_mode` |
|---|---|---|
| Default | `observer` | `host` |
| Observer + sensor TMST | `observer` | `tmst` |
| Official + host | `official` | `host` |
| Official + sensor TMST | `official` | `tmst` |

Camera consumers set `SC132_TIMESTAMP_PATH` explicitly before startup; direct library use defaults to observer when the variable is unset. Observer retains the `500µs` SIF capture-window admission. Official uses the same frame's RAW IRQ `timestamps − (tv − trig_tv) × 1000`, never starts the SIF observer, and reports timing validity `0` with uncertainty `UINT32_MAX` (unknown physical bound). Host preserves MONOTONIC with unknown physical error. TMST unwraps kernel-owned FIFO/UI transition evidence into bounded affine RAW sample time with a `200µs` computational admission, not physical accuracy. No mode restores FSYNC, spidev, or automatic fallback. See [Data Contracts](../development/data-contracts.md).

**Prerequisite for every pair:** a matching kernel IIO V3 capture module must already be bound. The existing V2 module is incompatible even for host; app deployment does not upgrade it. This documentation update performs no board testing or deployment and does not claim four-way target-board acceptance.

(non-ros-save)=

## 4. Saving Four-Channel Images and IMU

For the complete whole-package verification, mutually-exclusive ROS1 bag/MP4 configuration, graceful exit, result acceptance, offline conversion, and recovery flow, see [Saving Data](save-data-guide.md).

ROS bag saving is suitable for keeping JPEG image frames, camera parameters, and IMU data:

```bash
cd /root/demo
./sensor_demo --record-bag /root/save_demo/record.bag
```

MP4 saving reuses the RTSP-encoded H.264 access units and is suitable for long-term saving of four-channel video and IMU CSV:

```bash
cd /root/demo
./sensor_demo --record-mp4-dir /root/save_demo/mp4_session
```

MP4 mode requires `rtsp.codec: h264`, the full four-channel camera mask `0x0f`, and must not enable `--record-bag` or `record-frame-skip` at the same time. The configured final output directory must not end with `.partial`; if the target directory or a same-named `.partial` already exists, the program automatically writes to the sibling `<dirname>-YYYYMMDDTHHMMSSZ[-NNNN]`, and the exit summary `SENSOR_MP4_RESULT path=` gives the real directory.

Current MP4 sessions contain `camera0.mp4` through `camera3.mp4`, four `cameraN_timestamps.csv`, extended `imu.csv`, `exposure.jsonl`, `camera_params.yaml`, `session_status.json`, and `publication_receipt.json`, without an FSYNC sidecar. Image CSV uses microsecond-quantized realtime group times; exposure sidecars retain per-camera input observations. IMU CSV `sample_realtime_ns` comes from the output bridge and retains MONOTONIC, RAW, burst/sequence/generation, origin, and bridge bases/half-width. See [Data Contracts](../development/data-contracts.md). `.partial` is recovery only.

To convert to a JPEG dataset offline, use the scripts in the public demo repository on the host:

```bash
python3 scripts/rosbag_extract.py /root/save_demo/record.bag /data/record_dataset
python3 scripts/mp4_extract.py /root/save_demo/mp4_session /data/mp4_dataset
```

| `imu.sample_rate_hz` | `800` | `25/50/100/200/400/800/1600`; old values rejected. |

## 5. Run Camera RTSP Alone

```bash
cd /root/demo
pgrep -a cam-service
./cam_demo
```

Default behavior: four channels, `1280x1088`, `30fps`, H.264, RTSP path `/PRR`.

Common parameters:

```text
--fps <25|30|40|50|60>
--codec <h264|h265>
--rotate <0|90|180|270>
--bps <kbps>
--url <path>
--trigger-mode vin_lpwm
--camera-timestamp-path <observer|official>
--diagnostics
--max-skew-ns <ns>
--frame-timeout-ms <ms>
```

Trigger mode status:

| Mode | Current status |
|---|---|
| `vin_lpwm` | The only supported mode, VIN LPWM hardware triggering; other values are rejected. |

Limits: `--width/--height` accepts `1280x1088` (default), `640x480`, `720x480`, `1280x720`, either axial orientation; other combinations are rejected; scaling is performed by `libsc132` VSE hardware full-frame stretch and does not change the FOV. `--rotate 180` supports only `30fps`, not `25fps`, `40fps`, `50fps`, or `60fps`. The external NV12/RTSP canvas keeps width/height unchanged under rotation `0/180` (e.g. `1280x1088`, `640x480`) and swaps them under `90/270` (e.g. `1088x1280`, `480x640`). Camera, RTSP, ROS1 bag, and H.264 MP4 share the same `25/30/40/50/60fps` public frame-rate set.

Default four-channel RTSP:

```text
CAM1 / cam0 -> rtsp://192.168.1.12:554/PRR
CAM2 / cam1 -> rtsp://192.168.1.12:555/PRR
CAM3 / cam2 -> rtsp://192.168.1.12:556/PRR
CAM4 / cam3 -> rtsp://192.168.1.12:557/PRR
```

CAM1/CAM2/CAM3/CAM4 are the physical silkscreen labels on the board, and cam0/cam1/cam2/cam3 are the software camera IDs.
The above uses the factory default IP; replace the address in the URLs when the board address has been changed.

Single-sensor diagnostics:

```bash
./cam_demo --camera-id 0 --diagnostics
./cam_demo --camera-id 1 --diagnostics
./cam_demo --camera-id 2 --diagnostics
./cam_demo --camera-id 3 --diagnostics
```

Run only one `cam_demo` at a time. This mode is for isolating a single sensor, FPC, power, I2C, and MIPI/VIN link; it does not represent a 2- or 3-channel combination capability.

`cam-service` is a dependency of camera operation; keep it running. Before switching between `sensor_demo`, `cam_demo`, or a custom camera application, exit the old camera application normally to avoid camera/VIO/encoding resource conflicts.

(non-ros-mosaic)=

## 6. Four-Channel Mosaic RTSP (mosaic_rtsp_demo)

`mosaic_rtsp_demo` composites four SC132 `1280x1088` NV12 frame-sets in CPU into one `2560x2176` hbmem NV12 DMA output buffer and outputs fixed H.264 RTSP through `libprrtsp.so`'s external-NV12 input, avoiding a full-frame copy by PRRTSP.

```bash
cd /root/demo
./mosaic_rtsp_demo
./mosaic_rtsp_demo --fps 40
./mosaic_rtsp_demo --fps 50
```

Fixed RTSP address:

```text
rtsp://<x5-ip>:558/PRR
```

This program is a fixed form and does not provide camera-resolution, bitrate, codec, or RTSP port/path configuration:

- Fixed four channels, H.264, 8000kbps, upright orientation, output `2560x2176`, RTSP port `558`, path `/PRR`.
- `--fps` supports `25|30|40|50|60`, default `30`.

On exit it prints run statistics:

```text
queue_full_drop=... invalid_group=... copy_failure=... send_failure=...
retain_release_balance=... copy_duration_avg_ms=... send_duration_avg_ms=...
```

- `retain_release_balance=0` means all cross-thread retained SC132 frames were returned, with no frame leak.
- `queue_full_drop`, `invalid_group`, `copy_failure`, `send_failure` equal to `0` means no queue drops, no invalid frame groups, and no compositing or send failures during the run.
- `copy_duration_avg_ms`, `send_duration_avg_ms` are the per-frame average times for compositing and RTSP sending, used to judge headroom at a given fps.

Like `cam_demo`/`sensor_demo`, `mosaic_rtsp_demo` exclusively holds the four-camera resources; exit other camera applications before running it and keep `cam-service` running.

## 7. Run IMU Alone


```bash
cd /root/demo
./imu_reader_demo
./imu_reader_demo --sample-rate-hz 1600 --count 10000
./imu_reader_demo --imu-timestamp-mode tmst --print-metrics
```

It prints sampled records at `10Hz` by default; the program still consumes all IMU samples. To view metrics use:

```bash
./imu_reader_demo --print-metrics
```

Key fields:

- `sample_monotonic_ns`: kernel-assigned MONOTONIC host estimate, retained without Unix conversion by standalone CLI; `sample_seq` is the sequence. `TIME_BASE domain=monotonic` declares the native clock.
- `timestamp_mode`, `fifo_tmst`, `sample_raw_ns`, `timestamp_uncertainty_ns`: mode and raw FIFO low16; host leaves RAW sample zero and uncertainty `UINT32_MAX`, tmst adds mapped RAW sample and computational uncertainty without replacing MONOTONIC. Standalone output never converts either mode to Unix time.
- `accel_mps2`: acceleration in `m/s^2`.
- `gyro_rps`: angular velocity in `rad/s`.
- `--print-metrics` adds generation, evidence, source, packet/burst flags, MONOTONIC observation, independent RAW burst completion, estimated period, and same-domain MONOTONIC differences. Never directly subtract RAW and MONOTONIC.

V2 `accel_mps2` outputs `[X, Y, Z]`; PCB orientation and signs still need six-face/rotation board verification. Axis signs and transforms relative to the main board or cameras are not currently declared.

The library/standalone default is800Hz; checked-in YAML explicitly selects1600Hz. CLI overrides YAML, while a generated default config uses800Hz. Distinguish supported rates, library defaults, and active settings.

The kernel IIO V3 driver owns IMU SPI/INT1; the older V2 module is incompatible. Discover the unique `icm42670-capture` instance and validate its control node without fixed device numbers. Buffer defaults to4096, API accepts powers of two in256..8192; watermark1 and seven native ODRs. Both modes use this same capture path, without userspace SPI/spidev, FSYNC, or automatic fallback.


Realtime scheduling requires camera `observer` `SCHED_FIFO/60` (not started in `official`), IMU owner `SCHED_FIFO/20`, and consumers `SCHED_RR/3`. Failure rejects startup without automatic IRQ/debug/realtime-quota changes. The observer window remains `500µs`; official has unknown physical error. Neither IMU mode guarantees physical accuracy or zero loss.

## 8. Serial Demo


UART1/UART7 use `3.3V` logic at `/dev/ttyS1` and `/dev/ttyS7`; DEBUG_UART uses `1.8V` and is not for `serial_port_demo`. V2 CN2/CN3 have 5 pins; the separate CN3 IO defaults to PPS input without switching UART7 RX/TX. Complete pin order, power-pin ratings, and hot-plug conditions still await official V2 hardware confirmation. Wire with power off by default, leave adapter VCC disconnected, and prevent reverse feed. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart).

```bash
cd /root/demo
./serial_port_demo
```

The default configuration is `/dev/ttyS1`, `115200`, `txrx`. Common examples:

```bash
./serial_port_demo --port /dev/ttyS1 --mode tx --baud 115200 --text "hello-x5"
./serial_port_demo --port /dev/ttyS7 --mode rx --baud 115200
./serial_port_demo --port /dev/ttyS1 --mode txrx --baud 115200 --count 10 --text "ping"
./serial_port_demo --port /dev/ttyS7 --mode echo --baud 115200
```

The UART signal-exit fix covers RX waits only: `SIGINT`/`SIGTERM` exits normally and restores serial settings, other signals do not extend the RX deadline, and genuine I/O errors remain failures. This does not establish every UART mode or hardware reliability.

## 9. Verification Suggestions


- Camera: use `ffprobe` or a player to pull the four RTSP streams, and confirm codec, resolution, and frame rate.
- IMU: observe `SENSOR_IMU_RESULT` and `timestamp_duplicates` / `timestamp_regressions`.
- Dynamic libraries: always deploy as a whole package; avoid mixing same-named `.so` from other projects or system directories.
- Process occupancy: do not run multiple camera applications at the same time; exit the previous process before switching modes.

(non-ros-autostart)=

## 10. Boot Autostart

`sensor_demo` boot autostart is managed by the top-level runtime-package script `start_sensor_demo.sh`:

```bash
cd /root/demo
./start_sensor_demo.sh            # start sensor_demo in foreground (equivalent to ./sensor_demo)
./start_sensor_demo.sh enable     # install boot autostart (requires root)
./start_sensor_demo.sh disable    # cancel boot autostart (requires root)
./start_sensor_demo.sh status     # view autostart and running status
```

Boot autostart is implemented through the on-device `/userdata/startup.sh`: the system `S99auto_startup` executes this file after `/userdata` is mounted. The script only appends/removes its own block marked with `SENSOR_DEMO_AUTOSTART_MANAGED` and does not overwrite other applications' content; when canceling autostart, if only comment/blank-line residue remains in the file, it is removed entirely. The image-provided `wifi_setup` uses a separate boot entry, not this file. Boot autostart uses the runtime package's default configuration; edit `config/sensor_config.yaml` directly to adjust it without re-running `enable`. `enable`/`disable` require root privileges.

(non-ros-can)=

## 11. CAN Demo

`can_demo` uses Linux SocketCAN `CAN_RAW` on network devices registered by the TCAN4550 driver. Classical CAN is the default (`0..8` payload bytes); `--fd` explicitly enables CAN FD transmission (up to `64` bytes) or mixed classical/FD reception. Both formats support 11-bit standard and 29-bit extended IDs. Classical CAN can receive remote frames; FD has no remote frames. Error-frame subscriptions and automatic replies are not supported. The program does not directly access SPI or change device tree, GPIO, bitrate, or interface state, and does not depend on camera/IMU runtime libraries or `cam-service`.

### Prerequisites and Interface Setup

- The BSP must enable CAN, CAN_RAW, and M_CAN/TCAN4550 drivers, with correct SPI, IRQ, clock, power, and pinmux configuration. If `can0` is absent, fix the BSP; the application does not create it.
- With power off, connect CAN_H, CAN_L, and reference ground according to official V2 labels, not UART/TTL wiring. Use appropriate `120Ω` termination at both bus ends after checking existing terminators. Do not guess connector pin order or onboard termination state.
- The peer must use the same bitrate and be able to receive/ACK. `500000` below is an example, not a fixed board default. Use the interface name actually enumerated on your system.

The following commands require root or network-management privileges and interrupt that CAN interface. First ensure no other CAN application or control workload uses it, then execute manually:

```bash
ip -details -statistics link show can0
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 fd off
ip link set dev can0 up
ip -details -statistics link show can0
```

For CAN FD, both nodes must support FD and match arbitration/data bitrates and ISO/non-ISO mode. The `500000` / `2000000` values below are examples only. After ensuring no other workload uses the interface, configure FD manually before running the demo with `--fd`:

```bash
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 dbitrate 2000000 fd on
ip link set dev can0 up
ip -details -statistics link show can0
```

An FD interface must have MTU `72`. `--fd` fails on a classical interface with MTU `16` rather than reconfiguring it. `--brs` selects whether transmitted frames switch bitrate in the data phase; the peer must accept that frame format. The default classical mode also works on an FD interface but does not receive FD frames.

If CAN parameters are unsupported, install CAN-capable iproute2. For probe failures, absent interfaces, or BUS-OFF, check the BSP, wiring, terminators, peer, and bitrate first; do not stop or reconfigure `cam-service`. The program explicitly fails on absent, non-CAN, or non-UP interfaces.

### Receive and Transmit Examples

Receive in terminal A; wait indefinitely by default, and use Ctrl-C for normal shutdown:

```bash
cd /root/demo
./can_demo --interface can0 --mode rx
# Receive 10 frames, with a 5-second idle timeout for each wait.
./can_demo --interface can0 --mode rx --count 10 --timeout-ms 5000
```

Transmit examples (prepare the external receiver first):

```bash
cd /root/demo
./can_demo --interface can0 --mode tx --id 123 --data 0102030405060708 --count 10 --interval-ms 100
./can_demo --interface can0 --mode tx --extended --id 1ABCDE --data AABB
./can_demo --interface can0 --mode tx --id 123 --data ''
```

CAN FD examples (configure the FD interface and prepare the external receiver first):

```bash
# Receive mixed classical data/remote and FD data frames, not FD-only filtering.
./can_demo --interface can0 --mode rx --fd --count 10 --timeout-ms 5000
# 12-byte FD without a data-phase bit-rate switch.
./can_demo --interface can0 --mode tx --fd --id 123 --data 000102030405060708090A0B
# 16-byte extended-ID FD with BRS.
./can_demo --interface can0 --mode tx --fd --brs --extended --id 1ABCDE --data 000102030405060708090A0B0C0D0E0F
```

| Option | Meaning |
|---|---|
| `--interface <name>` | Default `can0`; operates only on an existing, UP CAN device |
| `--mode <rx\|tx>` | Default `rx`; no transmission by default |
| `--id <hex>` | TX ID, default `123`; optional `0x`, standard range `0..7FF`, extended range `0..1FFFFFFF` |
| `--extended` | Explicitly select the TX 29-bit format; numeric ID size does not select it automatically |
| `--fd` | TX uses FD frames; RX accepts mixed classical/FD frames; requires an FD-enabled interface with MTU `72` |
| `--brs` | TX data-phase bit-rate switch; requires both `--mode tx --fd`; not an RX filter |
| `--data <hexbytes>` | TX default `0102030405060708`; classical `0..8` bytes; FD accepts `0..8,12,16,20,24,32,48,64` bytes, rejecting other lengths without implicit padding; even hex-digit count without separators; empty string means zero payload |
| `--count <n>` | RX default `0` (continuous), TX default `1`; explicit `0` runs until Ctrl-C |
| `--interval-ms <n>` | TX inter-frame wait, default `1000`, range `1..3600000` ms; not a realtime-period guarantee |
| `--timeout-ms <n>` | RX idle timeout per wait, default `0` (infinite), range `0..3600000` ms; not a whole-session timeout |
| `--help` / `--version` | Use alone; no CAN hardware access |

TX-only options require `--mode tx`; `--fd` applies to TX or RX, and `--brs` also requires `--fd`. Invalid arguments exit `2`; interface/I/O/receive-timeout failures exit `1`; count completion or normal SIGINT/SIGTERM interruption exits `0`. Classical output is unchanged: `rx 123#0102030405060708`, 8-digit extended IDs, or remote frames such as `rx 123#R8`. FD output is `ID##<flags><data>`, with a single hex digit for flags: bit 0 is BRS and bit 1 is ESI. For example, `rx 123##1000102030405060708090A0B` is a 12-byte FD frame with BRS set. ESI is reported by the transmitting controller; the demo has no ESI-setting option. `--extended` changes only the ID format, not FD mode.

### Verification and Limits

`tx_queued=N` means only that the kernel accepted N frames, not that the peer received them or each transmission completed on the bus. Default SocketCAN local loopback may let another receiver on the same host see transmitted frames; this does not prove external wiring, transceiver, or ACK operation. External acceptance requires a second physical node to verify ID, format, payload, and count, then reverse transmission to verify reception on this board. Also inspect errors, drops, and BUS-OFF with `ip -details -statistics link show can0`. Host datagram logic tests, vcan, and `--help` do not replace this step.

Application FD support is not board-level BSP integrity or sustained-throughput acceptance. Long FD payloads may be corrupted on affected BSPs; complete frame counts, no bus errors, or passing short frames do not establish reliability. Use the matching repaired BSP first, then verify long payloads byte-for-byte, FD/BRS flags, and bidirectional counts at a second physical node. Combined-load, latency, and error recovery are not fully closed; no throughput is promised for the current system composition. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

Use `scripts/build_can_demo.sh` for a standalone build and `scripts/package_runtime.sh` for a full package; see [Building the Public Demo Source](../development/open-source-build.md).
