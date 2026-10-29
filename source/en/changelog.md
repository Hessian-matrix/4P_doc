# Changelog

This file records user-visible updates in the RoboBaton 4P public delivery, following the shared [Documentation Version Policy](release-and-support.md#documentation-version-policy). Documentation revisions on this page do not automatically change software versions and are distinct from SO SONAME/ABI versions.

## Unreleased

The following updates are implemented in current source but have not been released as a new software version. This documentation revision does not turn them into a software release or system acceptance. Current scope and unresolved limits are centralized in {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

### Improvements and Fixes

- Added standalone `can_demo`: classical CAN by default, explicit `--fd` for up-to-64-byte FD transmission and mixed classical/FD reception, and `--brs` for TX data-phase bit-rate switching, with standard/extended IDs. FD transmission accepts exactly encodable lengths without implicit padding. Integrated into builds, full runtime packaging, and verification. Users/BSP still configure the interface; application support does not replace BSP long-payload integrity acceptance, and local loopback or queued sends do not constitute external-bus acceptance.
- Camera, IMU, CLI, saving, and ROS2 public sensor timestamps now use `CLOCK_REALTIME` system time. Bounded VSYNC cross-sampling and the same-counter trigger delta reconstruct camera hardware trigger edges, without IRQ/arrival-time fallbacks; missing valid mappings stop acquisition.
- RAW remains internal to mapping/grouping. Sensor sample/trigger publication refreshes realtime bridges and follows backward clock steps; IMU host time instead retains the original burst-completion observation without rebridging at deferred publication. Bag record time independently reads realtime without a monotonic clamp; chunk indexes are time-sorted. A common domain does not establish hardware sample/exposure synchronization. Consumers of old time semantics must migrate headers, SOs, and applications together.
- Added opt-in LPWM-to-ICM-42670-P FSYNC trigger-to-sample association: hardware FIFO tags, bounded reconstruction from adjacent absolute TMSTs, unique RAW candidate matching, and missing/ambiguous statuses. Non-ROS `--fsync` and YAML/ROS2 `imu.fsync_enabled` default off and support only `800/1600Hz`; the `200µs` admission policy remains, without guaranteeing every trigger or exposure synchronization. Results reach stdout, bag `/robobaton/fsync`, MP4 `fsync.jsonl`, and the same ROS2 topic.
- Current ICM ABI is `3.0`: every export, including the FSYNC callback, uses only `ICM42670_X5_3.0`, with real file `libicm42670.so.3.0.0` and SONAME `libicm42670.so.3`. Field layouts remain unchanged, but host-time semantics are incompatible. Rebuild all consumers and remove old `.2` artifacts, without old symbol aliases or cross-major shims. Camera frame-set reserved fields carry RAW trigger, group uncertainty, and generation; public time remains realtime.
- Association records retain original per-camera realtime stamps for exact joins with ROS2 Image/CameraInfo; integer JSON requires lossless parsing. MP4 timestamp CSV contains microsecond-quantized group-trigger times expressed in ns; original per-camera values are in opt-in `fsync.jsonl`, not the CSV.
- Fixed acquisition blocking through cross-priority queue locks. IMU consumers/ROS2 publication use explicit realtime scheduling, SPI uses `10MHz`, and INT1 uses a `100µs` asynchronous-reset pulse. Failed starts release resources; final health snapshots retain trailing invalid-FIFO-packet counts. Phase, unique-match, and `200µs` checks remain; high-load results still depend on system IRQ/debug and subscriber scheduling, without guaranteeing every trigger or zero loss under arbitrary load.
- Final IMU health records include timing-drop and FSYNC captured/dropped totals. Non-ROS terminal summaries use post-stop counters, and invalid FIFO packets remain counted when timing rejection overlaps.
- FIFO order, measured TMST, and FSYNC tags/deltas now lead IMU acquisition. INT1 is wake-only: GPIO edge-time conversion, per-packet edge pairing, and the independent INT1 clock observer are removed. Bounded waits still check FIFO without notifications. Detectable missing notification sequence values are diagnostic, not proof of physical-edge/sample loss or independently fatal. FIFO overflow, bad packets, ambiguous clocks, and invalid epochs still fail; the `200µs` admission gate is unchanged.
- FIFO startup bounds measured Arm-to-enable completion by the shortest legal ODR interval. Late enable rejects startup rather than aliasing a whole TMST wrap; neither GPIO nor nominal ODR fabricates time.
- Camera ABI 3.0 includes frozen per-frame ISP exposure observations and frame-info prefix-size reads, with SONAME `libsc132.so.3`. Bag/tee metadata, MP4 `exposure.jsonl`, and ROS2 `/robobaton/camN/exposure` carry estimates separately from unavailable values, without certifying applied-frame identity, an error bound, or actual exposure midpoint; default trigger stamps remain unchanged. The capture observer inherits the allowed CPU mask rather than forcing CPU0.
- Fixed an unreleased MCLK reference acquired during sensor probing: release it before VIN takes ownership without clearing historical references. Camera capture uses FIFO/60 and handles in-scan VSYNC transitions. IMU fitting constrains read intervals, and overwide observations cannot poison unwrapping. The camera `500µs` and IMU `200µs` gates remain unchanged; high load can still cause explicit rejection or acquisition failure.
- IMU interval observations that contradict the retained clock certificate now invalidate it before further publication; overwide observations remain individually rejected. Fixed a bag shutdown race that mistook a final encoded frame arriving after prefetch for an order gap; real gaps still fail. Realtime threads remain subject to system scheduling and IRQ latency; system realtime quotas are unchanged, without a zero-loss guarantee under arbitrary load.
- Camera adds default-off `SC132_TEST_EXPOSURE_MIDPOINT`: test timestamps use trigger time plus half exposure duration, ignoring trigger-to-integration-start delay; unavailable exposure stops acquisition. Group admission, trigger skew, and FSYNC RAW audit remain unchanged; disabling restores original logic. Requires a current-source library rebuild, not a software release or hardware acceptance claim.
- UART RX waits now exit normally on `SIGINT`/`SIGTERM` and restore the original serial settings. Other signals do not extend the RX deadline; genuine I/O errors remain failures.
- With ROS2 rate metrics disabled, final IMU sink publication count is explicitly `unavailable` / `imu_publish_count_valid=no`; enabled metrics retain the actual successful `publish()` count. Producer, sink, and DDS reception counts remain distinct; producer counts do not substitute for an unmeasured sink count.
- ROS2 FastDDS SHM profile now reserves `256 MiB` per participant, leaving capacity headroom for three processes. Each extra daemon/CLI/subscriber process still counts separately; this does not establish that all historical SHM initialization errors are resolved.
- Native bag X5 hardware JPEG omits only the length-4 APP9 immediately after SOI containing a private frameIdx, preserving other APP markers and coded payload to avoid generic-decoder APP structure warnings. The ROS2 JPEG plugin output contract is unchanged.
- `rosbag_info.py --freq` explicitly identifies its bag record-time basis; new `--header-freq` separately reports saved IMU/CompressedImage/CameraInfo `Header.stamp` rates. Batched-write frequency is not sensor sampling rate or proof of losslessness.
- ROS1 bag overload now selects candidates with a strict default minimum drop interval of 10 consecutive frame-set arrival ordinals, not sparse producer IDs; all cameras share each retain/evict decision. If neither an old nor incoming group can legally be dropped, recording explicitly stops, drains to a partial bag, and exits nonzero. Bag metadata and final status expose ordinals, intervals, and the reason; source/IMU losses are outside this guarantee. Intentional alternate saving explicitly requires interval 2.
- Fixed premature IMU admission closure on strict bag image stops and ROS2 callback rejection before producer shutdown completes. Normal finalization keeps IMU input open until acquisition is quiescent, then drains queues. On SIGINT/SIGTERM, ROS2 cleans up the node while its context remains valid and shuts down the context last. A normal `publish()` return is not DDS receipt, nor a zero-loss guarantee under arbitrary load.

## 2.0.15 - 2026-10-29

- Align bag and ROS2 stop, admission, and drain contracts; distinguish fixed shutdown defects from the historical DDS difference that still cannot be exactly attributed.
- Software remains `2.0.0`, with unchanged SO ABIs. Short smoke runs do not replace sustained-pressure, high-frame-rate, long-recording, or release acceptance.

## 2.0.14 - 2026-10-29

This revision synchronizes public documentation in both languages only. Software remains `2.0.0`; it changes no software behavior, releases no new software, and establishes no additional hardware, load, or long-duration acceptance.

### Documentation Synchronization

- Centralize accepted parameters, independent software/hardware/documentation/SO ABI versions, and verification boundaries on the support page. Align complete rebuild and migration requirements for ICM42670/SC132 ABI `3.0` and PRRTSP ABI `2.0`.
- Align FIFO/TMST, wake-only INT1, original burst host observations, backward realtime steps, default trigger stamps and explicit exposure-midpoint test mode, plus FSYNC, exposure, and realtime-scheduling contracts.
- Synchronize strict bag drop spacing, partial stops, producer/sink/DDS count distinctions, and JPEG/record-time semantics. High frame rate, pressure recording, and the current composition's `8h` recording do not establish complete acceptance; historical results cannot certify this composition.
- Add user-facing LPWM, RTSP, SHM, USB, CAN, RTC/UTC, and runtime-dependency limits. Retain TF hardware repair and single-camera diagnostics as user-confirmed without generalizing to every environment.


## 2.0.13 - 2026-10-23

Record bag overload fixes and the added FIFO/TMST-led IMU ABI 3.0 migration. Documentation revision and software VERSION remain unchanged; IMU SONAME/ABI independently move for the incompatible semantics described below.

### Improvements and Fixes

- At image-burst or IMU high-water service points, the bag writer drains a snapshot of the current IMU backlog in bounded batches. Later arrivals wait for the next round, preventing a growing high-ODR deficit or indefinite image starvation. Queue capacities are unchanged; unbounded storage stalls can still lose data.
- Repeated oldest-complete-group replacement retires head eviction markers and checks the full committed record-order window before eviction. A claimed group's remaining frames stay protected; unready groups are not bypassed and ring slots are not overwritten. Evictions/rejections remain counted partial data. The bag fixes themselves change neither LPWM nor uncertainty checks; see below for the IMU architecture cutover.
- Clarify bag queue/writer-latency diagnostics and system-wide disk counters. Aggregate counters are not saving-device utilization or proof of payload completeness.
- IMU moves to ABI `3.0`, real file `libicm42670.so.3.0.0`, SONAME `.3`, and only `ICM42670_X5_3.0` for every current export. Field names/layouts remain unchanged; no old aliases, reexports, or compatibility shims exist. Synchronize headers, libraries, and every rebuilt consumer, remove old `.2` artifacts, and never substitute a lone SO or cross-major link.
- FIFO order and measured chip TMST define samples; FSYNC retains chip tags/deltas and measured endpoints, while INT1 only wakes acquisition. `host_timestamp_ns` becomes the RAW observation at the successful SPI FIFO burst completion, converted to realtime using that observation's bridge. Packets may share it; FSYNC deferral retains the converted value, it may precede publication, and it follows wall-clock steps. It is not IRQ-edge, sample, or exposure time. `sample_timestamp_ns` remains measured TMST-to-RAW-to-realtime, with unchanged `200µs` admission.
- GPIO notification sequence gaps are diagnostic, not proof of physical-edge/sample loss or independently fatal. Actual FIFO overflow, bad packets, ambiguous clocks, and invalid epochs still fail. This architecture changes neither LPWM nor kernel and does not fix the underlying GPIO/IRQ cause or guarantee zero loss under arbitrary load. Rebuild, synchronize, and repeat target-board acceptance; software version strings are not passing evidence.

## 2.0.12 - 2026-10-23

Clarify acquisition-latency troubleshooting conditions. Software versions and SO SONAME/ABI are unchanged.

### Improvements and Fixes

- Explain BSP per-transfer spidev dynamic-debug versus application logging, authorization for comparison experiments, and restoration of original flags. Passing with debug disabled is not a pass in the original environment; FIFO/INT1 identity, the `500µs`/`200µs` gates, and fail-closed behavior remain unchanged.
- Normal first FIFO packets also reject nonexistent fractional phases after Arm without consuming GPIO identity. GPIO event-gap detection remains active after the sequence wraps to zero. Both FSYNC modes retain the same timestamp and uncertainty gates.
- Fixed concurrent mutable-metadata access between a frame-set producer and group finalization. Internal dumps use the raw frame counter and RAW capture time; public consumers retain normalized frame IDs and the realtime timestamp contract.
- Arm uses only measured clock transitions accepted by the mapper. An incompatible bounded observation invalidates the old clock certificate instead of combining a new counter with a stale mapping. The `200µs` gate remains unchanged; neither nominal ODR nor arrival time replaces measured timestamps.

## 2.0.11 - 2026-10-22

Document acquisition-startup fixes. Software versions and SO SONAME/ABI are unchanged.

### Improvements and Fixes

- Frame-set warmup now discards unpublished frames before clock-map admission, exposure queries, and image transforms, avoiding startup failure on an unavailable first-frame capture map. Delivered frames still require exact capture matches with the unchanged `500µs` window limit.
- Retain leading FSYNC packets until a later absolute TMST arrives, then reconstruct bounded intervals using the measured startup clock transition instead of failing solely because no preceding FIFO endpoint exists. No nominal-ODR timestamps are synthesized; GPIO identity, unique rollover, the `200µs` limit, and drop policies remain unchanged.
- LPWM fatal diagnostics distinguish a rejected exact record from an absent trigger and snapshot that lookup's counter values, RAW bracket, and history endpoints. Timestamps, bounds, ABI, and fail-closed behavior are unchanged; this does not claim a sustained-acquisition fix.
- Fixed an uninitialized frame-set release risk when realtime bridging or exposure-midpoint validation fails. Clear the output descriptor before validation, preserving pending-frame ownership without delivering a partial group.
- Startup reconstruction checks the shared-Arm and one-full-ODR-later hypotheses separately, accepting only a unique feasible hypothesis and rejecting nonexistent fractional phases between them. Document sustained FIFO/INT1 identity failures and fail-closed boundaries; repeated-start success is not a sustained-stability guarantee.

## 2.0.10 - 2026-10-22

Add bilingual instructions for TF cards as data disks. Software versions and SO ABI are unchanged; this is not new hardware or card-compatibility acceptance.

### Improvements and Fixes

- Document TF (microSD) versus system eMMC identification, filesystem selection, manual mounting, acquisition output paths, normal unmounting, and enumeration troubleshooting. Check SD type and mount device number before saving to avoid writing into RAM or the system disk after a failed mount. No automatic formatting, mounting, or hot-plug safety claim.

## 2.0.9 - 2026-10-22

This revision aligns both public language trees with the current V2 product. Software remains `2.0.0`; SO versions and ABI are unchanged, without a new hardware-acceptance claim.

### Improvements and Fixes

- Remove obsolete product-version history, download instructions, main-board and UART photographs, and flashing screenshots; retain applicable camera dimensions and the RTSP playback example.
- Replace migration comparisons with current V2 interface, data, and runtime-library contracts. Preserve UART logic levels, pending complete pin order and power ratings, power-off wiring, and hot-plug safety boundaries.

## 2.0.8 - 2026-10-22

Document independent SO revisions and the incompatible camera migration. Software remains `2.0.0`, without a new hardware-acceptance claim.

### Improvements and Fixes

- ICM42670 real SO is `2.1.0` (SONAME `2`), SC132 is `3.0.0` (SONAME `3`, `LIBSC132_3.0`, public ABI `3.0`), and PRRTSP is `2.0.1` (SONAME `2`). Align producers, consumers, packaging, and verification. Old camera consumers must be rebuilt; never link `.so.2` to `.so.3`. Each family retains one real file and two relative links.
- Incremental ROS2 installs remove obsolete revisions and majors of the same producer family; the verifier rejects extra libraries, dangling old links, and cross-major compatibility aliases. The staged ICM C link probe consumes both `ICM42670_X5_2.0` and `ICM42670_X5_2.1`, rather than treating producer version definitions as consumer version needs.

## 2.0.7 - 2026-10-22

This revision documents canonical shared-library chains and link-preserving delivery in both languages. Software versions and SO ABI are unchanged; this is not new board-level functional acceptance.

### Improvements and Fixes

- Producer synchronization, non-ROS packages, and ROS2 installs retain one real library with exact relative links instead of flattening `.so`/`.so.2` aliases into duplicate files. Document link-preserving archives/copies, metadata versus byte verification, and the requirement to regenerate non-ROS v3 provenance packages.

## 2.0.6 - 2026-10-22

Synchronize bilingual instructions for the image-provided Wi-Fi command and dedicated boot restore. Software versions and SO ABI are unchanged; no cold-boot acceptance claim for a newly flashed image.

### Improvements and Fixes

- Use the `wifi_setup` system command, dedicated boot entry, and persistent opt-in marker instead of the shared application startup file; document static Ethernet carrier-down routing, image dependencies, credential permissions, and acceptance boundaries.

## 2.0.5 - 2026-10-21

This revision documents YAML configuration for the non-ROS exposure-midpoint test switch. Software versions and SO ABI are unchanged.

### Improvements and Fixes

- Non-ROS `sensor_demo` adds YAML `camera.test_exposure_midpoint`, default off in packaged and auto-generated configurations, with explicit YAML taking precedence over the environment. Document estimated midpoints, ROS1 bag image stamps, and rebuild/restart requirements.

## 2.0.4 - 2026-10-21

This bilingual documentation revision covers the exposure-midpoint test switch. Software versions and SO ABI are unchanged; no calibrated-exposure-midpoint or hardware acceptance claim.

### Improvements and Fixes

- Synchronize bilingual usage, default-off behavior, estimated midpoint formula, failure boundaries, and group/per-camera timestamp semantics for the test switch.

## 2.0.3 - 2026-10-21

This revision completes the bilingual API reference for public image output structures. Documentation only; software versions, SO ABI, and hardware acceptance scope are unchanged.

### Improvements and Fixes

- Complete per-frame, frame-group, and exposure fields, units, sequence/time semantics, NV12 padding, reference lifetime, and ROS2/encoded-output differences; add a direct link from Data Contracts.

## 2.0.2 - 2026-10-20

This revision adds bilingual CAN usage documentation. Software remains `2.0.0`; this does not declare CAN hardware or system acceptance.

### Improvements and Fixes

- Add CAN wiring prerequisites, manual interface setup, transmit/receive commands, options, build, and deployment entries.

## 2.0.1 - 2026-10-20

Documentation-only synchronization with current source; software remains `2.0.0`. The unreleased changes above do not become a software release or system acceptance through this documentation revision.

### Improvements and Fixes

- Align realtime timestamps, opt-in FSYNC, camera ABI 2.2 exposure observations, and IMU ABI 2.1; complete configuration, topic, and saved-sidecar entry points.
- Distinguish ISP exposure estimates, trigger-to-sample association, storage completeness, and actual DDS delivery; document realtime permissions, final health counters, and high-load rejection boundaries.
- Correct MP4/bag frame-rate completeness guarantees, the exposure-accuracy interpretation of `max_skew_ns`, and timestamp checks during backward clock steps.

## 2.0.0 - 2026-10-15

V2.0.0 release: software and documentation versions unified to 2.0.0, with default trigger mode switched to LPWM.

### Improvements and Fixes

- All camera acquisition entries support only `vin_lpwm` (VIN LPWM hardware triggering); software GPIO and free-run paths are removed.
- Camera timestamps preserve frame-propagated `trig_tv` trigger captures in the native SIF counter domain, not RAW/UTC. Sharing the camera/IMU wire does not establish sample/exposure association.
- V2 images are explicitly unreleased. Independent PPS IO defaults on without UART7 RX/TX multiplexing. Camera mapping, FOV, factory networking, and UART levels follow their corresponding usage guides.
- The PTP master PHC uses the PTP/TAI time scale; `phc2sys -w` follows the UTC offset from `ptp4l` instead of using `-O 0`. Hardware `hwts_filter full` lets the master receive Delay_Req timestamps and return Delay_Resp. Passing master/packet checks does not establish slave lock or absolute UTC accuracy.
- Bags use a separate, nondecreasing common recording clock. Images and CameraInfo retain camera capture times; IMU messages retain sample times. Session configuration declares the three domains separately, preventing cross-domain numeric comparisons from corrupting record order. Missing LPWM captures produce at most one terminal callback, serialized by the dispatcher, with callback-side stop requests supported.
