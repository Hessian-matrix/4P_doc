# Data Contracts

This page records the data formats, fields, and time semantics that users can rely on. Undisclosed physical orientation, coordinate systems, extrinsics, and hardware-sync capabilities are explicitly listed as limitations and are not fabricated in the documentation.

Parameters and fields describe the current implemented contract, not acceptance of a complete mode/load/duration matrix. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for current results and limits.

## Camera Images and RTSP

| Item | Contract |
|---|---|
| `libsc132.so` / camera callback raw frame | NV12; native `1280x1088` or VSE-scaled `640x480`/`720x480`/`1280x720`; rotation `0/180` keeps width/height unchanged, `90/270` swaps width/height |
| RTSP external stream | H.264 default; H.265 supported |
| FOV | Camera A/B retain horizontal `148.4°`/`115.6°`, vertical `126.6°`/`96.8°`, diagonal `193.8°`/`157.2°`. |
| camera FPS | Default `30fps`, supports `25fps`, `30fps`, `40fps`, `50fps`, and `60fps`; other values rejected before startup side effects |
| RTSP path | `/PRR` |
| Port mapping | CAM1..CAM4 map respectively to software cam0..cam3 and `554/555/556/557`. |

The `libsc132.so` callback exposes NV12 raw frames, while RTSP carries H.264/H.265 encoded video. Frame information includes `width`, `height`, `stride`, `vstride`, Y/UV virtual/physical addresses, and sizes. Rotation `90/270` swaps dimensions; consumers must use each frame's metadata and stride/size rather than assume compact `1280x1088`.

For complete C declarations, field-by-field meanings, NV12 row layout, and reference lifetime, see the {ref}`API Image Output Structure Reference <camera-output-structures>`.

Only full four-camera operation or single-sensor diagnostics is supported, not 2/3-camera combinations; rotation `180` requires `30fps`. VSE sizes are the discrete set above, not arbitrary scaling.

## Frame Set Fields

| Field | Meaning |
|---|---|
| `camera_count` | Number of cameras in the current frame group; full four-camera is `4`. |
| `group_id` | Frame-group sequence number. |
| `group_timestamp_ns` | Frame-group timestamp in `ns`. |
| `max_skew_ns` | Observed trigger-capture span of the group in `ns`; test exposure-midpoint offsets do not change it. |
| `items[i].camera_id` | Software ID `0..3`, mapping respectively to physical CAM1..CAM4. |
| `items[i].frame_id` | Normalized frame ID. |
| `items[i].timestamp_ns` | Single-channel frame timestamp in `ns`. |

`sc132_frame_set_config_t.max_skew_ns` is the frame-group admission upper bound; its default is `10000000 ns (10ms)`. It limits trigger-capture differences, not exposure alignment accuracy.

## Trigger Modes

| Mode | Current status | Public contract |
|---|---|---|
| `vin_lpwm` | The only supported trigger for all camera applications and the library | Camera and IMU FSYNC share the LPWM IO; the camera time base is the frame-propagated `trig_tv` hardware capture. Missing capture stops acquisition rather than falling back to frame arrival time. |

All public sensor timestamps use `CLOCK_REALTIME` system time (Unix epoch, in ns). By default camera stamps represent the LPWM hardware trigger edge, not frame arrival, IRQ, or exposure midpoint; see the opt-in {ref}`Exposure-Midpoint Test Switch <test-exposure-midpoint>`. The library brackets a SIF VSYNC capture-register transition with RAW reads, subtracts `VSYNC − trigger` in the shared 24 MHz counter, and exactly matches the frame's `trig_tv` against capture history. The background thread inherits the process's allowed CPU mask, uses `SCHED_FIFO/60`, and sleeps `50µs` between scans. An in-scan transition uses that scan's bracket, rereads TRIG, and verifies stable VSYNC. Failure to enable realtime scheduling rejects startup. A register window exceeding `500µs`, missing capture, or failed match stops acquisition without an arrival-time fallback. This implementation requires the fixed X5 register map, read-only `/dev/mem` access, and realtime scheduling permission; the rejection window is not demonstrated synchronization accuracy.

