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
| `vin_lpwm` | Only supported camera trigger | Uses frame-propagated `trig_tv` capture; missing capture stops acquisition without arrival-time fallback. |

Camera timestamps use `CLOCK_REALTIME` system time (Unix epoch, in ns). With exposure-midpoint testing disabled, they represent the selected LPWM trigger-time estimate, not frame arrival or exposure midpoint. The startup-only `camera_timestamp_path` selects `observer` (default) or `official`; direct library users set `SC132_TIMESTAMP_PATH` before startup. Stop and restart to change it; invalid values fail startup and neither path falls back to the other.

- `observer`: bracket a SIF VSYNC capture-register transition with RAW reads, subtract `VSYNC − trigger` in the shared 24 MHz counter, and exactly match the frame's `trig_tv` against capture history. The background thread inherits the allowed CPU mask, uses `SCHED_FIFO/60`, and sleeps `50µs` between scans. An in-scan transition uses that scan's bracket, rereads TRIG, and verifies stable VSYNC. Missing realtime scheduling permission rejects startup. A register window exceeding the unchanged `500µs` admission limit, missing capture, or failed match stops acquisition. This path requires the fixed X5 register map and read-only `/dev/mem`; the window is not demonstrated physical synchronization accuracy.
- `official`: use the same frame's `out_img.info.timestamps` (IRQ time in `CLOCK_MONOTONIC_RAW`) minus `(tv − trig_tv) × 1000`, where `tv` and `trig_tv` are AON microseconds, not RAW/realtime epochs. It never starts or uses the SIF MMIO observer. Invalid metadata, arithmetic overflow, or underflow stops acquisition. This is an IRQ-derived trigger estimate with an unknown physical-error bound: `reserved[SC132_GROUP_TIMING_VALID]=0` and `reserved[SC132_GROUP_UNCERTAINTY_NS]=UINT32_MAX`, never the observer's bounded validity marker.

Frame-set mode first discards 30 warmup frames per camera by default. Each acquisition worker queries exposure and primes its one-hardware-frame association during warmup, then immediately returns buffers without image transforms or timestamp admission for these unpublished frames. Every delivered frame must satisfy the selected path: an exact capture match within the `500µs` window for observer, or valid same-frame metadata/arithmetic for official. Disabling warmup neither exempts the first frame nor creates an exposure predecessor.

Grouping uses the selected trigger RAW estimate, followed by one freshly sampled RAW-to-realtime bridge for the entire group. Group time is the minimum delivered channel timestamp; `max_skew_ns` measures differences between selected trigger estimates, not exposure or camera/IMU alignment accuracy. Non-ROS diagnostics, RTSP input times, saved images, and ROS2 image stamps use the delivered timestamp: realtime trigger estimate by default, estimated exposure midpoint in test mode. Bridges follow runtime clock corrections, including backward steps, without a frozen offset or monotonic clamp. Internal timeouts remain monotonic. IMU selectors and clocks are independent of the camera path.

### Per-frame Exposure Observations

Each acquisition worker exclusively owns zero-initialized per-session exposure-association state. An ISP getter obtained while acquiring raw hardware frame N estimates adjacent N+1 only. Matching uses uint32 adjacency of acquired raw hardware frame IDs, allowing wrap, never normalized `frame_id`, group IDs, or SDK `source_frame_id`. Frame-set warmup primes this association. Only getter metadata is retained, without extra image buffering or delivery delay. The matched result is frozen in the target frame's `sc132_frame_info_t.exposure`; re-reading a retained frame is unaffected by later queries.

The first acquired frame without a predecessor, a hardware frame-ID gap, or an invalid predecessor query yields `status=0` (UNAVAILABLE), with all other exposure fields zero. Never stretch an older value across a gap. A failed query, invalid duration, or failed RAW clock read invalidates that getter. Query failure at N makes N+1 unavailable, but a valid adjacent predecessor can still estimate N. Default image delivery continues; exposure-midpoint test mode still stops on unavailable exposure without trigger-time fallback.

