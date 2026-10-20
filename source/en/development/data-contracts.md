# Data Contracts

This page records the data formats, fields, and time semantics that users can rely on. Undisclosed physical orientation, coordinate systems, extrinsics, and hardware-sync capabilities are explicitly listed as limitations and are not fabricated in the documentation.

## Camera Images and RTSP

| Item | Contract |
|---|---|
| `libsc132.so` / camera callback raw frame | NV12; native `1280x1088` or VSE-scaled `640x480`/`720x480`/`1280x720`; rotation `0/180` keeps width/height unchanged, `90/270` swaps width/height |
| RTSP external stream | H.264 default; H.265 supported |
| FOV | Camera A/B retain horizontal `148.4°`/`115.6°`, vertical `126.6°`/`96.8°`, diagonal `193.8°`/`157.2°`. |
| camera FPS | Default `30fps`, supports `25fps`, `30fps`, `40fps`, `50fps`, and `60fps`; other values rejected before startup side effects |
| RTSP path | `/PRR` |
| Port mapping | CAM1..CAM4 map respectively to software cam0..cam3 and `554/555/556/557`, unchanged from V1. |

The `libsc132.so` callback exposes NV12 raw frames, while RTSP carries H.264/H.265 encoded video. Frame information includes `width`, `height`, `stride`, `vstride`, Y/UV virtual/physical addresses, and sizes. Rotation `90/270` swaps dimensions; consumers must use each frame's metadata and stride/size rather than assume compact `1280x1088`.

## Frame Set Fields

| Field | Meaning |
|---|---|
| `camera_count` | Number of cameras in the current frame group; full four-camera is `4`. |
| `group_id` | Frame-group sequence number. |
| `group_timestamp_ns` | Frame-group timestamp in `ns`. |
| `max_skew_ns` | The maximum timestamp skew actually observed in the current frame group, in `ns`. |
| `items[i].camera_id` | Software ID `0..3`, mapping respectively to physical CAM1..CAM4, unchanged from V1. |
| `items[i].frame_id` | Normalized frame ID. |
| `items[i].timestamp_ns` | Single-channel frame timestamp in `ns`. |

`sc132_frame_set_config_t.max_skew_ns` is the frame-group admission upper bound; its default is `10000000 ns (10ms)`. It limits trigger-capture differences, not exposure alignment accuracy.

## Trigger Modes

| Mode | Current status | Public contract |
|---|---|---|
| `vin_lpwm` | The only supported trigger for all camera applications and the library | Camera and IMU FSYNC share the LPWM IO; camera `timestamp_ns` is the frame-propagated `trig_tv` hardware capture. Missing capture stops acquisition rather than falling back to frame arrival time. |

All public sensor timestamps use `CLOCK_REALTIME` system time (Unix epoch, in ns). Camera stamps still represent the LPWM hardware trigger edge, not frame arrival, IRQ, or exposure midpoint. The library brackets a SIF VSYNC capture-register transition with RAW reads, subtracts `VSYNC − trigger` in the shared 24 MHz counter, and exactly matches the frame's `trig_tv` against capture history. The background thread inherits the process's allowed CPU mask, uses `SCHED_FIFO/60`, and sleeps `50µs` between scans. An in-scan transition uses that scan's bracket, rereads TRIG, and verifies stable VSYNC. Failure to enable realtime scheduling rejects startup. A register window exceeding `500µs`, missing capture, or failed match stops acquisition without an arrival-time fallback. This implementation requires the fixed X5 register map, read-only `/dev/mem` access, and realtime scheduling permission; the rejection window is not demonstrated synchronization accuracy.

Grouping remains in internal RAW time, followed by one freshly sampled RAW-to-realtime bridge for the entire group. Group time is the minimum mapped channel time; `max_skew_ns` measures mapped trigger-time differences, not exposure or camera/IMU alignment accuracy. Non-ROS diagnostics, RTSP input times, saved images, and ROS2 image stamps preserve realtime captures. Bridges follow runtime clock corrections, including backward steps, without a frozen offset or monotonic clamp. Internal timeouts remain monotonic; the FSYNC trigger-to-sample association below is explicitly opt-in.

### Per-frame Exposure Observations

After acquiring each frame and before output transforms, query the latest ISP state once and freeze it in `sc132_frame_info_t.exposure`. Re-reading a retained frame is unaffected by subsequent queries. `status=1` (ESTIMATED) is an estimate attached to that delivered frame, not certified sensor-applied per-frame exposure. Even equal source/frame IDs do not prove atomic latching of exposure and identity. There is no error bound; AE convergence or lighting changes can produce substantial adjacent changes. A failed query, invalid duration, or failed RAW clock read produces `status=0` (UNAVAILABLE), with all other fields zero, never carried forward; image delivery continues.

