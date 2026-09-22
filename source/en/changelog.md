# Changelog

This file records user-visible updates in the RoboBaton 4P public delivery. Version numbers follow [Semantic Versioning 2.0.0](https://semver.org/); the SO SONAME/ABI version is independent of the product release version — for example the `2` in `libicm42688.so.2` is the ABI major and does not equal the product version.

## 1.3.1 - 2026-09-20

### Added

- The runtime package adds the `sensor_demo` boot-autostart script `start_sensor_demo.sh`: foreground start with no arguments, and `enable`/`disable`/`status` to manage boot autostart. Autostart is implemented through the on-device `/userdata/startup.sh` (the system `S99auto_startup` runs after `/userdata` is mounted); the script only appends/removes its own marked block and can coexist with `wifi_setup.sh` and others; usage is in {ref}`non-ROS Demo Usage: Boot Autostart <non-ros-autostart>`.
- Ships the factory system image and flashing tool matching on-device software `v1.3.0`, supporting factory-system restore and system-version upgrade; image acquisition, flashing steps, and acceptance are in {ref}`Fixes and Upgrades: System Flashing <system-flashing>`.

## 1.3.0 - 2026-09-16

### Added

- Releases the non-ROS `mosaic_rtsp_demo`: composites four SC132 `1280x1088` NV12 frames into one `2560x2176` frame in CPU, outputting fixed H.264 RTSP via `libprrtsp`; the public frame-rate set is `25/30/40/50/60fps`, default `30fps`, fixed address `rtsp://<X5_IP>:558/PRR`. For application details, exit statistics, and resource usage see {ref}`non-ROS Demo Usage: Four-Channel Mosaic RTSP (mosaic_rtsp_demo) <non-ros-mosaic>`.

### Improvements and Fixes

- Releases the updated SC132GS ISP tuning parameter `patch/sc132gs_tuning.json`, improving image quality in some lighting scenarios; usage and rollback are in {ref}`Fixes and Upgrades: ISP Image Quality Fix <isp-image-quality-fix>`.

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