Frame-set mode first discards 30 warmup frames per camera by default. Until all enabled cameras finish warmup, buffers are returned immediately, without exposure queries, image transforms, or capture-map admission for these unpublished frames. Every delivered frame after warmup still requires a valid exact capture match with the unchanged `500µs` window limit; disabling warmup does not exempt the first frame.

Grouping remains in internal trigger RAW time, followed by one freshly sampled RAW-to-realtime bridge for the entire group. Group time is the minimum delivered channel timestamp; `max_skew_ns` always measures trigger-capture differences, not exposure or camera/IMU alignment accuracy. Non-ROS diagnostics, RTSP input times, saved images, and ROS2 image stamps use the delivered timestamp: realtime trigger time by default, estimated exposure midpoint in test mode. Bridges follow runtime clock corrections, including backward steps, without a frozen offset or monotonic clamp. Internal timeouts remain monotonic; the FSYNC trigger-to-sample association below is explicitly opt-in.

### Per-frame Exposure Observations

After acquiring each frame and before output transforms, query the latest ISP state once and freeze it in `sc132_frame_info_t.exposure`. Re-reading a retained frame is unaffected by subsequent queries. `status=1` (ESTIMATED) is an estimate attached to that delivered frame, not certified sensor-applied per-frame exposure. Even equal source/frame IDs do not prove atomic latching of exposure and identity. There is no error bound; AE convergence or lighting changes can produce substantial adjacent changes. A failed query, invalid duration, or failed RAW clock read produces `status=0` (UNAVAILABLE), with all other fields zero, never carried forward; default image delivery continues, but exposure-midpoint test mode stops acquisition.

| Field | Meaning |
|---|---|
| `status` | `0` unavailable (all other exposure fields zero); `1` latest ISP estimate, without accuracy or applied-frame guarantees. |
| `duration_ns` | SDK integration seconds converted to ns, not host waiting/arrival latency. |
| `source_frame_id` / `source_timestamp` | Current SDK identity; timestamp is opaque, not RAW or realtime. Compare with `raw_frame_id` diagnostically, not as proof of the applied-parameter frame. |
| `observed_raw_ns` | Query completion in `CLOCK_MONOTONIC_RAW`, not exposure start/end. |

Public `timestamp_ns` is the trigger edge by default. The test switch can select trigger time plus half the duration, but this is not a certified exposure midpoint: trigger-to-integration-start has not been calibrated. Bag `/cameraN/frame_metadata` and tee `camN/frames.jsonl` preserve `exposure`. MP4 `exposure.jsonl` records input-camera identity, raw/normalized frame IDs, group ID, group/per-camera delivered times, and exposure. It can contain input frames not saved by the encoder: join the camera's timestamp CSV using `group_timestamp_ns // 1000 * 1000`, not source frame ID as a file index. ROS2 `/robobaton/camN/exposure` (`std_msgs/msg/String`, Reliable KeepLast(8)) publishes `robobaton_exposure_v1` JSON with `camera_id/sequence/frame_id/raw_frame_id/timestamp_ns/exposure`; join by camera and Image `header.stamp`. Clock steps may repeat stamps: preserve sequence and acquisition boundaries, rather than assume stamps alone are globally unique. Parse integer JSON losslessly.

MP4 sidecar top-level keys are `camera_id/raw_frame_id/frame_id/group_id/group_timestamp_ns/camera_timestamp_ns/exposure`. Its per-camera delivered-time field is named `camera_timestamp_ns`, unlike `timestamp_ns` in ROS2 JSON. Check `exposure.status` before using `duration_ns`; do not use `source_timestamp` to align Unix time.

(test-exposure-midpoint)=
### Exposure-Midpoint Timestamp Test Switch

Only `libsc132.so` rebuilt from current source supports `SC132_TEST_EXPOSURE_MIDPOINT`; existing delivered binaries are not updated automatically. Disabled by default; set `1` before startup to enable, or set `0`/unset it to restore the original logic. No C ABI, SONAME, or software-version change.

```bash
SC132_TEST_EXPOSURE_MIDPOINT=1 ./cam_demo
SC132_TEST_EXPOSURE_MIDPOINT=0 ./cam_demo
```

