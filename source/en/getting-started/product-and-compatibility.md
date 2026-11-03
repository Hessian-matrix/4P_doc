# Product Version and Compatibility

This page describes compatibility between current RoboBaton 4P V2 source, non-ROS/ROS2 demos, and runtime environments. Technical facts follow public headers, configuration, VERSION, and runtime manifests.

## Documentation and Software Versions

See [Release, License, and Support](../release-and-support.md#documentation-version-policy) for the current documentation revision, software releases, and shared version definitions. A documentation revision does not require software versions to increase with it.

Hardware identity, software `2.0.0`, documentation, and SO ABI are identified independently. Supported parameters do not mean all mode/load/duration combinations passed. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for high-rate, pressure, long-recording, and peripheral limits.

V2 uses ICM-42670-P, API `icm42670_*`, ABI 3.0, real SO `libicm42670.so.3.0.0`, and SONAME `libicm42670.so.3`. Every export uses only `ICM42670_X5_3.0`, without old aliases. Field layouts remain unchanged, but host time becomes the SPI FIFO burst-completion observation and INT1 is wake-only; FIFO order and measured TMST define samples. Synchronize headers, libraries, consumers, and configuration, rebuild every consumer, and remove old `.2` libraries without cross-major links. Software VERSION is unchanged. Native ODRs are `25/50/100/200/400/800/1600Hz`, default `800Hz`; unsupported rates are explicitly rejected, not silently resampled.

| Deliverable | User entry |
|---|---|
| Documentation | This site and the `4P_doc` repository. |
| non-ROS demo / runtime package | `/root/demo`, from `RoboBaton_4p_demo`'s `demo/`. |
| ROS2 package/install | `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. |


## Capabilities and runtime directories

| Path | Main capabilities | Runtime directory | Notes |
|---|---|---|---|
| non-ROS | Four-channel RTSP, IMU, UART, mutually exclusive bag/MP4 saving, optional FSYNC, exposure observations | `/root/demo` | RTSP `554..557/PRR`, H.264 default, H.265 optional; four-view mosaic example at `558/PRR`. |
| ROS2 | raw/compressed images, CameraInfo, per-frame exposure observations, IMU, temperature, optional FSYNC | `/root/ros2_demo/install` | ROS2 Humble; compressed uses X5 `MEDIA_CODEC_ID_JPEG` hardware encoding; no RTSP. |

Do not mix directories, headers, or `.so` files between the two paths. Run only one application that uses camera/VIO/encoding resources at a time.

## Runtime requirements

| Item | Requirement |
|---|---|
| On-device platform | X5; camera operation depends on `cam-service`, which should not be stopped or reconfigured. |
| ROS2 | Humble underlay; load the environment via `robobaton_ros2_env.bash`. |
| Cross compilation | Only use the X5 cross-compilation package on the host; native compilation on the X5 is not recommended. |
| non-ROS camera configuration | default `1280x1088@30fps`; supports `25/30/40/50/60fps`; output canvas `1280x1088`/`640x480`/`720x480`/`1280x720`. |
| Trigger | All camera entries support only `vin_lpwm` (VIN LPWM hardware triggering); no free-run or software GPIO triggering. |
| Permissions and scheduling | Cameras require read-only `/dev/mem`; capture and IMU realtime threads require scheduling permission, with failure rejecting startup. See [Data Contracts](../development/data-contracts.md). |

Cameras support only full four-camera operation or single-sensor diagnostics, not 2/3 cameras; rotation `180` requires `30fps`. Single-camera diagnostics are user-confirmed, not acceptance of every mode or pressure load.

The ROS2 path does not provide RTSP; use the non-ROS path when RTSP is needed. TF, extrinsics, camera intrinsics, and distortion calibration are not currently provided; CameraInfo only has width/height, and IMU orientation is unavailable.

Current camera ABI 3.0 adds frozen per-frame ISP `exposure` observations with frame-info prefix-size reads but a new `libsc132.so.3` SONAME; old binaries must be rebuilt; estimates do not certify applied exposure for that frame. FSYNC defaults off, supports only `800/1600Hz`, and provides unique trigger-to-sample association, not exposure synchronization. An identical software version does not prove identical package capabilities: distinguish unreleased changes in [Changelog](../changelog.md) and check manifests, headers, and actual libraries.

## Factory system image and target-board compatibility

Public information for the matching V2 BSP/system image and recovery channel is pending confirmation. No public image download or confirmed flashing procedure is currently available; see [System Flashing](../ops/system-flashing.md). Do not write an image unless its compatibility with the current hardware is confirmed.

## Version query and whole-package matching

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

Deploy and verify as a whole package: non-ROS uses `manifest.sha256`, and the ROS2 install uses the archive checksum plus the runtime `abi_manifest.sha256`. Do not replace only a single executable or a single `.so`; programs, headers, and runtime libraries must come from the same verified software package. The documentation revision cannot establish software or ABI compatibility.
