# non-ROS Demo Usage

[`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo) is the public V2 non-ROS source repository, providing four-camera SC132 RTSP, four-channel mosaic RTSP, ICM-42670-P IMU, UART, and SocketCAN CAN examples. Old V1 downloads do not provide the V2 hardware/API.

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
- ICM-42670-P INT1 (`34120000.gpio` offset `8`) + sensor timestamp FIFO IMU acquisition thread.

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
SENSOR_IMU_RESULT samples=... invalid=... timestamp_duplicates=... timestamp_regressions=... effective_hz=...
```
In a window without system-clock corrections, check `timestamp_duplicates=0` and `timestamp_regressions=0`. Public realtime stamps may move backward with clock corrections; a regression across such a window alone is not a hardware-ordering failure. Also inspect sequences, timing drops, final health counters, and actual payloads.

`--imu-sample-drop-policy allow-counted` is the default: samples with provable identity but inadmissible timing are counted and dropped while acquisition continues. `strict` fails on timing/invalid-packet rejection. Unprovable identity, an invalid clock certificate, or hardware errors stop both policies. `--imu-start-order camera-first|imu-first` controls startup order, default `camera-first`, without changing timestamps or association contracts.

(non-ros-yaml)=
## 3. YAML Configuration

`sensor_demo` reads `${DEMO_DIR:-current directory}/config/sensor_config.yaml` at startup. Command-line arguments take precedence over YAML.

Default configuration structure:

```yaml
camera:
  # width/height: 1280x1088 (default), 640x480, 720x480, or 1280x720, either axial orientation
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
  test_exposure_midpoint: false
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 800
  print_rate_hz: 10
  print_metrics: false
  fsync_enabled: false
save_data:
  save: false
  format: mp4
  save_path: /root/demo/save_mp4/
  skip: false
```

Boundaries:

- `camera.width` / `camera.height` support `1280x1088` (default), `640x480`, `720x480`, `1280x720`, either axial orientation; other values are rejected before the camera starts.
- The full four-camera path is fixed to four channels; single-sensor diagnostics use `cam_demo --camera-id`.
- The non-ROS public frame-rate set is 25/30/40/50/60fps; default `30`, other values rejected before the camera starts.
- `camera.test_exposure_midpoint` defaults to `false`; set `true` and restart `sensor_demo` to use estimated exposure-midpoint image timestamps: trigger time plus half exposure duration. An explicit YAML value overrides `SC132_TEST_EXPOSURE_MIDPOINT`; older files omitting the field preserve the environment setting (off when unset). Rebuild both the application and a supporting `libsc132.so`. IMU stamps and bag record time are unchanged. Use the image `header.stamp` for ROS1 bag alignment; do not add half exposure again. Unavailable exposure stops acquisition; this is not a calibrated actual midpoint. See {ref}`Data Contracts <test-exposure-midpoint>`.
- `rtsp.codec` supports `h264` and `h265`.
- IMU native sample rates are `25/50/100/200/400/800/1600Hz`, default `800Hz`; old `500/1000/2000Hz` values are rejected, not resampled.
- `save_data.format` defaults to `mp4` and also supports `rosbag`; the save path must be an absolute path.

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

Current MP4 sessions contain `camera0.mp4` through `camera3.mp4`, four `cameraN_timestamps.csv` files, `imu.csv`, `exposure.jsonl`, `fsync.jsonl`, `camera_params.yaml`, `session_status.json`, and `publication_receipt.json`. `fsync.jsonl` is always created but receives association records only with FSYNC enabled. MP4 uses nominal H.264 frame timing; timestamp CSV stores microsecond-quantized realtime group-trigger times expressed in ns. Original per-camera values are in the input exposure sidecar and, with FSYNC enabled, association records. Exposure `status=1` is an estimate, not certified applied exposure; the input sidecar may outnumber encoded frames. See [Data Contracts](../development/data-contracts.md) for joins. `.partial` is recovery-only, not a complete data source.

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
```

It prints sampled records at `10Hz` by default; the program still consumes all IMU samples. To view metrics use:

```bash
./imu_reader_demo --print-metrics
```

Key fields:

- `ts_ns`: IMU sample time in `CLOCK_REALTIME`, in `ns`, provided by the producer's FIFO TMST-to-RAW-to-realtime mapping; `host_ts_ns` is the INT1 edge in the same domain. `TIME_BASE domain=realtime realtime_start_ns=...` reports a startup system reference, not a frozen offset. Runtime clock corrections can move subsequent stamps backward.
- `accel_mps2`: acceleration in `m/s^2`.
- `gyro_rps`: angular velocity in `rad/s`.
- `uncertainty_us`, `gpio_gap_count`, `fifo_overflow_count`, `mapper_failure_count`: timestamp mapping and acquisition-link diagnostics.

V2 `accel_mps2` outputs `[X, Y, Z]`; PCB orientation and signs still need six-face/rotation board verification. Do not infer axis signs or camera-frame transforms from V1 top-view images.

IMU INT1 uses `34120000.gpio` offset `8`, with per-sample FIFO TMST timing. Cameras use LPWM and the VIN-propagated trigger capture, not frame arrival time. Camera and IMU FSYNC share one physical IO; this does not automatically associate FIFO samples one-to-one with exposures.

Use `sensor_demo --fsync --sample-rate-hz 1600` or YAML `imu.fsync_enabled: true` for explicit association (default off, only `800/1600Hz`). Without saving, stdout emits `robobaton_fsync_v1` JSON; saving stores bag `/robobaton/fsync` or MP4 `fsync.jsonl`. Only `status=1` is a unique match. Check timing drops, sequence gaps, and `SENSOR_FSYNC_RESULT`; sample correspondence is not exposure synchronization. See [Data Contracts](../development/data-contracts.md).

Realtime scheduling permission is required: camera capture uses `SCHED_FIFO/60`, IMU owner `SCHED_FIFO/20`, INT1 observer `SCHED_FIFO/30`, and the combined application's IMU consumer `SCHED_RR/3`. Both observers inherit the allowed CPU mask and sleep `50µs` per iteration. Scheduling failure rejects startup. Applications do not automatically change IRQ/debug or realtime quotas; high load can cause counted drops or failure. Storage and association acceptance must also inspect `IMU_RUNTIME_HEALTH final=yes health_valid=yes` after successful stop, not merely continued terminal output.

## 8. Serial Demo


UART1/UART7 retain `3.3V` logic at `/dev/ttyS1` and `/dev/ttyS7`; DEBUG_UART uses `1.8V` and is not for `serial_port_demo`. V2 CN2/CN3 have 5 pins; the separate CN3 IO defaults to PPS input without switching UART7 RX/TX. Use official V2 pin order and power ratings, wire with power off, and do not inherit V1 `500 mA` or hot-plug claims. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart).

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

Boot autostart is implemented through the on-device `/userdata/startup.sh`: the system `S99auto_startup` executes this file after `/userdata` is mounted. The script only appends/removes its own block marked with `SENSOR_DEMO_AUTOSTART_MANAGED` and does not overwrite content written by other scripts (e.g. `wifi_setup.sh`); when canceling autostart, if only comment/blank-line residue remains in the file, it is removed entirely. Boot autostart uses the runtime package's default configuration; edit `config/sensor_config.yaml` directly to adjust it without re-running `enable`. `enable`/`disable` require root privileges.

(non-ros-can)=

## 11. CAN Demo

`can_demo` uses Linux SocketCAN `CAN_RAW` on network devices registered by the TCAN4550 driver. It supports classical CAN only: transmit 11-bit standard or 29-bit extended data frames, receive standard/extended data and remote frames, with `0..8` payload bytes. CAN FD, error-frame subscriptions, and automatic replies are not supported. It does not directly access SPI or change device tree, GPIO, bitrate, or interface state, and does not depend on camera/IMU runtime libraries or `cam-service`.

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

| Option | Meaning |
|---|---|
| `--interface <name>` | Default `can0`; operates only on an existing, UP CAN device |
| `--mode <rx\|tx>` | Default `rx`; no transmission by default |
| `--id <hex>` | TX ID, default `123`; optional `0x`, standard range `0..7FF`, extended range `0..1FFFFFFF` |
| `--extended` | Explicitly select the TX 29-bit format; numeric ID size does not select it automatically |
| `--data <hexbytes>` | TX `0..8` bytes, default `0102030405060708`; even hex-digit count without separators; empty string means zero payload |
| `--count <n>` | RX default `0` (continuous), TX default `1`; explicit `0` runs until Ctrl-C |
| `--interval-ms <n>` | TX inter-frame wait, default `1000`, range `1..3600000` ms; not a realtime-period guarantee |
| `--timeout-ms <n>` | RX idle timeout per wait, default `0` (infinite), range `0..3600000` ms; not a whole-session timeout |
| `--help` / `--version` | Use alone; no CAN hardware access |

TX-only options require `--mode tx`. Invalid arguments exit `2`; interface/I/O/receive-timeout failures exit `1`; count completion or normal SIGINT/SIGTERM interruption exits `0`. Output resembles `rx 123#0102030405060708`; extended IDs use 8 digits, and remote frames resemble `rx 123#R8`.

### Verification and Limits

`tx_queued=N` means only that the kernel accepted N frames, not that the peer received them or each transmission completed on the bus. Default SocketCAN local loopback may let another receiver on the same host see transmitted frames; this does not prove external wiring, transceiver, or ACK operation. External acceptance requires a second physical node to verify ID, format, payload, and count, then reverse transmission to verify reception on this board. Also inspect errors, drops, and BUS-OFF with `ip -details -statistics link show can0`. Host datagram logic tests, vcan, and `--help` do not replace this step.

Use `scripts/build_can_demo.sh` for a standalone build and `scripts/package_runtime.sh` for a full package; see [Building the Public Demo Source](../development/open-source-build.md).