Read once at each `sc132_start_frame_set()` startup, never toggled during acquisition. Unset, empty, or `0/false/FALSE/off/OFF/no/NO` disables it; any other nonempty value enables it. Stop and restart the process/acquisition after changing the environment; ROS2 must pass the variable to the node or launch process.

The non-ROS combined entry `sensor_demo` also accepts `camera.test_exposure_midpoint: true|false` in `config/sensor_config.yaml`; packaged and auto-generated configurations default to `false`. Explicit YAML overrides the environment; only an omitted key preserves environment control. Rebuild `sensor_demo` and a supporting library, and restart after configuration changes. `cam_demo` does not read this YAML; ROS2 still uses the environment variable. See {ref}`non-ROS YAML Configuration <non-ros-yaml>`.

When enabled, each `timestamp_ns = realtime trigger time + floor(exposure.duration_ns / 2)`, using that frame's frozen latest ISP observation. It ignores trigger-to-integration-start delay, not replacing time with host now, arrival time, or opaque source time. Frame info and frame-set items agree; group time is the minimum adjusted channel timestamp. Non-ROS saving/RTSP, ROS2 Image/CameraInfo, and exposure messages use these values; consumers must not add half exposure a second time. Unavailable exposure, zero duration, or addition overflow stops acquisition rather than silently reverting to trigger time.

Group admission and `max_skew_ns` still use original trigger RAW; reserved RAW/generation/uncertainty and FSYNC correspondence are not shifted. Thus test-mode group time and RAW audit time intentionally describe different events. This is only an exposure-midpoint estimate without delay compensation, not a guarantee of applied exposure, error bounds, or hardware synchronization accuracy.


## IMU

| Item | Contract |
|---|---|
| Device path | `/dev/spidev2.0` |
| SPI mode/speed | mode `0`, `10 MHz` |
| INT1 DRDY | `34120000.gpio` offset `8`; not old GPIO395 |
| Read mode | sensor timestamp FIFO |
| FIFO watermark | `1` |
| Native ODR | `25/50/100/200/400/800/1600Hz`, default `800Hz`; other values are rejected, not resampled |
| FSYNC | V2 input shares the camera trigger net; opt-in rising-edge capture links a trigger to its first subsequent tagged IMU sample without changing continuous sampling phase. |

Field semantics:

| Field | Unit / semantics |
|---|---|
| `sample_sequence` / demo `sample_seq` | IMU sequence defined by FIFO order, not INT1 notifications or increasing realtime. |
| `temperature_c` / demo `temp_c` | Degrees Celsius. |
| `accel_mps2` | `m/s^2`. |
| `gyro_rps` | `rad/s`. |
| `host_timestamp_ns` / CLI `fifo_observation_ns` | RAW observation at the packet's successful SPI FIFO burst completion, converted to `CLOCK_REALTIME` ns using the bridge measured for that observation. Packets in one burst may share it; FSYNC deferral retains the converted value, possibly earlier than publication, without rebridging old RAW. Follows wall steps; not IRQ-edge, sample, or exposure time. |
| `sample_timestamp_ns` | Per-sample FIFO TMST-to-RAW-to-`CLOCK_REALTIME` timestamp; each publication refreshes the bridge and follows backward system-clock steps. |
| demo `ts_ns` | Producer realtime sample time retained unchanged, in ns; `host_ts_ns` is also realtime, with no further consumer offset. |
| `reserved0` | Count of observed FIFO timestamp low-16-bit rollovers in this session. |
| `timestamp_uncertainty_us` | Per-sample time-mapping uncertainty, in microseconds. |
| `gpio_event_gap_count` / `fifo_overflow_count` / `mapper_failure_count` | Session counts of detectable missing GPIO notification sequence values, FIFO overflows, and mapping failures. GPIO gaps are diagnostic, not proof of physical-edge/sample loss or independently fatal. |

The IMU samples continuously and independently. FIFO order and measured chip TMST define sequence and time; INT1 only wakes FIFO draining, without per-packet pairing. FSYNC uses chip tags/deltas and measured endpoints to identify the first tagged sample after a trigger, not exposure simultaneity. Exposure midpoint, TF extrinsics, and calibration remain unavailable. Neither host observations nor FSYNC deltas are sample time. Both realtime stamps follow clock corrections; unique host values and increasing wall time are not acquisition-order requirements.

