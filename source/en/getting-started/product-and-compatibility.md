# Product Version and Compatibility

This page describes compatibility between current RoboBaton 4P V2 source, non-ROS/ROS2 demos, and runtime environments. Technical facts follow public headers, configuration, VERSION, and runtime manifests.

## Documentation and Software Versions

See [Release, License, and Support](../release-and-support.md#documentation-version-policy) for the current documentation revision, software releases, and shared version definitions. A documentation revision does not require software versions to increase with it.

Hardware identity, software `2.0.0`, documentation, and SO ABI are identified independently. Supported parameters do not mean all mode/load/duration combinations passed. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for high-rate, pressure, long-recording, and peripheral limits.

Current IMU capture uses kernel IIO public ABI 6.0: real file `libicm42670.so.6.0.0`, SONAME `libicm42670.so.6`, and nine exports under `ICM42670_X5_6.0`. A matched kernel IIO V4 capture module must already bind the device; the existing V2/V3 module is incompatible even for host. Rebuild all consumers with matching headers/libraries and remove old-major artifacts, without cross-major links. Startup `camera_timestamp_path=observer|official` (default observer) and `imu_timestamp_mode=host|tmst` (default host) give four combinations in the same binary with the same IIO reads/owner; stop/restart to change. Host retains MONOTONIC with unknown physical error; tmst adds bounded-affine RAW sample mapping from kernel FIFO/UI transition evidence while preserving MONOTONIC. Its `200µs` computational admission is not physical accuracy. Official camera time is a same-frame IRQ-derived estimate with unknown physical bound, never a SIF observer result. Saving/ROS2 bridge the selected native mode to realtime and retain native evidence. No userspace SPI/spidev, FSYNC restoration, or fallback exists. See [non-ROS Usage](../usage/non-ros-demo.md), [ROS2 Usage](../usage/ros2-demo.md), and [Data Contracts](../development/data-contracts.md). See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for the current non-ROS HO short smoke and unverified scope. software, documentation, ABI, and release status remain independent.

| Deliverable | User entry |
|---|---|
| Documentation | This site and the `4P_doc` repository. |
| non-ROS demo / runtime package | `/root/demo`, from `RoboBaton_4p_demo`'s `demo/`. |
| ROS2 package/install | `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. |


## Capabilities and runtime directories

| Path | Main capabilities | Runtime directory | Notes |
|---|---|---|---|
| non-ROS | Four-channel RTSP, IMU, UART, mutually exclusive bag/MP4 saving, IMU timing metadata, exposure observations | `/root/demo` | RTSP `554..557/PRR`, H.264 default, H.265 optional; four-view mosaic example at `558/PRR`. |
| ROS2 | raw/compressed images, CameraInfo, per-frame exposure observations, IMU, temperature, IMU timing metadata | `/root/ros2_demo/install` | ROS2 Humble; compressed uses X5 `MEDIA_CODEC_ID_JPEG` hardware encoding; no RTSP. |

Do not mix directories, headers, or `.so` files between the two paths. Run only one application that uses camera/VIO/encoding resources at a time.

## Runtime requirements

| Item | Requirement |
|---|---|
| On-device platform | X5; camera operation depends on `cam-service`, which should not be stopped or reconfigured. |
| ROS2 | Humble underlay; load the environment via `robobaton_ros2_env.bash`. |
| Cross compilation | Only use the X5 cross-compilation package on the host; native compilation on the X5 is not recommended. |
| non-ROS camera configuration | default `1280x1088@30fps`; supports `25/30/40/50/60fps`; output canvas `1280x1088`/`640x480`/`720x480`/`1280x720`. |
| Trigger | All camera entries support only `vin_lpwm` (VIN LPWM hardware triggering); no free-run or software GPIO triggering. |
| Permissions and scheduling | Only camera `observer` needs read-only `/dev/mem` and `SCHED_FIFO/60`; `official` does not start that observer. IMU owner/consumer realtime threads require scheduling permission; failure rejects startup. See [Data Contracts](../development/data-contracts.md). |

Cameras support only full four-camera operation or single-sensor diagnostics, not 2/3 cameras; rotation `180` requires `30fps`. Single-camera diagnostics are user-confirmed, not acceptance of every mode or pressure load.

The ROS2 path does not provide RTSP; use the non-ROS path when RTSP is needed. TF, extrinsics, camera intrinsics, and distortion calibration are not currently provided; CameraInfo only has width/height, and IMU orientation is unavailable.

Camera ABI 3.0 `exposure` freezes a fixed one-hardware-frame association estimate: a getter obtained while acquiring raw hardware frame N estimates adjacent N+1 only, allowing uint32 wrap, never matched by normalized group IDs or SDK source frame IDs. No predecessor, hardware gaps, or invalid predecessor queries yield unavailable/all zero; provenance retains older-getter values. Consumers forward unchanged without another frame shift. Estimates certify neither applied exposure nor a measured physical-error bound. Frame-info prefix-size reads, public layout, SONAME, software versions, and default trigger stamps are unchanged; opt-in midpoint uses the matched estimate and still stops when unavailable. Identical software versions do not prove identical packages: check [Changelog](../changelog.md), manifest, headers, and loaded libraries. See [Exposure Observations](../development/data-contracts.md#per-frame-exposure-observations) for the complete state/warmup contract.

Fixed N→N+1 is only an estimated-association rule. Real AE can have a different effective lag; there is no per-frame applied-exposure guarantee or AE acceptance claim.

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
