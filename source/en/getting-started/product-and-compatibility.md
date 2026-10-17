# Product Version and Compatibility

This page describes compatibility between current RoboBaton 4P V2 source, non-ROS/ROS2 demos, and runtime environments; historical V1 downloads are not automatically V2-compatible. Technical facts follow public headers, configuration, VERSION, and runtime manifests.

## Documentation and Software Versions

See [Release, License, and Support](../release-and-support.md#documentation-version-policy) for the current documentation revision, software releases, and shared version definitions. A documentation revision does not require software versions to increase with it.

V2 uses ICM-42670-P, API `icm42670_*`, real SO `libicm42670.so.2.0.0`, SONAME `libicm42670.so.2`, and node `ICM42670_X5_2.0`. This is incompatible with V1 ICM libraries; update headers, libraries, consumers, and configuration together. Native ODRs are `25/50/100/200/400/800/1600Hz`, default `800Hz`; old `500/1000/2000Hz` rates are explicitly rejected, not silently resampled.

| Deliverable | User entry |
|---|---|
| Documentation | This site and the `4P_doc` repository. |
| non-ROS demo / runtime package | `/root/demo`, from `RoboBaton_4p_demo`'s `demo/`. |
| ROS2 package/install | `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. |


## Capabilities and runtime directories

| Path | Main capabilities | Runtime directory | Notes |
|---|---|---|---|
| non-ROS | Four-channel RTSP, IMU, UART examples, public C ABI | `/root/demo` | RTSP ports `554..557`, path `/PRR`; H.264 default, H.265 optional. |
| ROS2 | raw/compressed images, CameraInfo, IMU, temperature topics | `/root/ros2_demo/install` | ROS2 Humble; compressed uses X5 `MEDIA_CODEC_ID_JPEG` hardware encoding; does not provide RTSP. |

Do not mix directories, headers, or `.so` files between the two paths. Run only one application that uses camera/VIO/encoding resources at a time.

## Runtime requirements

| Item | Requirement |
|---|---|
| On-device platform | X5; camera operation depends on `cam-service`, which should not be stopped or reconfigured. |
| ROS2 | Humble underlay; load the environment via `robobaton_ros2_env.bash`. |
| Cross compilation | Only use the X5 cross-compilation package on the host; native compilation on the X5 is not recommended. |
| non-ROS camera configuration | default `1280x1088@30fps`; supports `25/30/40/50/60fps`; output canvas `1280x1088`/`640x480`/`720x480`/`1280x720`. |
| Trigger | All camera entries support only `vin_lpwm` (VIN LPWM hardware triggering); no free-run or software GPIO triggering. |

The ROS2 path does not provide RTSP; use the non-ROS path when RTSP is needed. TF, extrinsics, camera intrinsics, and distortion calibration are not currently provided; CameraInfo only has width/height, and IMU orientation is unavailable.

## Factory system image and target-board compatibility

The historical factory image and flashing tool for on-device software `v1.3.0` apply only to its original V1 board and must not be written to V2; URLs and artifacts cannot be overwritten in place. Public information for the matching V2 BSP/system image and recovery channel is pending confirmation; see [System Flashing](../ops/system-flashing.md).

## Version query and whole-package matching

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

Deploy and verify as a whole package: non-ROS uses `manifest.sha256`, and the ROS2 install uses the archive checksum plus the runtime `abi_manifest.sha256`. Do not replace only a single executable or a single `.so`; programs, headers, and runtime libraries must come from the same verified software package. The documentation revision cannot establish software or ABI compatibility.