| Field | Meaning |
|---|---|
| `status` | `0` unavailable (all other exposure fields zero); `1` latest ISP estimate, without accuracy or applied-frame guarantees. |
| `duration_ns` | SDK integration seconds converted to ns, not host waiting/arrival latency. |
| `source_frame_id` / `source_timestamp` | Current SDK identity; timestamp is opaque, not RAW or realtime. Compare with `raw_frame_id` diagnostically, not as proof of the applied-parameter frame. |
| `observed_raw_ns` | Query completion in `CLOCK_MONOTONIC_RAW`, not exposure start/end. |

Public `timestamp_ns` remains the trigger edge. Trigger time plus half the duration is not an actual exposure midpoint: trigger-to-integration-start has not been calibrated. Bag `/cameraN/frame_metadata` and tee `camN/frames.jsonl` preserve `exposure`. MP4 `exposure.jsonl` records input-camera identity, raw/normalized frame IDs, group ID, group/per-camera trigger times, and exposure. It can contain input frames not saved by the encoder: join the camera's timestamp CSV using `group_timestamp_ns // 1000 * 1000`, not source frame ID as a file index. ROS2 `/robobaton/camN/exposure` (`std_msgs/msg/String`, Reliable KeepLast(8)) publishes `robobaton_exposure_v1` JSON with `camera_id/sequence/frame_id/raw_frame_id/timestamp_ns/exposure`; join by camera and Image `header.stamp`. Clock steps may repeat stamps: preserve sequence and acquisition boundaries, rather than assume stamps alone are globally unique. Parse integer JSON losslessly.

MP4 sidecar top-level keys are `camera_id/raw_frame_id/frame_id/group_id/group_timestamp_ns/camera_timestamp_ns/exposure`. Its per-camera trigger field is named `camera_timestamp_ns`, unlike `timestamp_ns` in ROS2 JSON. Check `exposure.status` before using `duration_ns`; do not use `source_timestamp` to align Unix time.

## IMU

| Item | Contract |
|---|---|
| Device path | `/dev/spidev2.0` |
| SPI mode/speed | mode `0`, `10 MHz` |
| INT1 DRDY | `34120000.gpio` offset `8`; not old GPIO395 |
| Read mode | sensor timestamp FIFO |
| FIFO watermark | `1` |
| Native ODR | `25/50/100/200/400/800/1600Hz`, default `800Hz`; old `500/1000/2000Hz` configurations are rejected, not resampled |
| FSYNC | V2 input shares the camera trigger net; opt-in rising-edge capture links a trigger to its first subsequent tagged IMU sample without changing continuous sampling phase. |

Field semantics:

| Field | Unit / semantics |
|---|---|
| `sample_sequence` / demo `sample_seq` | IMU sample sequence number. |
| `temperature_c` / demo `temp_c` | Degrees Celsius. |
| `accel_mps2` | `m/s^2`. |
| `gyro_rps` | `rad/s`. |
| `host_timestamp_ns` | Paired INT1 edge mapped to `CLOCK_REALTIME` nanoseconds; not the sample timestamp. |
| `sample_timestamp_ns` | Per-sample FIFO TMST-to-RAW-to-`CLOCK_REALTIME` timestamp; each publication refreshes the bridge and follows backward system-clock steps. |
| demo `ts_ns` | Producer realtime sample time retained unchanged, in ns; `host_ts_ns` is also realtime, with no further consumer offset. |
| `reserved0` | Count of observed FIFO timestamp low-16-bit rollovers in this session; not V1 20-bit SPI snapshot rollovers. |
| `timestamp_uncertainty_us` | Per-sample time-mapping uncertainty, in microseconds. |
| `gpio_event_gap_count` / `fifo_overflow_count` / `mapper_failure_count` | Cumulative counts of edge gaps, FIFO overflows, and mapping failures in the current session. |

The IMU samples independently and continuously. FSYNC identifies the first hardware-tagged sample after a trigger; it does not make that sample simultaneous with camera exposure. Exposure midpoint, TF extrinsics, and calibration remain unavailable. Neither the host INT1 timestamp nor an FSYNC delta is the sample time.

### FSYNC Trigger-to-Sample Association

Disabled by default. Non-ROS uses `sensor_demo --fsync --sample-rate-hz 1600` or YAML `imu.fsync_enabled: true`; ROS2 sets `imu.fsync_enabled:=true` and `imu.sample_rate_hz:=1600`. Only `800/1600Hz` are supported; the rate is not changed automatically. The tighter `800Hz` budget can cause more timing drops; `1600Hz` also does not guarantee an admissible sample for every trigger.