### Web Attitude Preview Inputs

The `sensor_demo` IMU SSE retains `schema_version: 1` and adds three-element arrays `attitude_accel_mps2` (`m/s²`) and `attitude_gyro_rps` (`rad/s`) for browser attitude preview only. Raw `accel_mps2` / `gyro_rps`, values/traces, native sampling, saved data, and C ABI are unchanged. Nanosecond timestamps, sequences, and session IDs remain decimal strings to preserve precision.

The device processes all six axes at every native sample through four cascaded one-pole low-pass stages before extracting telemetry. Each pole is `min(10Hz, telemetry limit×0.2, source rate×0.2)`, with about 64ms low-frequency group delay at the default 800→50Hz. The timestamp identifies the current input sample, not a delay-compensated measurement or a single raw observation. Invalid input produces JSON `null` attitude-array elements. Non-increasing timestamps, a sequence reset, or native-sample gaps over 100ms reseed history without synthesizing missing samples. Filtering estimates neither attitude nor bias; the browser independently fuses inputs and uses raw axes for stationary-quality checks. Absolute heading and removal of vibration-rectification error are not guaranteed.

### FSYNC Trigger-to-Sample Association

Disabled by default. Non-ROS uses `sensor_demo --fsync --sample-rate-hz 1600` or YAML `imu.fsync_enabled: true`; ROS2 sets `imu.fsync_enabled:=true` and `imu.sample_rate_hz:=1600`. Only `800/1600Hz` are supported; the rate is not changed automatically. The tighter `800Hz` budget can cause more timing drops; `1600Hz` also does not guarantee an admissible sample for every trigger.

The hardware FSYNC FIFO tag replaces the packet's absolute TMST with trigger-to-sample delay. The implementation waits for adjacent absolute TMSTs, bounds missing time with legal tick-step intervals, and includes interval half-width in midpoint uncertainty; it never synthesizes timestamps from nominal ODR. Measured clock slope converts delay to ns before subtraction from sample RAW time. Missing endpoints, ambiguous wrap, or uncertainty exceeding the `200µs` policy do not produce fabricated associations.

Retain a leading FSYNC-tagged packet and its original burst-completion observation until a later absolute TMST permits reconstruction, without waiting for or consuming a corresponding GPIO identity. The measured pre-enable Arm transition is not a preceding FIFO sample: check shared-transition and one-full-legal-ODR-later hypotheses separately, narrowed by later measured endpoints. Accept only a unique feasible hypothesis, never fractional phases. Both FIFO-enable writes must complete before the shortest legal ODR interval measured from the start of the Arm observation bracket, converted using the measured clock-slope lower bound. Exceeding this deadline rejects startup to prevent whole-TMST-wrap aliasing. Unique wrap, measured clocks, and `200µs` admission remain required. Unprovable clocks/epochs fail; over-budget samples retain strict/allow-counted policies and health counters.

Camera groups and FSYNC edges match only with a unique candidate in both directions within combined RAW uncertainty intervals, never by nearest neighbor or equal realtime timestamps. History is bounded (128 groups, 256 events); restarted generations cannot mix. JSON schema is `robobaton_fsync_v1`:

| Field | Meaning |
|---|---|
| `status` | `1` unique match; `2` missing event or group; `3` ambiguous. Only `1` is valid. |
| `camera_generation` / `group_id` / `frame_ids` / `camera_mask` | Camera session, group number, cam0..3 frame IDs, and active-camera bitmap. |
| `imu_generation` / `fsync_sequence` / `sample_sequence` | IMU session, hardware trigger sequence, and published sample sequence; gaps are possible. |
| `group_timestamp_ns` / `sample_timestamp_ns` / `fsync_timestamp_ns` | Realtime delivered group, IMU sample, and FSYNC-edge times, in ns; group time defaults to trigger time and becomes the minimum estimated camera exposure midpoint in test mode. |
| `camera_timestamps_ns` | Original realtime stamp for each cam0..3 frame; use `camera_mask` to select valid entries and join each ROS2 Image/CameraInfo `header.stamp` exactly. Group time is the minimum, not a replacement for every camera stamp. |
| `group_raw_ns` / `sample_raw_ns` / `fsync_raw_ns` | Internal RAW values for association auditing only, not UTC; group RAW always means earliest trigger and is not shifted by exposure-midpoint test mode. |
| `fsync_to_sample_ns` | Measured delay from the FSYNC edge to its subsequent hardware-tagged sample. |
| `group_uncertainty_ns` / `uncertainty_ns` | Camera-group and IMU-event mapping uncertainties, not exposure-sync accuracy claims. |