`status=1` (ESTIMATED) is only a fixed one-hardware-frame association estimate, not certified sensor-applied per-frame exposure. Equal source identities from a non-atomic getter do not prove synchronous parameter latching. There is no measured physical-error bound or resulting claim about AE behavior or real-board acceptance. This semantic fix changes neither public structure layout, SONAME, software versions, nor default trigger timestamps. Consumers forward `exposure` unchanged and must not apply another frame shift.

Fixed N→N+1 is the chosen estimated-association rule, not a universal law of effective AE lag. Real AE can have a different effective lag; this rule provides no per-frame guarantee of applied exposure or identity.

| Field | Meaning |
|---|---|
| `status` | `0` unavailable (all other exposure fields zero); `1` fixed one-hardware-frame association estimate, without a measured physical-error bound or applied-exposure guarantee. |
| `duration_ns` | SDK integration seconds converted to ns, not host waiting/arrival latency. |
| `source_frame_id` / `source_timestamp` | Original SDK identity from the older getter, preserved rather than rewritten to the target image; never used for hardware-frame adjacency matching. Timestamp is opaque, not RAW/realtime, and does not certify the applied-parameter frame. |
| `observed_raw_ns` | Original `CLOCK_MONOTONIC_RAW` completion time of the older getter, not rewritten to target-image time and not exposure start/end. |

Public `timestamp_ns` is the trigger edge by default. The test switch can select trigger time plus half the duration, but this is not a certified exposure midpoint: trigger-to-integration-start has not been calibrated. Bag `/cameraN/frame_metadata` and tee `camN/frames.jsonl` preserve `exposure`. MP4 `exposure.jsonl` records input-camera identity, raw/normalized frame IDs, group ID, group/per-camera delivered times, and exposure. It can contain input frames not saved by the encoder: join the camera's timestamp CSV using `group_timestamp_ns // 1000 * 1000`, not source frame ID as a file index. ROS2 `/robobaton/camN/exposure` (`std_msgs/msg/String`, Reliable KeepLast(8)) publishes `robobaton_exposure_v1` JSON with `camera_id/sequence/frame_id/raw_frame_id/timestamp_ns/exposure`; join by camera and Image `header.stamp`. Clock steps may repeat stamps: preserve sequence and acquisition boundaries, rather than assume stamps alone are globally unique. Parse integer JSON losslessly.

MP4 sidecar top-level keys are `camera_id/raw_frame_id/frame_id/group_id/group_timestamp_ns/camera_timestamp_ns/exposure`. Its per-camera delivered-time field is named `camera_timestamp_ns`, unlike `timestamp_ns` in ROS2 JSON. Check `exposure.status` before using `duration_ns`; do not use `source_timestamp` to align Unix time.

(manual-exposure)=
### Startup-only Manual Exposure Configuration

Non-ROS `sensor_demo` accepts boolean `camera.auto_exposure`, default `true`, and integer microseconds `camera.exposure_time_us`, default `2000`, with valid input `1..4294967295`. Zero, negatives, fractions, overflow, trailing text, and invalid booleans are rejected before startup. Auto mode ignores the duration without rewriting the SDK tuning's automatic-exposure policy. Manual mode selects ISP `HBN_ISP_MODE_MANUAL` for each enabled camera, sets SDK seconds to `exposure_time_us / 1000000`, and fixes analog, sensor digital, and ISP gains to `1x` for repeatable calibration. The SDK/profile limits the usable range: SDK rejection fails startup without silent fallback to auto.

The library reads `SC132_AUTO_EXPOSURE=1|0` and decimal `SC132_EXPOSURE_TIME_US` once at each `sc132_start_frame_set()` startup, defaulting to `1` / `2000` when unset. `sensor_demo` always writes explicit or default YAML options into the environment, overriding inherited values; omitting YAML keys does not preserve environment control. Settings are startup-only: stop and restart after changes, and rebuild both the application and a supporting library. See the {ref}`non-ROS YAML Configuration <non-ros-yaml>` for examples.

Manual parameters are set after camera flow starts successfully and before the worker is ready. Each camera discards `3` transition frames even when normal warmup is disabled. This does not certify applied-parameter identity for subsequent frames; per-frame `exposure` retains the estimate contract above. Bag `/robobaton/session_config` fields `auto_exposure` / `exposure_time_us` record requested values, not measured exposure. The feature is independent of `camera.test_exposure_midpoint`, changes neither timestamp formulas, the C ABI, nor SONAME, and makes no physical exposure-midpoint claim. No board deployment or verification has been performed.