The hardware FSYNC FIFO tag replaces the packet's absolute TMST with trigger-to-sample delay. The implementation waits for adjacent absolute TMSTs, bounds missing time with legal tick-step intervals, and includes interval half-width in midpoint uncertainty; it never synthesizes timestamps from nominal ODR. Measured clock slope converts delay to ns before subtraction from sample RAW time. Missing endpoints, ambiguous wrap, or uncertainty exceeding the `200µs` policy do not produce fabricated associations.

Camera groups and FSYNC edges match only with a unique candidate in both directions within combined RAW uncertainty intervals, never by nearest neighbor or equal realtime timestamps. History is bounded (128 groups, 256 events); restarted generations cannot mix. JSON schema is `robobaton_fsync_v1`:

| Field | Meaning |
|---|---|
| `status` | `1` unique match; `2` missing event or group; `3` ambiguous. Only `1` is valid. |
| `camera_generation` / `group_id` / `frame_ids` / `camera_mask` | Camera session, group number, cam0..3 frame IDs, and active-camera bitmap. |
| `imu_generation` / `fsync_sequence` / `sample_sequence` | IMU session, hardware trigger sequence, and published sample sequence; gaps are possible. |
| `group_timestamp_ns` / `sample_timestamp_ns` / `fsync_timestamp_ns` | Realtime group trigger, IMU sample, and FSYNC-edge times, in ns. |
| `camera_timestamps_ns` | Original realtime stamp for each cam0..3 frame; use `camera_mask` to select valid entries and join each ROS2 Image/CameraInfo `header.stamp` exactly. Group time is the minimum, not a replacement for every camera stamp. |
| `group_raw_ns` / `sample_raw_ns` / `fsync_raw_ns` | Internal RAW values for association auditing only, not UTC. |
| `fsync_to_sample_ns` | Measured delay from the FSYNC edge to its subsequent hardware-tagged sample. |
| `group_uncertainty_ns` / `uncertainty_ns` | Camera-group and IMU-event mapping uncertainties, not exposure-sync accuracy claims. |

Without saving, JSON goes to stdout; ROS1 bags store `/robobaton/fsync` (`std_msgs/String`); MP4 sessions store `fsync.jsonl`; ROS2 publishes `/robobaton/fsync` (`std_msgs/msg/String`, Reliable KeepLast(256)). Missing-side fields are zero: check `status` and generation first. Storage completeness differs from association completeness: inspect statuses, sequence gaps, and captured/dropped in `SENSOR_FSYNC_RESULT`; exit code or container completeness alone cannot prove every trigger matched.

Read integer timestamps and sequences with a lossless integer JSON parser (for example, Python `json.loads` uses `int`). Epoch nanoseconds exceed the IEEE-754 safe-integer range; ordinary JavaScript `JSON.parse` rounds them, so use a BigInt-aware lossless parser. Association describes source-frame/source-sample identity, not successful storage selection, queue admission, or DDS delivery; cross-check per-camera stamps, frame metadata, and IMU sequences against actual data. With `SENSOR_FSYNC_RESULT health_valid=no`, captured/dropped are `unknown`, not zero; `stdout_dropped` reports stdout write losses.

Load boundary: the acquisition owner uses `SCHED_FIFO/20`; the non-ROS IMU consumer and ROS2 IMU publication thread use `SCHED_RR/3`. Cross-priority queue locks use priority inheritance so ordinary load cannot starve a lock holder. SPI is fixed at `10MHz`; INT1 retains a `100µs` asynchronous-reset pulse. Realtime scheduling permission is required; configuration failures do not silently downgrade scheduling. Applications do not automatically change system IRQ routing, INT1 IRQ thread priority, or SPI dynamic-debug settings; under saturation, these settings and subscriber scheduling still affect results. Absolute-TMST/INT1 phase checks, unique bidirectional matching, and the `200µs` gate remain unchanged: violations are rejected or stop acquisition. At `800Hz`, many FSYNC-tagged samples can still be rejected; this is not a zero-loss guarantee under arbitrary load.

