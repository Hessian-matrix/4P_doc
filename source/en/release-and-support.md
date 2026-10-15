# Release, License, and Support

This page records the release status of public deliverables, the known limitations users will encounter, licensing, and problem-feedback information.

## Documentation Version Policy

This page defines the version policy for the entire public documentation set; [Changelog](changelog.md) records user-visible updates under this policy.

- Documentation versions use major.minor.revision. The final revision number identifies small bug fixes, build-script adjustments, or documentation corrections within the same release series, without automatically changing individual software versions.
- `4P_doc/VERSION` is the sole source of the documentation revision; both Sphinx language configurations read it directly. Each revision updates the latest versioned changelog entry and this page's version information in both languages.
- Software versions in the main, non-ROS, and ROS2 repositories remain identified by their own `VERSION`, ROS2 `package.xml`, package version, and `--version` output. Documentation revisions must not change these versions or require them to equal the documentation revision.
- SO SONAME/ABI versions are independent of documentation and software versions: `2` in `libicm42670.so.2` is the ABI major; real SO `2.0.0` and product `--version` are also distinct identifiers. Documentation revisions do not imply software re-release or a target-board update.

## Version Set

| Item | Current version | Status |
|---|---|---|
| Documentation revision | `2.0.0` | This site updates continuously; see [Changelog](changelog.md) for revision details. This does not indicate a software version upgrade. |
| non-ROS demo/runtime package | `v2.0.0` | Deployed to `/root/demo`, whole-package verified by `manifest.sha256`. |
| ROS2 package/install | `v2.0.0` | The package is deployed to `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. Before use on the target board, complete the corresponding path's actual checks per [ROS2 Demo Usage](usage/ros2-demo.md), [non-ROS Demo Usage](usage/non-ros-demo.md), and [Saving Data](usage/save-data-guide.md); package release does not replace target-board runtime checks. |

Feature additions, fixes, and compatibility changes are in [Changelog](changelog.md).

The online documentation continues to update based on user feedback; there is currently no separately pinned `stable` documentation version. Documentation revisions follow the policy above; Read the Docs `latest` is a deployment identifier, not a software version. An official software release does not mean target-board runtime checks can be skipped. The public camera parameter set supports `25/30/40/50/60fps`, default `30fps`; the saving and ROS2 paths should be judged by actual results, exit codes, manifest, and target-board environment checks.

Current usage guides describe V2 source. Inherited software version values do not imply V1 binary compatibility: migrate ICM-42670-P headers, libraries, consumers, and configuration together. Native rates are `25/50/100/200/400/800/1600Hz`, default `800Hz`, with old `500/1000/2000Hz` values explicitly rejected. Historical V1 download URLs and changelogs are unchanged and cannot establish V2 board or system acceptance.

## Known Limitations

- TF extrinsics, camera intrinsics, and distortion calibration are currently not provided.
- ROS2 does not provide RTSP; use non-ROS `/root/demo` when RTSP is needed.
- Camera applications exclusively hold camera/VIO/encoding resources; before switching, exit the old application and keep `cam-service` running.
- non-ROS camera, RTSP, ROS1 bag, H.264 MP4, and the ROS2 image node publicly support `25/30/40/50/60fps`, default `30fps`; `--rotate 180` still supports only `30fps`.
- `vin_lpwm` is the V2.0.0 default trigger (VIN hardware trigger); `none` is only for explicit free-run diagnostics; the `software_gpio` public entry is closed and kept only as a main-repo internal debug path.
- CameraInfo only has width/height, and IMU orientation is unavailable.
- H.265 or four-channel high-frame-rate playback depends on the client's decode and render capability.
- V2 UART pinout, voltage, power/hot-plug boundaries, PPS mux, and physical mapping are pending confirmation; do not inherit the V1 `500 mA` limit or historical acceptance. See [Hardware Connection and Safety](getting-started/hardware-and-safety.md). IMU FSYNC shares the camera trigger net but does not provide camera/IMU hardware alignment.

## License and Support

| Item | Current status |
|---|---|
| Documentation/source license | Documentation, non-ROS example source, and ROS2 example source use Apache-2.0; governed by each repository's `LICENSE`. |
| Precompiled vendor dynamic-library license | Not covered by Apache-2.0; the current product binary restrictions are retained; delivered with the RoboBaton 4P product and licensed to run only on RoboBaton 4P hardware and its matching system; see `LICENSE_SCOPE.md` in the demo repository. |
| Technical support entry | WeChat: 189-2619-5421 |

## Problem Feedback Checklist

When submitting a problem, include the version, usage path, executed command, error text, and a necessary log summary: non-ROS attach the `manifest.sha256` verification result, camera ID, RTSP URL, codec/fps, and `ffprobe` output; ROS2 attach the launch command, topic names, `robobaton_imu_rate_monitor` output, and the `abi_manifest.sha256` verification result; UART attach the device node, baud, mode, and wiring description. Do not submit real IPs, accounts, credentials, internal paths, internal log packages, or unpublicized verification material.