(test-exposure-midpoint)=
### Exposure-Midpoint Timestamp Test Switch

Only `libsc132.so` rebuilt from current source supports `SC132_TEST_EXPOSURE_MIDPOINT`; existing delivered binaries are not updated automatically. Disabled by default; set `1` before startup to enable, or set `0`/unset it to restore the original logic. No C ABI, SONAME, or software-version change.

```bash
SC132_TEST_EXPOSURE_MIDPOINT=1 ./cam_demo
SC132_TEST_EXPOSURE_MIDPOINT=0 ./cam_demo
```

Read once at each `sc132_start_frame_set()` startup, never toggled during acquisition. Unset, empty, or `0/false/FALSE/off/OFF/no/NO` disables it; any other nonempty value enables it. Stop and restart the process/acquisition after changing the environment; ROS2 must pass the variable to the node or launch process.

The non-ROS combined entry `sensor_demo` also accepts `camera.test_exposure_midpoint: true|false` in `config/sensor_config.yaml`; packaged and auto-generated configurations default to `false`. Explicit YAML overrides the environment; only an omitted key preserves environment control. Rebuild `sensor_demo` and a supporting library, and restart after configuration changes. `cam_demo` does not read this YAML; ROS2 still uses the environment variable. See {ref}`non-ROS YAML Configuration <non-ros-yaml>`.

When enabled, each `timestamp_ns = realtime trigger time + floor(exposure.duration_ns / 2)`, using the predecessor getter estimate matched to the target image by the raw-hardware-frame adjacency rule above. It ignores trigger-to-integration-start delay and never substitutes host now, arrival time, or opaque source time. Frame info and frame-set items agree; group time is the minimum adjusted channel timestamp. Non-ROS saving/RTSP, ROS2 Image/CameraInfo, and exposure messages use these values and forward exposure unchanged; consumers must neither shift another frame nor add half exposure a second time. Unavailable exposure, zero duration, or addition overflow stops acquisition rather than silently reverting to trigger time.

Group admission and `max_skew_ns` still use original trigger RAW; reserved RAW/generation/uncertainty are not shifted. Thus test-mode group time and RAW audit time intentionally describe different events. This is only an exposure-midpoint estimate without delay compensation, not a guarantee of applied exposure, error bounds, or hardware synchronization accuracy.


## IMU

The public library requires the matching **kernel IIO V4 capture module** already bound to the device. An existing V2/V3 capture module is incompatible, including in host mode; rebuilding/deploying applications alone does not upgrade it. Enumerate the unique instance named `icm42670-capture`, validate its scan layout, and BIND its matching control node. Never assume an `iio:deviceN` number. Both timestamp modes use the same IIO reads and kernel SPI/INT1 owner, in the same binary. The library neither loads modules nor changes the device tree, and has no userspace SPI/spidev or automatic fallback backend.

| Item | Contract |
|---|---|
| ABI | `6.0`; real file `libicm42670.so.6.0.0`, SONAME `libicm42670.so.6`, all nine exports versioned `ICM42670_X5_6.0`; rebuild every consumer with matching headers/libraries |
| Native ODR | `25/50/100/200/400/800/1600Hz`, default `800Hz`; reject other values without resampling |
| FIFO watermark | Fixed at `1` |
| Buffer capacity | Default `buffer_capacity=4096`; power of two in `256..8192` only |
| Invalid six-axis payload policy | Default `allow-counted` counts and continues; `strict` fails on invalid payloads. Not a timestamp-precision policy |
| Timestamp mode | Startup-only `timestamp_mode`: `ICM42670_TIMESTAMP_MODE_HOST=0` (default) or `ICM42670_TIMESTAMP_MODE_TMST=1`; app `imu_timestamp_mode` accepts `host` or `tmst` |
| FSYNC diagnostics | `fsync_diagnostics=1` enables by default; 0 disables. Startup configuration never changes ordinary host/tmst time |