Without saving, JSON goes to stdout; ROS1 bags store `/robobaton/fsync` (`std_msgs/String`); MP4 sessions store `fsync.jsonl`; ROS2 publishes `/robobaton/fsync` (`std_msgs/msg/String`, Reliable KeepLast(256)). Missing-side fields are zero: check `status` and generation first. Storage completeness differs from association completeness: inspect statuses, sequence gaps, and captured/dropped in `SENSOR_FSYNC_RESULT`; exit code or container completeness alone cannot prove every trigger matched.

Read integer timestamps and sequences with a lossless integer JSON parser (for example, Python `json.loads` uses `int`). Epoch nanoseconds exceed the IEEE-754 safe-integer range; ordinary JavaScript `JSON.parse` rounds them, so use a BigInt-aware lossless parser. Association describes source-frame/source-sample identity, not successful storage selection, queue admission, or DDS delivery; cross-check per-camera stamps, frame metadata, and IMU sequences against actual data. With `SENSOR_FSYNC_RESULT health_valid=no`, captured/dropped are `unknown`, not zero; `stdout_dropped` reports stdout write losses.

Load boundary: the acquisition owner uses `SCHED_FIFO/20`; non-ROS IMU consumers and ROS2 IMU publication use `SCHED_RR/3`. Cross-priority queue locks use priority inheritance. SPI is `10MHz`; INT1 retains its `100µs` asynchronous-reset wake pulse. Realtime scheduling failure never silently downgrades. Applications do not automatically change IRQs, SPI dynamic-debug, realtime quotas, LPWM, or the kernel. SPI/scheduling and subscriber load still matter. Measured TMST, unique bidirectional FSYNC matching, and `200µs` admission remain unchanged, without a zero-loss guarantee under arbitrary load.

INT1 is notification, not a sample clock or per-packet identity source; GPIO software IRQ timestamps are not physical-edge hardware latches and acquisition does not consume them. Detectable notification sequence gaps only increment `gpio_event_gap_count`; continuous sequences cannot rule out loss/merging before event generation. FIFO/TMST-led acquisition removes per-edge pairing but **does not fix or establish the underlying GPIO/kernel cause**. Diagnosing that cause still requires matching-BSP IRQ capture or synchronized physical waveforms. Bounded timeouts still check FIFO liveness without IRQs. Do not infer sample loss from notification gaps; inspect FIFO/sample sequences, final health, and actual payloads.

The sensor TMST-to-RAW fit requires one affine line satisfying valid read intervals, not exact midpoint observations. Contradictory narrow observations invalidate old certificates; overwide SPI observations do not advance unwrapping. Slope, extrapolation, and FSYNC reconstruction count toward admission uncertainty. FIFO overflow, bad packets, wrap/clock ambiguity, and invalid epochs still fail. Long SPI stalls can still reject samples or stop acquisition; wider gates, nominal-ODR timestamps, and cached old samples do not conceal failures.

Acceptance must use the final `IMU_RUNTIME_HEALTH final=yes health_valid=yes` after a successful stop: require a nonzero generation and check `published_samples`, `invalid_packet_drop_count`, GPIO gaps, and FIFO overflows. The final record also reports `mapper_failure_count`, `uncertainty_over_200_drop_count`, `max_consecutive_timing_drop_count`, `fsync_captured`, and `fsync_dropped`, including losses after the final successful sample. Invalid packets are counted even when timing admission also rejects them. The last published sample is insufficient because a trailing error may have no later sample to carry its counters. Timing drops and FSYNC dropped tags remain explicitly counted, not complete associations. Storage or DDS acceptance must also read actual IMU/four-camera payloads and verify association coverage using the timestamp rules above, rather than rely only on health summaries, topic existence, or container completeness.