INT1 kernel edge timestamps use MONOTONIC. Conversion to internal RAW uses bounded clock observations near the edge, not a dequeue-time offset applied to a queued edge. An independent observer inherits the allowed CPU mask, uses `SCHED_FIFO/30` (below the board's default FIFO/50 GPIO IRQ thread), and sleeps `50µs` between iterations; startup confirms successful scheduler setup. Its 4096-entry history inserts at intervals of at least `100µs` so a queue-drain burst cannot evict old edge certificates; at lower ODRs this does not guarantee coverage of the entire 256-edge queue. Acquisition also adds observations while waiting for INT1 and polling the sensor clock; a priority-inheritance lock serializes sampling and insertion. Certificate selection accounts for both bracket half-width and clock-steering distance; scheduling delay cannot change the GPIO sequence or reassign an edge to another sample. This steering bound applies to the current X5 Linux 6.1 kernel without `CONFIG_NTP_PPS` or a boot `ntp_tick_adj=` override. Revalidate the clock bound after kernel/boot-parameter changes; never reduce reported uncertainty on that basis.

The sensor TMST-to-RAW fit requires one affine line to satisfy all valid read intervals rather than treating their midpoints as exact observations. An incompatible narrow observation cannot leave a contradicted old certificate. An overwide SPI observation does not advance counter unwrapping. Slope, extrapolation, INT1 phase, and FSYNC reconstruction errors still count toward publication admission. IRQ delays and long SPI stalls can still cause explicitly reported timing rejections, identity failures, or FIFO overflows; neither wider gates nor cached old samples conceal them.

Acceptance must use the final `IMU_RUNTIME_HEALTH final=yes health_valid=yes` after a successful stop: require a nonzero generation and check `published_samples`, `invalid_packet_drop_count`, GPIO gaps, and FIFO overflows. The final record also reports `mapper_failure_count`, `uncertainty_over_200_drop_count`, `max_consecutive_timing_drop_count`, `fsync_captured`, and `fsync_dropped`, including losses after the final successful sample. Invalid packets are counted even when timing admission also rejects them. The last published sample is insufficient because a trailing error may have no later sample to carry its counters. Timing drops and FSYNC dropped tags remain explicitly counted, not complete associations. Storage or DDS acceptance must also read actual IMU/four-camera payloads and verify association coverage using the timestamp rules above, rather than rely only on health summaries, topic existence, or container completeness.

`accel_mps2` outputs `[X, Y, Z]`. The V2 PCB mounting direction and acceleration signs still require on-board six-face/rotation verification; do not inherit the V1 top-view `[0, 0, -9.8]` or left/front axis claims.

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

Storage completeness is recorder-specific. Bag complete checks session success and recorder queue/write errors, not independently zero producer timing drops. MP4 complete additionally requires valid final health after successful stop, published=observed=admitted=written>0, continuous sample sequences, no GPIO/FIFO/timing/invalid-packet drops, and maximum sample uncertainty ≤`200µs`. Default `allow-counted` can continue after timing rejection with provable identity, so bag complete does not prove zero sample loss. Unavailable exposure estimates and missing/ambiguous FSYNC associations also require separate checks rather than inference from container completeness; see [Saving Data](../usage/save-data-guide.md).

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

ROS2 `header.stamp` is not publication time: cameras use realtime trigger-edge times, and IMU/Temperature use realtime `sample_timestamp_ns`, not `host_timestamp_ns`. ROS2 only splits nanoseconds into `sec`/`nanosec`, without another offset. Stamps can be compared on the same calibrated system timeline, but a common domain does not guarantee hardware sample/exposure alignment; cross-device accuracy still depends on clock synchronization. `use_sim_time` does not change sensor stamps to simulation `/clock`. Subsequent stamps follow NTP/PTP system-clock corrections; these services do not establish FSYNC sample associations.

ROS2 does not publish RTSP, TF extrinsics, or calibration. FSYNC provides trigger-to-sample correspondence only, without changing sample phase or guaranteeing exposure synchronization. For general visualization, prefer `/image_raw/compressed`; ordinary RGB/BGR tools may not display raw NV12.

## UART

| Item | Contract |
|---|---|
| Default device | `/dev/ttyS1` |
| Switchable example | `/dev/ttyS7` or another site device |
| Baud rate | `serial_port_demo` defaults to `115200`; DEBUG_UART uses `921600`. |
| serial_port_demo data format | 8N1, raw, no flow control |
| demo modes | `tx`, `rx`, `txrx`, `echo` |
| UART1/UART7 TX/RX signal logic level | Unchanged `3.3V`; DEBUG_UART uses `1.8V`. |
| UART1/UART7 power pins | V2 CN2/CN3 power function, voltage, rated load, and hot-plug limits pending confirmation; do not reuse the V1 `500 mA` total limit. |
| Historical V1 boundary | UART1/UART7 were validated on V1; this is not proof of V2 electrical or harness compatibility. |

V2 UART1/UART7 use CN2/CN3 5-pin connectors and `/dev/ttyS1`, `/dev/ttyS7`. CN3 has an independent IO enabled as PPS input by default, without RX/TX mux switching; discover the enumerated PPS device. Use official V2 labeling for complete pin order and power-pin function. DEBUG_UART is not a user serial port. Wire with power off after checking TX/RX/GND, peer voltage, and common ground; leave adapter VCC disconnected and prevent reverse feed. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart).