| Field | Units and semantics |
|---|---|
| `session_generation` / `sample_sequence` | Session identity and FIFO packet sequence; use sequence for order and never mix sessions |
| `sample_monotonic_ns` | Kernel-assigned `CLOCK_MONOTONIC` host estimate, retained unchanged in both modes; not Unix time or a measured physical sampling edge |
| `observation_monotonic_ns` | Host observation in the same MONOTONIC domain; its difference from sample time is not certified physical sampling latency |
| `estimated_period_ns` | Host-estimated period, not a measured chip timestamp |
| `evidence_id` / `burst_flags` | In-session burst identity; bit `1` denotes an ordinary successful burst, bit `2` a STOP tail |
| `burst_complete_raw_ns` | Separate `CLOCK_MONOTONIC_RAW` burst-completion observation; shared within a burst. Never subtract it directly from MONOTONIC fields |
| `timestamp_source` | `1=IRQ`, `2=SERVICE`; SERVICE identifies a service-time estimate without IRQ, not a hardware sampling edge |
| `packet_flags` | Low three bits are accel/gyro/temperature valid (`1/2/4`) |
| `temperature_c` / `accel_mps2[3]` / `gyro_rps[3]` | Celsius, `m/s^2`, `rad/s`; `raw` retains original six-axis/temperature values |
| `timestamp_mode` | Numeric mode `0=HOST`, `1=TMST` in the C sample; output JSON/CSV uses `host`/`tmst` |
| `fifo_tmst` | Raw FIFO field low16, zero-extended into u32; tagged packets carry FSYNC delta microseconds, not an absolute tick, unwrapped timestamp, or Unix time |
| `sample_raw_ns` | `0` in host mode; in tmst mode, userspace-unwrapped FIFO TMST mapped to `CLOCK_MONOTONIC_RAW` using kernel-owned FIFO/UI transition evidence |
| `timestamp_uncertainty_ns` | `UINT32_MAX` (unknown) in host mode; tmst computational mapping-admission bound in ns, not a physical sampling-accuracy certificate |
| `fifo_header` | Raw FIFO header byte zero-extended into u32 |
| `fsync_flags` | Bits `ICM42670_FSYNC_ENABLED=1`, `ICM42670_FSYNC_TAGGED=2`, `ICM42670_FSYNC_TIME_VALID=4`, `ICM42670_FSYNC_UNRESOLVED=8` |
| `fsync_sequence` / `fsync_delta_us` | Sequence advances only for real tags; both fields are 0 on ordinary packets. Delta is the raw tag interval in microseconds |
| `fsync_raw_ns` / `fsync_uncertainty_ns` | Independent diagnostic-edge `CLOCK_MONOTONIC_RAW` value and uncertainty in ns; 0/`UINT32_MAX` without a valid edge. Host `sample_raw_ns` remains 0 |

Host mode preserves the kernel MONOTONIC estimate without a physical-error bound. TMST mode uses kernel-owned FIFO TMST and bounded UI transition observations; userspace unwraps the counter and performs bounded affine mapping to RAW. Missing, contradictory, stale, ambiguous, or out-of-budget timing evidence fails rather than falling back to host or nominal-ODR time. The `200µs` sample-mapping admission is computational, not measured physical accuracy. It does not provide trigger-to-sample association, or userspace SPI.

### Web Attitude Preview Inputs

`GET /api/v1/info` retains the software `version` and application-session identity. The current Web service reports `web_implementation: "rust"`, `webrtc_stack: "str0m"`, and `webrtc_version: "0.24.1"`. Read the WebRTC version from `webrtc_version`; the former Go/Pion `pion_version` field is no longer provided. These implementation fields do not change the software version or SO ABI.

The `sensor_demo` IMU SSE uses **`schema_version: 2`**, without legacy `sample_timestamp_ns` / `host_timestamp_ns` aliases. SSE `session_id` matches `/api/v1/info.application_session_id` as the application-session identity; `source_generation` identifies the producer session, and `sample_sequence` is the native sample sequence. There is no SSE field named `sequence`. Every u64 field is a decimal string to avoid JavaScript precision loss.