`accel_mps2` outputs `[X, Y, Z]`. The V2 PCB mounting direction and acceleration signs still require on-board six-face/rotation verification. Axis signs and transforms relative to the main board or cameras are not currently declared.

## non-ROS Save Output

| Output | Contract |
|---|---|
| ROS bag | `sensor_demo --record-bag <absolute .bag>` saves four-channel JPEG images, camera parameters, and IMU data; incomplete stress/abnormal runs use an explicit `.partial.bag` recovery file. |
| MP4 session | `sensor_demo --record-mp4-dir <absolute directory>` saves four H.264 MP4s, four timestamp CSVs, `imu.csv`, input-frame `exposure.jsonl`, `fsync.jsonl`, `camera_params.yaml`, `session_status.json`, and `publication_receipt.json`. The FSYNC file is always created; association records require FSYNC enabled. |
| MP4 path conflict | When the configured final directory or a same-named `.partial` already exists, the actual output automatically switches to the sibling `<name>-YYYYMMDDTHHMMSSZ[-NNNN]`; follow `SENSOR_MP4_RESULT path=`. |
| `.partial` | Keeps the recovery namespace; a `.partial` MP4 session can be extracted for inspection but is not declared complete. |

MP4 mode only supports H.264 and the full four-channel camera mask `0x0f`, and cannot be enabled together with bag saving or frame-skip. MP4 file timing is nominal container timing. The same session's `cameraN_timestamps.csv` aligns encoded frames by `frame_index` and stores realtime group-trigger times quantized to encoder microsecond precision, expressed in ns, not each camera's original nanosecond stamp. With FSYNC enabled, `fsync.jsonl` preserves original per-camera values in `camera_timestamps_ns`; compare CSV against `group_timestamp_ns // 1000 * 1000`. After storage drops, producer `frame_ids` must not be treated directly as file `frame_index`. A `published_complete` source must carry a matching `publication_receipt.json` and a complete four-channel MP4/index inventory.

Bag payload stamps are separate from record time: image and first-frame CameraInfo `header.stamp` preserve realtime camera captures; IMU payloads retain realtime sample stamps. Bag record time independently reads `CLOCK_REALTIME` at writing, not sampling. Backward clock steps are preserved rather than clamped. Physical write order remains unchanged; each connection's chunk index is time-sorted for ROS bag readers. Session config declares `camera_timestamp_domain`, `imu_timestamp_domain`, and `record_timestamp_domain` all as `"realtime"`.

MP4 CSV indexes use the realtime system timeline, subject to the precision and per-camera distinction above; container playback remains relative/nominal, not Unix epoch. A backward step unsupported by the encoder/container produces an error and incomplete artifacts rather than fabricated increasing times. Complete system-clock synchronization before continuous recording.

Storage completeness is recorder-specific. Bag complete checks the session and recorder queue/write errors, not independently zero producer timing drops. MP4 complete additionally requires valid successful-stop final health, published=observed=admitted=written>0, continuous sequences, zero FIFO/timing/invalid-packet drops, and maximum uncertainty ≤`200µs`. GPIO notification gaps are diagnostic and do not independently make storage incomplete. Default `allow-counted` may continue after timing rejection with provable clock identity, so bag complete does not prove zero sample loss. Exposure/FSYNC completeness needs separate checks; see [Saving Data](../usage/save-data-guide.md).

Bag overload retains/drops complete four-camera groups together. The default minimum interval `10` uses contiguous `source_group_order`, not producer `group_id`. Candidates must be fully encoded, complete, and unclaimed; writer-claimed groups stay protected. Without a legal old or incoming group to drop, stop and drain to a readable partial bag with nonzero exit. Every group drop means `data_complete=false`; policy compliance is not sustained-pressure or all-sensor acceptance. Intentional alternate saving explicitly requires minimum interval `2`; see [Saving Queue Diagnostics](../usage/save-data-guide.md).

