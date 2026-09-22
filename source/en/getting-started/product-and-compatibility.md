# Product Version and Compatibility

This page describes the matching relationship among the RoboBaton 4P first-release documentation, the non-ROS demo, the ROS2 demo, and the X5 runtime environment. Technical facts are sourced from the public repositories, public headers, default configuration, `VERSION`, and runtime package manifest.

## Current official release baseline: v1.3.0

| Deliverable | Current version | User entry |
|---|---|---|
| Documentation | `1.3.0` | This site and the `4P_doc` repository. |
| non-ROS demo / runtime package | `1.3.0` | `/root/demo`, from `RoboBaton_4p_demo`'s `demo/`. |
| ROS2 package / install | `1.3.0` | `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. |


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
| Trigger | `software_gpio` is the only stable V1 trigger; `none` is only for explicit free-run diagnostics. |

The ROS2 path does not provide RTSP; use the non-ROS path when RTSP is needed. TF, extrinsics, camera intrinsics, and distortion calibration are not currently provided; CameraInfo only has width/height, and IMU orientation is unavailable.

## Factory system image and target-board compatibility

On-device software `v1.3.0` ships a matching factory system image and flashing tool. The image applies only to the original product board and does not guarantee compatibility with other target boards; see [System Flashing](../ops/system-flashing.md) for image acquisition and flashing steps.

## Version query and whole-package matching

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

Deploy and verify as a whole package: non-ROS uses `manifest.sha256`, and the ROS2 install uses the archive checksum plus the runtime `abi_manifest.sha256`. Do not replace only a single executable or a single `.so`; the `1.3.0` documentation, runtime package, and ROS2 package should be used as the same v1.3.0 release set.