Explicit time fields are `sample_realtime_ns`, `sample_monotonic_ns`, `sample_raw_ns`, `observation_monotonic_ns`, `burst_complete_raw_ns`, and `estimated_period_ns`. `timestamp_mode` is `host` or `tmst`; host `timestamp_uncertainty_ns` is JSON `null` (no error bound), while tmst reports computational mapping admission. Retain `source_generation`, `evidence_id`, `burst_flags`, `packet_flags`, `timestamp_source`, `fifo_tmst`, and `bridge_monotonic_ns`, `bridge_raw_ns`, `bridge_realtime_ns`, `bridge_uncertainty_ns`. Never subtract directly across RAW/MONOTONIC. ABI6 exposes no per-sample GPIO/mapper counters; SSE neither fabricates zeros nor retains those fields.

Three-element `attitude_accel_mps2` (`m/s²`) and `attitude_gyro_rps` (`rad/s`) arrays remain browser-attitude inputs only. Raw `accel_mps2` / `gyro_rps`, values/traces, native sampling, and saving are unchanged. Attitude integration and continuity use selected native sample time: MONOTONIC in host, RAW in tmst, never realtime, so wall-clock adjustments cannot contaminate integration.

The device processes all six axes at every native sample through four cascaded one-pole low-pass stages before extracting telemetry. Each pole is `min(10Hz, telemetry limit×0.2, source rate×0.2)`, with about 64ms low-frequency group delay at the default 800→50Hz. The timestamp identifies the current input sample, not a delay-compensated measurement or a single raw observation. Invalid input produces JSON `null` attitude-array elements. Non-increasing timestamps, a sequence reset, or native-sample gaps over 100ms reseed history without synthesizing missing samples. Filtering estimates neither attitude nor bias; the browser independently fuses inputs and uses raw axes for stationary-quality checks. Absolute heading and removal of vibration-rectification error are not guaranteed.

