# Release, License, and Support

This page records the release status of public deliverables, the known limitations users will encounter, licensing, and problem-feedback information.

## Documentation Version Policy

This page defines the version policy for the entire public documentation set; [Changelog](changelog.md) records user-visible updates under this policy.

- Documentation versions use major.minor.revision. The final revision number identifies small bug fixes, build-script adjustments, or documentation corrections within the same release series, without automatically changing individual software versions.
- `4P_doc/VERSION` is the sole source of the documentation revision; both Sphinx language configurations read it directly. Each revision updates the latest versioned changelog entry and this page's version information in both languages.
- Software versions in the non-ROS and ROS2 repositories remain identified by their own `VERSION`, ROS2 `package.xml`, package version, and `--version` output. Documentation revisions must not change these versions or require them to equal the documentation revision.
- SO SONAME/ABI versions are independent of documentation revisions and software versions: for example, the `2` in `libicm42688.so.2` is the ABI major. A documentation revision does not imply an ABI change, a software re-release, or an update on the target board.

## Version Set

| Item | Current version | Status |
|---|---|---|
| Documentation revision | `1.3.3` | This site updates continuously; see [Changelog](changelog.md) for revision details. This does not indicate a software version upgrade. |
| non-ROS demo/runtime package | `v1.3.3` | Software patch version; the runtime package targets `/root/demo` and is whole-package verified by `manifest.sha256`. |
| ROS2 package/install | `v1.3.3` | Software patch version; the install targets `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. Before use on the target board, complete the corresponding path's actual checks per [ROS2 Demo Usage](usage/ros2-demo.md), [non-ROS Demo Usage](usage/non-ros-demo.md), and [Saving Data](usage/save-data-guide.md); a Git release does not imply a target-board update. |

Feature additions, fixes, and compatibility changes are in [Changelog](changelog.md).

The online documentation continues to update based on user feedback; there is currently no separately pinned `stable` documentation version. Documentation revisions follow the policy above; Read the Docs `latest` is a deployment identifier, not a software version. An official software release does not mean target-board runtime checks can be skipped. The public camera parameter set supports `25/30/40/50/60fps`, default `30fps`; the saving and ROS2 paths should be judged by actual results, exit codes, manifest, and target-board environment checks.

## Known Limitations

- TF extrinsics, camera intrinsics, and distortion calibration are currently not provided.
- ROS2 does not provide RTSP; use non-ROS `/root/demo` when RTSP is needed.
- Camera applications exclusively hold camera/VIO/encoding resources; before switching, exit the old application and keep `cam-service` running.
- non-ROS camera, RTSP, ROS1 bag, H.264 MP4, and the ROS2 image node publicly support `25/30/40/50/60fps`, default `30fps`; `--rotate 180` still supports only `30fps`.
- `software_gpio` is the only V1 stable trigger; `none` is only for explicit free-run diagnostics.
- CameraInfo only has width/height, and IMU orientation is unavailable.
- H.265 or four-channel high-frame-rate playback depends on the client's decode and render capability.
- DEBUG_UART is the `1.8V` system console/debug port; in normal mode UART1/UART7 use `3.3V` TX/RX/GND with common ground, and hardware communication passed V1 acceptance. The `3V3` pins of UART1/UART7 support input/output and can power peripherals, with a shared `500 mA` total limit across the two interfaces and hot-plug support; `serial_port_demo` applies only to normal UART mode. PPS mode occupies UART7 RX as `/dev/pps2` separately and releases UART7 TX as GPIO/IO; see [PPS Sync](time-sync/pps-sync.md).

## License and Support

| Item | Current status |
|---|---|
| Documentation/source license | Documentation, non-ROS example source, and ROS2 example source use Apache-2.0; governed by each repository's `LICENSE`. |
| Precompiled vendor dynamic-library license | Not covered by Apache-2.0; the current product binary restrictions are retained; delivered with the RoboBaton 4P product and licensed to run only on RoboBaton 4P hardware and its matching system; see `LICENSE_SCOPE.md` in the demo repository. |
| Technical support entry | WeChat: 189-2619-5421 |

## Problem Feedback Checklist

When submitting a problem, include the version, usage path, executed command, error text, and a necessary log summary: non-ROS attach the `manifest.sha256` verification result, camera ID, RTSP URL, codec/fps, and `ffprobe` output; ROS2 attach the launch command, topic names, `robobaton_imu_rate_monitor` output, and the `abi_manifest.sha256` verification result; UART attach the device node, baud, mode, and wiring description. Do not submit real IPs, accounts, credentials, internal paths, internal log packages, or unpublicized verification material.