Native bag JPEG removes only the length-`4` JPU APP9 immediately after SOI containing private frameIdx, preserving other APP markers and coded payload without changing ROS2 JPEG plugin output. `rosbag_info.py --freq` measures record time; `--header-freq` separately reports saved-message `Header.stamp`. Neither alone proves lossless acquisition. Compare producer, consumer, recorder, and readback counts separately; continuous saved sequences can still omit source head/tail data.

## ROS2 Topics

| Topic | Message type | Contract |
|---|---|---|
| `/robobaton/cam0..3/image_raw` | `sensor_msgs/msg/Image` | Four raw NV12 images, `encoding="nv12"`. |
| `/robobaton/cam0..3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | Standard compressed transport JPEG; the current plugin uses X5 media codec hardware JPEG encoding. |
| `/robobaton/cam0..3/camera_info` | `sensor_msgs/msg/CameraInfo` | Only contains the current frame width/height; calibration fields are empty. |
| `/robobaton/cam0..3/exposure` | `std_msgs/msg/String` | `robobaton_exposure_v1` frozen per-frame ISP observations; `status=1` is an estimate, not certified applied-frame identity. |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42670-P gyro/accel; orientation unavailable. |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42670-P temperature, reusing the IMU sample stamp. |
| `/robobaton/fsync` | `std_msgs/msg/String` | Opt-in FSYNC association JSON. |

ROS2 QoS:

| Data | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | Follows the raw publisher, also Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
| Exposure | Reliable + KeepLast(8) |
| FSYNC | Reliable + KeepLast(256), disabled by default |
| IMU | `SensorDataQoS`, keep last 100 |
| Temperature | `SensorDataQoS`, keep last 10 |

ROS2 raw `Image.step` uses the underlying DMA buffer's stride; `data.size()` uses the underlying Y/UV buffer size, which may be larger than the compact `width * height * 3 / 2`. Subscribers must not index the UV plane directly under the compact-NV12 assumption.

ROS2 `header.stamp` is not publication time: cameras use realtime trigger-edge times by default or the estimated exposure midpoint in opt-in test mode. IMU/Temperature use realtime `sample_timestamp_ns`, not `host_timestamp_ns`. ROS2 only splits nanoseconds into `sec`/`nanosec`, without another offset. Stamps can be compared on the same calibrated system timeline, but a common domain does not guarantee hardware sample/exposure alignment; cross-device accuracy still depends on clock synchronization. `use_sim_time` does not change sensor stamps to simulation `/clock`. Subsequent stamps follow NTP/PTP system-clock corrections; these services do not establish FSYNC sample associations.

ROS2 does not publish RTSP, TF extrinsics, or calibration. FSYNC provides trigger-to-sample correspondence only, without changing sample phase or guaranteeing exposure synchronization. For general visualization, prefer `/image_raw/compressed`; ordinary RGB/BGR tools may not display raw NV12.

## UART

| Item | Contract |
|---|---|
| Default device | `/dev/ttyS1` |
| Switchable example | `/dev/ttyS7` or another site device |
| Baud rate | `serial_port_demo` defaults to `115200`; DEBUG_UART uses `921600`. |
| serial_port_demo data format | 8N1, raw, no flow control |
| demo modes | `tx`, `rx`, `txrx`, `echo` |
| UART1/UART7 TX/RX signal logic level | `3.3V`; DEBUG_UART uses `1.8V`. |
| UART1/UART7 power pins | Pin 1 is the 3V3 power pin; leave it disconnected by default. Rated load and hot-plug limits await confirmation. Wire with power off, leave adapter VCC disconnected, and prevent reverse feed. |

UART1 uses CN1 GH1.25 4-pin and `/dev/ttyS1`; UART7 uses CN2 GH1.25 5-pin and `/dev/ttyS7`. UART7 pin 4 is the independent PPS input, enabled by default without RX/TX mux switching; discover the enumerated PPS device. See the {ref}`Interface Wiring Diagram <wiring-diagram>` for pin numbers and signal order, and check orientation against physical labeling before crimping. DEBUG_UART is not a user serial port. Wire with power off after checking TX/RX/GND, peer voltage, and common ground; leave adapter VCC disconnected and prevent reverse feed. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart).