The public library and standalone `icm42670_reader`/`imu_reader_demo` never convert to Unix time. Both modes preserve native MONOTONIC; tmst additionally supplies RAW sample time and uncertainty. `IMU_TIMING_SUMMARY` separates `timestamp_hz` (host-assigned MONOTONIC span, even in tmst mode) from `acquisition_hz` (independent RAW endpoints of ordinary non-STOP bursts and each endpoint's last packet sequence). The latter requires `acquisition_valid=yes` and at least two ordinary bursts. Neither rate alone proves physical sampling accuracy or completeness.

### Output Realtime Bridge and Timing Metadata

The `sensor_demo` saving and ROS2 output adapters select native sample time by mode: host uses `sample_monotonic_ns` with MONOTONIC→REALTIME; tmst uses `sample_raw_ns` with RAW→REALTIME. One bridge is observed for each new `(session_generation,evidence_id,timestamp_mode)` and reused within that burst; original MONOTONIC host fields and RAW burst observations are never rewritten. The bridge tries at most three times, rejecting an observation whose selected native-clock bracket exceeds `200000ns`; failure of all attempts fails output. `bridge_uncertainty_ns` is the bracket half-width rounded up, separate from the tmst sample-mapping admission and not physical sampling precision or a camera/IMU synchronization bound. Backward wall-clock steps remain visible in subsequent bursts without a monotonic clamp.

Bag `/imu/data` and ROS2 IMU/Temperature `Header.stamp` use the explicitly converted realtime. Bag `/robobaton/imu/timing` (`std_msgs/String`) and the same ROS2 topic (`std_msgs/msg/String`, Reliable KeepLast(256)) retain per-sample `robobaton_imu_timing_v3` JSON:

- Clock declarations: `sample_clock` and `bridge_clock` are `CLOCK_MONOTONIC` for host, `CLOCK_MONOTONIC_RAW` for tmst; `output_clock=CLOCK_REALTIME`, `burst_complete_clock=CLOCK_MONOTONIC_RAW`;
- Identity: `generation`, `sample_sequence`, `evidence_id`, `burst_flags`;
- Times and origin: `sample_monotonic_ns`, `sample_realtime_ns`, `burst_complete_raw_ns`, `observation_monotonic_ns`, `estimated_period_ns`, `timestamp_source`, `packet_flags`, plus `timestamp_mode` (`host`/`tmst`), `fifo_tmst`, `sample_raw_ns`, and `timestamp_uncertainty_ns`; Independent FSYNC diagnostics: `fifo_header,fsync_flags,fsync_sequence,fsync_raw_ns,fsync_uncertainty_ns,fsync_delta_us`;
- Bridge observations: `bridge_monotonic_ns` (host only; zero for tmst), `bridge_raw_ns` (tmst only; zero for host), `bridge_realtime_ns`, `bridge_uncertainty_ns`. Never relabel a RAW bridge base as MONOTONIC or subtract across clocks.

MP4 `imu.csv` uses output realtime in `sample_realtime_ns`, retaining native times, identity, burst, origin, bridge bases/half-width, temperature, and raw six-axis columns (generation is named `session_generation`). Its additional selector fields are `timestamp_mode,fifo_tmst,sample_raw_ns,timestamp_uncertainty_ns,bridge_clock,bridge_raw_ns`. Host retains RAW sample zero and unknown sample uncertainty; tmst retains the original MONOTONIC estimate separately. Independent FSYNC diagnostics default on and can be disabled; no separate FSYNC topic, sidecar, callback, trigger-to-sample association, or `200µs` physical precision guarantee exists. Exposure observations and the exposure-midpoint test switch remain available with either camera path; official uncertainty remains unknown. A common Unix epoch does not establish physical synchronization. FSYNC diagnostic columns are `fifo_header,fsync_flags,fsync_sequence,fsync_raw_ns,fsync_uncertainty_ns,fsync_delta_us`; they never correct host/tmst, camera-frame, or group time, and never use nearest-neighbor matching.

Parse JSON timestamps and sequences losslessly as integers. Epoch nanoseconds exceed IEEE-754's safe integer range; ordinary JavaScript `JSON.parse` rounds them, so use a lossless integer parser.

### STOP, ACK, and Final Health

The serial acquisition worker invokes callbacks with a sample borrowed until return. Callbacks must not throw or call stop/destroy; `user_data` must remain alive until stop returns. STOP keeps callback admission open, drains the complete stop cohort, then joins. Asynchronous consumers must drain concurrently, not close admission first. `--count N` is a STOP-request threshold: final counts may exceed N and do not truncate the cohort. A record is ACKed only after all covered samples reach callbacks; repeated stop retains terminal diagnostics.

`icm42670_get_runtime_health` can return obtained terminal diagnostics even after stop reports failure; never replace failed-stop fields with zero and call them healthy. Final health includes `session_generation`, `published_samples`, `consumed_scans`, `records_consumed`, `records_acked`, `last_packet_sequence`, `irq_wakeup_count`, `timer_service_count`, plus `fatal_reason/fatal_errno`, `fifo_overflow_count`, `invalid_payload_count`, `scan_push_failure_count`, `evidence_full_count`, `timestamp_service_burst_count`, `tail_packet_count`, `unknown_hardware_tail`, `quiesce_errno`, and `transport_complete`.

Evaluate stop/health statuses, nonzero generation, terminal errors, counts, sequences, and producer/consumer/actual-payload totals together. `transport_complete=1` certifies only consumption and ACK of the stop cohort, not absence of fatal errors. `unknown_hardware_tail` identifies physical tail data outside the STOP fence, not certified delivery of all physical samples. `allow-counted` is not zero loss; strict is not physical precision. CLI final records use best-effort nonblocking output: a missing summary is not a health pass.

`accel_mps2` is `[X,Y,Z]`. PCB orientation/signs remain unpublished; no main-board/camera transform, TF, or extrinsics is declared. Acquisition uses `SCHED_FIFO/20`, non-ROS consumers/ROS2 IMU publication `SCHED_RR/3`. Scheduling failure rejects startup without automatic system IRQ/debug/realtime-quota changes.

## non-ROS Save Output

| Output | Contract |
|---|---|
| ROS bag | `sensor_demo --record-bag <absolute .bag>` saves four-channel JPEG images, camera parameters, and IMU data; incomplete stress/abnormal runs use an explicit `.partial.bag` recovery file. |
| MP4 session | Four H.264 MP4s, four timestamp CSVs, extended `imu.csv`, input `exposure.jsonl`, `camera_params.yaml`, `session_status.json`, `publication_receipt.json`; no FSYNC file. |
| MP4 path conflict | When the configured final directory or a same-named `.partial` already exists, the actual output automatically switches to the sibling `<name>-YYYYMMDDTHHMMSSZ[-NNNN]`; follow `SENSOR_MP4_RESULT path=`. |
| `.partial` | Keeps the recovery namespace; a `.partial` MP4 session can be extracted for inspection but is not declared complete. |

MP4 requires H.264, full mask0x0f, and no simultaneous bag/frame-skip. Image CSV joins `frame_index` to microsecond-quantized realtime group times. Match exposure input observations by camera/group time, not source-frame identity as encoded index. A complete source also requires matching publication receipt and four MP4/CSV pairs.

Bag payload stamps are separate from record time: image and first-frame CameraInfo `header.stamp` preserve realtime camera captures; IMU payloads retain realtime sample stamps. Bag record time independently reads `CLOCK_REALTIME` at writing, not sampling. Backward clock steps are preserved rather than clamped. Physical write order remains unchanged; each connection's chunk index is time-sorted for ROS bag readers. Session config declares `camera_timestamp_domain`, `imu_timestamp_domain`, and `record_timestamp_domain` all as `"realtime"`.

Bag `/robobaton/session_config` also records startup `camera_timestamp_path` and `imu_timestamp_mode`. Four combinations use one binary and one IIO capture/owner; only the two timestamp axes change. Select them before acquisition as shown in [non-ROS Usage](../usage/non-ros-demo.md) and [ROS2 Usage](../usage/ros2-demo.md).

MP4 CSV indexes use the realtime system timeline, subject to the precision and per-camera distinction above; container playback remains relative/nominal, not Unix epoch. A backward step unsupported by the encoder/container produces an error and incomplete artifacts rather than fabricated increasing times. Complete system-clock synchronization before continuous recording.

Storage completeness is recorder-specific. Bag complete does not independently certify zero producer invalid payloads. Dynamic MP4 uses `imu_health_scope=callback_window`, checking native samples, sequence continuity, counter differences, and queue writes within that callback window. It neither stops the shared producer nor certifies outside-window completeness. A still-active startup-auto session uses `imu_health_scope=producer_session`, checking valid final health after application exit, published=observed=admitted=written>0, scan=published, records=ACK, continuous sequences, and zero fatal/overflow/invalid/push/evidence/quiesce errors. Old mapper/precision fields are removed. Stop-cohort completeness is not all-physical-sample completeness; check exposure coverage separately. See [Saving Data](../usage/save-data-guide.md).

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
| `/robobaton/imu/timing` | `std_msgs/msg/String` | Per-sample `robobaton_imu_timing_v3` native clocks and bridge observations. |

ROS2 QoS:

| Data | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | Follows the raw publisher, also Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
| Exposure | Reliable + KeepLast(8) |
| IMU timing | Reliable + KeepLast(256), active with IMU |
| IMU | `SensorDataQoS`, keep last 100 |
| Temperature | `SensorDataQoS`, keep last 10 |

ROS2 raw `Image.step` uses the underlying DMA buffer's stride; `data.size()` uses the underlying Y/UV buffer size, which may be larger than the compact `width * height * 3 / 2`. Subscribers must not index the UV plane directly under the compact-NV12 assumption.

ROS2 Headers are not publication time. Cameras use the selected realtime trigger estimate (or opt-in exposure-midpoint estimate); IMU/Temperature use the selected per-burst MONOTONIC→REALTIME or RAW→REALTIME bridge. Timing JSON retains native MONOTONIC, independent RAW, mode, identity, and correctly labeled bridge observations. Backward wall-clock steps remain visible; no simulation `/clock` conversion. A common epoch is not physical synchronization.

ROS2 provides no RTSP, TF extrinsics, calibration, or trigger-to-sample association. Prefer compressed for general visualization; RGB/BGR tools may not display NV12 directly.

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
