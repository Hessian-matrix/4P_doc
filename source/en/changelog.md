# Changelog

This file records user-visible updates in the RoboBaton 4P public delivery, following the shared [Documentation Version Policy](release-and-support.md#documentation-version-policy). Documentation revisions on this page do not automatically change software versions and are distinct from SO SONAME/ABI versions.

## Unreleased

- Camera, IMU, CLI, saving, and ROS2 public sensor timestamps now use `CLOCK_REALTIME` system time. Bounded VSYNC cross-sampling and the same-counter trigger delta reconstruct camera hardware trigger edges, without IRQ/arrival-time fallbacks; missing valid mappings stop acquisition.
- RAW remains internal to mapping/grouping. Realtime bridges refresh at publication and follow backward system-clock steps. Bag record time independently reads realtime without a monotonic clamp; chunk indexes are time-sorted. A common domain does not establish camera/IMU hardware sample/exposure synchronization. Consumers of old SIF/RAW times must migrate headers, SOs, and applications together.
- Added opt-in LPWM-to-ICM-42670-P FSYNC trigger-to-sample association: hardware FIFO tags, bounded reconstruction from adjacent absolute TMSTs, unique RAW candidate matching, and missing/ambiguous statuses. Non-ROS `--fsync` and YAML/ROS2 `imu.fsync_enabled` default off and support only `800/1600Hz`; the `200µs` admission policy remains, without guaranteeing every trigger or exposure synchronization. Results reach stdout, bag `/robobaton/fsync`, MP4 `fsync.jsonl`, and the same ROS2 topic.
- ICM ABI minor is `2.1`: the separate FSYNC callback uses `ICM42670_X5_2.1`; existing function nodes, structure sizes, real SO filename, and SONAME are unchanged. Camera frame-set reserved fields carry RAW trigger, group uncertainty, and generation; public time remains realtime.
- Association records retain original per-camera realtime stamps for exact joins with ROS2 Image/CameraInfo; integer JSON requires lossless parsing. MP4 timestamp CSV contains microsecond-quantized group-trigger times expressed in ns; original per-camera values are in opt-in `fsync.jsonl`, not the CSV.
- Fixed acquisition blocking through cross-priority queue locks. IMU consumers/ROS2 publication use explicit realtime scheduling, SPI uses `10MHz`, and INT1 uses a `100µs` asynchronous-reset pulse. Failed starts release resources; final health snapshots retain trailing invalid-FIFO-packet counts. Phase, unique-match, and `200µs` checks remain; high-load results still depend on system IRQ/debug and subscriber scheduling, without guaranteeing every trigger or zero loss under arbitrary load.
- Final IMU health records include timing-drop and FSYNC captured/dropped totals. Non-ROS terminal summaries use post-stop counters, and invalid FIFO packets remain counted when timing rejection overlaps.
- INT1-to-RAW conversion retains event-time observations and selects certificates by complete bracket-plus-steering uncertainty. An independent realtime observer continues through SPI/callback stalls; startup handshaking and a priority-inheritance lock preserve initialization and history order, without changing phase or publication gates.
- Camera ABI 2.2 adds frozen per-frame ISP exposure observations while preserving old frame-info prefix reads and SONAME. Bag/tee metadata, MP4 `exposure.jsonl`, and ROS2 `/robobaton/camN/exposure` carry estimates separately from unavailable values, without certifying applied-frame identity, an error bound, or actual exposure midpoint; trigger stamps remain unchanged. The capture observer inherits the allowed CPU mask rather than forcing CPU0.
- Fixed an unreleased MCLK reference acquired during sensor probing: release it before VIN takes ownership without clearing historical references. Camera capture uses FIFO/60 and handles in-scan VSYNC transitions; the INT1 observer inherits the CPU mask at FIFO/30 to stay below the default GPIO IRQ. IMU fitting constrains read intervals, overwide observations cannot poison unwrapping, and longer edge-time history is retained. The `500µs`/`200µs` gates remain unchanged; high load can still cause explicit rejection or acquisition failure.
- IMU interval observations that contradict the retained clock certificate now invalidate it before further publication; overwide observations remain individually rejected. Fixed a bag shutdown race that mistook a final encoded frame arriving after prefetch for an order gap; real gaps still fail. Realtime threads remain subject to system scheduling and IRQ latency; system realtime quotas are unchanged, without a zero-loss guarantee under arbitrary load.

## 2.0.1 - 2026-10-20

Documentation-only synchronization with current source; software remains `2.0.0`. The unreleased changes above do not become a software release or system acceptance through this documentation revision.

- Align realtime timestamps, opt-in FSYNC, camera ABI 2.2 exposure observations, and IMU ABI 2.1; complete configuration, topic, and saved-sidecar entry points.
- Distinguish ISP exposure estimates, trigger-to-sample association, storage completeness, and actual DDS delivery; document realtime permissions, final health counters, and high-load rejection boundaries.
- Correct MP4/bag frame-rate completeness guarantees, the exposure-accuracy interpretation of `max_skew_ns`, and timestamp checks during backward clock steps; preserve historical version records.

## 2.0.0 - 2026-10-15

V2.0.0 release: software and documentation versions unified to 2.0.0, with default trigger mode switched to LPWM.

- All camera acquisition entries support only `vin_lpwm` (VIN LPWM hardware triggering); software GPIO and free-run paths are removed.
- Camera timestamps preserve frame-propagated `trig_tv` trigger captures in the native SIF counter domain, not RAW/UTC. Sharing the camera/IMU wire does not establish sample/exposure association.
- V2 images are explicitly unreleased. Remove V1 TF/fan device-tree repairs, ISP parameter replacement, and UART7-to-PPS mux steps; use the default independent PPS IO. Mark old product/interface images for replacement before release. Camera mapping, FOV, factory networking, and UART levels remain unchanged.
- The PTP master PHC uses the PTP/TAI time scale; `phc2sys -w` follows the UTC offset from `ptp4l` instead of using `-O 0`. Hardware `hwts_filter full` lets the master receive Delay_Req timestamps and return Delay_Resp. Passing master/packet checks does not establish slave lock or absolute UTC accuracy.
- Bags use a separate, nondecreasing common recording clock. Images and CameraInfo retain camera capture times; IMU messages retain sample times. Session configuration declares the three domains separately, preventing cross-domain numeric comparisons from corrupting record order. Missing LPWM captures produce at most one terminal callback, serialized by the dispatcher, with callback-side stop requests supported.

## 1.3.3 - 2026-10-11

This bilingual documentation revision covers the V2 hardware migration; software VERSION files are unchanged, and this does not declare full V2 feature or system acceptance.

- Current IMU guides, APIs, and examples move to ICM-42670-P, `icm42670_*`, and `icm42670_driver.h`; real SO `libicm42670.so.2.0.0`, SONAME `libicm42670.so.2`, node `ICM42670_X5_2.0`.
- Native ODRs are `25/50/100/200/400/800/1600Hz`, default `800Hz`; old `500/1000/2000Hz` rates are explicitly rejected and require deliberate configuration migration.
- Camera producer resolves trigger controller `34130000.gpio` offset `0`; INT1 uses `34120000.gpio` offset `8`. Sharing the camera trigger net at IMU FSYNC does not establish camera/IMU hardware alignment.
- Time fields follow the new public header; V2 pinout, electrical limits, physical mapping, IMU direction, and photographs remain pending confirmation. Historical V1 download URLs, artifact identities, and changelog entries below are retained unchanged, not as V2 compatibility or acceptance claims.

## 1.3.2 - 2026-10-10

This update revises build scripts and documentation within the 1.3 series. All software version numbers remain unchanged.

### Improvements and Fixes

- Corrects ROS2 explicit toolchain argument precedence and runtime-library selection, and supports generating and verifying runtime packages from standalone non-ROS clones.
- Adds Ubuntu 22.04 x86_64 host preparation and complete build steps for five non-ROS examples and ROS2 nodes/plugins; see [Building the Public Demo Source](development/open-source-build.md). Build and package verification do not replace on-device hardware acceptance.
- Defines a shared documentation version policy and maintenance constraints; documentation revisions are independent of software versions, and both language builds read the same revision from `4P_doc/VERSION`.

## 20261009 Toolchain - 2026-10-10

- Publishes [x5_4cam_cross_toolchain_20261009.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20261009.tar.gz), adding target ROS Humble, image_transport/pluginlib, and environment entries, with a fixed bundled compiler and sysroot search paths. See [Building the Public Demo Source](development/open-source-build.md) for the size, SHA-256, and usage.

## 1.3.1 - 2026-09-20

### Added

- The runtime package adds the `sensor_demo` boot-autostart script `start_sensor_demo.sh`: foreground start with no arguments, and `enable`/`disable`/`status` to manage boot autostart. Autostart is implemented through the on-device `/userdata/startup.sh` (the system `S99auto_startup` runs after `/userdata` is mounted); the script only appends/removes its own marked block and can coexist with `wifi_setup.sh` and others; usage is in {ref}`non-ROS Demo Usage: Boot Autostart <non-ros-autostart>`.
- Ships the factory system image and flashing tool matching on-device software `v1.3.0`, supporting factory-system restore and system-version upgrade; image acquisition, flashing steps, and acceptance are in {ref}`Fixes and Upgrades: System Flashing <system-flashing>`.

## 1.3.0 - 2026-09-16

### Added

- Releases the non-ROS `mosaic_rtsp_demo`: composites four SC132 `1280x1088` NV12 frames into one `2560x2176` frame in CPU, outputting fixed H.264 RTSP via `libprrtsp`; the public frame-rate set is `25/30/40/50/60fps`, default `30fps`, fixed address `rtsp://<X5_IP>:558/PRR`. For application details, exit statistics, and resource usage see {ref}`non-ROS Demo Usage: Four-Channel Mosaic RTSP (mosaic_rtsp_demo) <non-ros-mosaic>`.

### Improvements and Fixes

- Releases the updated SC132GS ISP tuning parameter `patch/sc132gs_tuning.json`, improving image quality in some lighting scenarios.

## 1.2.0 - 2026-09-14

### Added

- non-ROS `cam_demo`/`sensor_demo` support VSE hardware full-frame scaled output canvas: `640x480`, `720x480`, `1280x720`, either axial orientation is legal; scaling does not change the FOV, software rotation (180/270) is done by Nano2D after scaling, and external rotation `90/270` swaps the delivered canvas width/height.
- ROS2 image-node frame rate extends to `25/30/40/50/60fps` (default `30fps`), aligned with the non-ROS/RTSP public set.
- `libsc132` real SO upgrades from `libsc132.so.2.0.0` to `libsc132.so.2.0.1`; SONAME is still `libsc132.so.2`, and the ABI node `LIBSC132_2.0` is unchanged.
- Documentation adds NTP, PPS input/UART7 IO reuse, and the X5 master + Mid-360 slave PTP reference configuration; PPS fixedly uses `/dev/pps2` in the current product combination.
- Updates deployment verification, the public API, the version-compatibility entry, and the time-sync boundary. The per-frame-rate completeness and stress boundary of save modes uniformly follows {ref}`Saving Data: Frame Rate and Stress Boundaries <persistence-fps-boundary>`.

## 1.1.1 - 2026-09-08


### Added

- Relative to v1.0.0, non-ROS `sensor_demo` adds ROS1 bag v2.0 saving, including four-channel synchronized JPEG images, camera info, frame metadata, independent IMU, and session status.
- non-ROS `sensor_demo` adds the mutually exclusive H.264 MP4 session save mode, outputting four MP4s, four precise timestamp CSVs, independent IMU CSV, camera parameters, session status, and publication receipt.
- Adds the host offline conversion tool from MP4 session to timestamp-named JPEG, supporting complete and recovery sources and never upgrading partial to complete.
- ICM real SO upgrades from `libicm42688.so.2.0.0` to `libicm42688.so.2.1.0`, ABI minor 2.1; SONAME continues as `libicm42688.so.2`. Existing functions keep the `ICM42688_X5_2.0` node; the new `icm42688_get_runtime_health()` uses the `ICM42688_X5_2.1` node, with sample/config layout unchanged.
- Adds [Saving Data](usage/save-data-guide.md), covering whole-package verification, ROS1 bag/MP4 configuration, graceful exit, acceptance, offline conversion, and recovery.
- The non-ROS public repository adds the interactive `scripts/wifi_setup.sh`, supporting on-board Wi-Fi AP/STA configuration, status viewing, disabling, and optional boot restore; adds the [Wi-Fi Configuration](getting-started/wifi-configuration.md) usage guide.

### Improvements and Fixes

- Strengthens temporary writing, partial/quarantine, atomic no-replace publication, receipt, directory durability, and crash recovery for ROS1 bag and MP4.
- Strengthens stop ordering, callback ownership, timeout process-group cleanup, and error propagation for SC132, RTSP, IMU, writer, and external tools.
- MP4 complete strictly binds the full four-channel inventory, four-channel equal nonzero frames, IMU final health, and status/receipt identity.

### Known Limitations and Release Gates

- ROS1 bag and MP4 currently support only one save mode and cannot be enabled simultaneously in the same process.
- MP4 supports only H.264 full four-channel and no frame skip; the device requires `ffmpeg`, and offline extraction requires a full `ffmpeg`/`ffprobe` on the Host.
- v1.1.1 non-ROS camera and RTSP public frame-rate set is `25/30/40/50/60fps`, default `30fps`; the ROS2 image node is `25/30fps`. IMU supports `25/50/100/200/500/1000/2000Hz`. Save-backend parameter acceptance, completeness, and stress boundaries are in {ref}`Saving Data: Frame Rate and Stress Boundaries <persistence-fps-boundary>`.
- `trigger_mode=none` is only for explicit free-run diagnostics and is not part of the V1 stable release contract; the V1-verified mode is `software_gpio`.
- The non-ROS ROS1 bag and H.264 MP4 complete-save criteria and per-frame-rate boundaries are in [Saving Data](usage/save-data-guide.md); historical evidence is still kept at its original frame rate and does not replace the current release gate.

## v1.0.0 - 2026-08-06


### Added

- non-ROS four-camera H.264/H.265 RTSP example, default four-channel `1280x1088@30fps`.
- Initial version exposes `25/30/40/50/60fps` discrete camera and RTSP configuration.
- camera ID 0/1/2/3 single-channel diagnostics, 0/90/180/270-degree rotation, and pre-configuration validation.
- ICM-42688 FIFO/TMST timestamps, `25/50/100/200/500/1000/2000Hz` discrete ODR, and the non-ROS combined `sensor_demo`.
- ROS2 four-channel NV12 raw, X5 hardware JPEG compressed image, and IMU topic publishing.
- ROS2 runtime environment script, FastDDS SHM configuration, publish-rate metrics, and IMU frequency check tool.
- ROS2 install-root environment script `robobaton_ros2_env.bash`, uniformly loading underlay, overlay, FastDDS SHM profile, and log-buffering settings.
- All in-house SOs provide `*_get_version()` C ABI; delivered executables provide hardware-free `--version`.
- UART1/UART7 3.3V hardware communication passed V1 acceptance; the combined rated boundary for peripheral power from the two UART 3.3V power pins is `500 mA`.

### Known Limitations

- 40/50/60fps are usable, but under high system CPU pressure frame drops may occur, especially at 60fps.
- V1 stability and formal delivery default to four-channel `30fps`.
- The current stable verified four-channel `trigger` mode is `software_gpio`.
- `180`-degree rotation is supported only under the `30fps` configuration.
