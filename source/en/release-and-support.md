# Release, License, and Support

This page records the release status of public deliverables, the known limitations users will encounter, licensing, and problem-feedback information.

## Documentation Version Policy

This page defines the version policy for the entire public documentation set; [Changelog](changelog.md) records user-visible updates under this policy.

- Documentation versions use major.minor.revision. The final revision number identifies small bug fixes, build-script adjustments, or documentation corrections within the same release series, without automatically changing individual software versions.
- `4P_doc/VERSION` is the sole source of the documentation revision; both Sphinx language configurations read it directly. Each revision updates the latest versioned changelog entry and this page's version information in both languages.
- Software versions in the main, non-ROS, and ROS2 repositories remain identified by their own `VERSION`, ROS2 `package.xml`, package version, and `--version` output. Documentation revisions must not change these versions or require them to equal the documentation revision.
- SO SONAME/ABI versions are independent of documentation and software versions: `5` in `libicm42670.so.5` is the ABI major; real SO `5.0.0` and product `--version` are also distinct identifiers. Documentation revisions do not imply software re-release or a target-board update.


| Library | Real file | SONAME | Symbol nodes |
|---|---|---|---|
| ICM42670 | `libicm42670.so.5.0.0` | `libicm42670.so.5` | `ICM42670_X5_5.0` |
| SC132 | `libsc132.so.3.0.0` | `libsc132.so.3` | `LIBSC132_3.0` |
| PRRTSP | `libprrtsp.so.2.0.1` | `libprrtsp.so.2` | `LIBPRRTSP_2.0` |

Real-library revisions identify implementations; SONAME majors identify replaceable public contracts; symbol nodes distinguish compatible extensions from incompatible cutovers. They do not track product generations mechanically. SC132 currently uses ABI 3.0: rebuild consumers together against the current headers' time-domain, trigger-mode, and frame-info semantics; never add a `.so.2 -> .so.3` link. ROS2 includes only ICM42670 and SC132.

Current IMU capture uses kernel IIO public ABI 5.0, with nine exports in the table's symbol node. All consumers must be rebuilt with matching headers/libraries, removing old majors without shims. The matched **kernel IIO V3 capture module** must already bind the device; existing V2 is incompatible even in host mode, and application packages do not upgrade it. Startup `camera_timestamp_path=observer|official` (default observer) and `imu_timestamp_mode=host|tmst` (default host) provide four pairs in the same binary with the same IIO reads/owner; stop/restart to change. Host preserves MONOTONIC without a physical bound; tmst adds bounded-affine RAW mapping from kernel-owned FIFO/UI evidence while retaining native host/burst values. Saving/ROS2 bridge the selected native mode to realtime, with separate RAW/MONOTONIC bridge fields and timing schema v2. No userspace SPI/spidev, FSYNC restoration, or automatic fallback exists. Official camera time never uses the SIF observer and has unknown physical error (validity0/uncertainty `UINT32_MAX`); observer's `500µs` admission remains unchanged. See [Data Contracts](development/data-contracts.md), [non-ROS Usage](usage/non-ros-demo.md), and [ROS2 Usage](usage/ros2-demo.md).

## Version Set

| Item | Current version | Status |
|---|---|---|
| Documentation revision | `2.0.17` | This site updates continuously; see [Changelog](changelog.md) for revision details. This does not indicate a software version upgrade. |
| non-ROS demo/runtime package | `v2.0.0` | Default installation path: `/root/demo`; verify the whole package with `manifest.sha256`. This does not establish that the target board has artifacts matching current source installed. |
| ROS2 package/install | `v2.0.0` | Default installation path: `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. Source updates or local rebuilds do not establish the target board's installed revision or an official upgrade; check its actual manifests and loaded libraries. Before use, complete the corresponding path's actual checks per [ROS2 Demo Usage](usage/ros2-demo.md), [non-ROS Demo Usage](usage/non-ros-demo.md), and [Saving Data](usage/save-data-guide.md). |

Feature additions, fixes, and compatibility changes are in [Changelog](changelog.md).

The online documentation continues to update based on user feedback; there is currently no separately pinned `stable` documentation version. Documentation revisions follow the policy above; Read the Docs `latest` is a deployment identifier, not a software version. An official software release does not mean target-board runtime checks can be skipped. The public camera parameter set supports `25/30/40/50/60fps`, default `30fps`; the saving and ROS2 paths should be judged by actual results, exit codes, manifest, and target-board environment checks.

Current guides cover V2 software identified as `2.0.0` and the explicitly unreleased source updates in the changelog. An identical version string does not prove an identical artifact composition: check runtime manifests, actually linked libraries, and matching instructions. Match ICM-42670-P headers, libraries, consumers, and configuration as one set. Native rates are `25/50/100/200/400/800/1600Hz`, default `800Hz`; unsupported rates are explicitly rejected, not silently resampled. Documentation revisions do not establish board or system acceptance.

Hardware identity (current hardware revision V2.2), software `2.0.0`, documentation revision, and each SO ABI are independent dimensions, not substitutes for compatibility or acceptance. This change synchronizes documentation only; it changes no software behavior or release status.

## Current Implemented Capabilities

These are parameters and output contracts accepted by current public source, not acceptance of every mode, load, and duration combination.

| Path | Current capability | Constraints |
|---|---|---|
| Camera | `25/30/40/50/60fps`, default `30fps`; native NV12 `1280x1088`, discrete VSE `640x480`/`720x480`/`1280x720` | Full four-camera operation or single-sensor diagnostics only, not 2/3 cameras; rotation `180` only at `30fps`. Every entry uses only `vin_lpwm`. |
| IMU | Native `25/50/100/200/400/800/1600Hz`, default800Hz; host/tmst startup selector | Same IIO V3 capture; MONOTONIC host evidence retained in both modes, tmst adds RAW sample mapping. Watermark1, buffer4096 default, powers of two in256..8192. Library/standalone demos do not convert to realtime. |
| non-ROS | Four H.264/H.265 RTSP streams, with either ROS1 bag or H.264 MP4 saving | Bag and MP4 are mutually exclusive; MP4 requires H.264 and all four cameras. Standalone UART/CAN examples do not establish peripheral or combined-load acceptance. |
| ROS2 | raw/compressed Image, CameraInfo, exposure observations, IMU, temperature, IMU timing metadata | No RTSP, TF, or calibration; successful publication is not actual DDS reception. |
| Exposure/timing metadata | Latest ISP exposure estimates; IMU output retains native clocks and bridge observations | Exposure does not certify applied-frame identity; bridge half-width is not physical precision; no trigger-to-sample association. |

The camera `observer` thread uses `SCHED_FIFO/60` (not started in `official`), IMU owner `SCHED_FIFO/20`, and non-ROS consumers/ROS2 publication `SCHED_RR/3`; scheduling failure rejects startup without automatic IRQ/debug/realtime-quota changes. Observer retains `500µs` capture-window admission; official has unknown physical error. Host has no physical-error bound; tmst's `200µs` computational sample-mapping admission and the output bridge bracket are not physical accuracy. See [Data Contracts](development/data-contracts.md).

(capability-verification-boundary)=
## Capability and Verification Boundaries

| Area | Current conclusion and user-facing limits |
|---|---|
| High frame rate | Accepted settings do not promise sustained throughput for every saving, streaming, and ROS2 combination; older compositions do not certify current IIO operation. |
| Bag overload/group drops | Default minimum interval10 uses contiguous source_group_order; retain/drop complete four-camera groups together and protect writer-claimed groups. Without a legal candidate, stop/drain to partial and exit nonzero. Any drop means data_complete=false; policy compliance does not guarantee sustained throughput. Intentional alternate saving requires interval2. |
| Sample completeness | Keep admission open and drain during STOP; check final generation, fatal, scans, records/ACK, stop status, and actual payloads. `transport_complete` certifies only the stop cohort, not all physical tail data. `allow-counted` counts invalid payloads; strict fails on them. Neither guarantees zero loss under arbitrary load. |
| ROS2 rate and SHM | Per-participant256MiB SHM is capacity budgeting, not an arbitrary-process/load guarantee. Disabled metrics mean unavailable sink counts; enabled metrics count normal `publish()` returns, not DDS receipt. |
| Long recording | No claim of completed long-duration or all-pressure-mode acceptance for the current composition; historical recordings cannot certify it. |
| Timestamp selectors | No board testing or deployment is performed in this documentation update. Four-way examples document implemented startup selection, not completed board validation, physical-accuracy calibration, or all-load acceptance. |
| Capture and startup | Selected camera-path failures stop without fallback. IIO requires the matched V3 module (V2 incompatible), a unique device, and valid scan/control identity. Overflow, push/evidence, I/O, quiesce, timing-evidence, and fatal errors must not be hidden by a successful prefix. |
| Encoding | Native bag JPEG strips private JPU APP9 without changing the ROS2 JPEG plugin. Clean bag JPEG decoding does not close H.264 RTSP `60fps` missing-reference/slice warnings. |
| USB/CAN | USB state-dependent and asymmetric bidirectional throughput, the full Bulk mode combinations, and re-enumeration remain unresolved. CAN application features do not establish matching-BSP payload integrity, sustained throughput, combined-load, latency, or error-recovery acceptance; no throughput is promised for the current system composition. |
| TF and single-sensor diagnostics | The TF hot-plug hardware repair and single-camera diagnostics are user-confirmed. This does not imply a new hardware version, compatibility with every card, or safe removal during recording; see [TF Card Usage](getting-started/tf-card.md). |
| System time and runtime dependencies | Realtime field semantics do not certify persistent RTC, clock synchronization after reboot, or absolute UTC. Clean-image versus package ownership of `python3`/`libstdc++` remains unresolved; package verification does not prove every runtime dependency is validated. |

Judge functionality, actual saved/received payloads, exit status, and the target environment separately. Accepted parameters, association JSON, complete containers, and historical individual results do not substitute for current-composition acceptance.


## Known Limitations

- TF extrinsics, camera intrinsics, and distortion calibration are currently not provided.
- ROS2 does not provide RTSP; use non-ROS `/root/demo` when RTSP is needed.
- Camera applications exclusively hold camera/VIO/encoding resources; before switching, exit the old application and keep `cam-service` running.
- non-ROS camera, RTSP, ROS1 bag, H.264 MP4, and the ROS2 image node publicly support `25/30/40/50/60fps`, default `30fps`; `--rotate 180` still supports only `30fps`.
- Every camera acquisition entry supports only `vin_lpwm` (VIN LPWM hardware triggering); `none`, free-run, and `software_gpio` paths are no longer available.
- CameraInfo only has width/height, and IMU orientation is unavailable.
- Camera ABI 3.0 `exposure` freezes the latest ISP observation per frame; `status=1` is only an estimate and `0` means unavailable. Applied-frame identity, an error bound, and actual exposure midpoint are not guaranteed.
- No FSYNC enable options or association outputs exist; a common realtime epoch does not establish exposure/physical sampling synchronization.
- Camera capture observers and IMU owner/consumer threads require realtime scheduling permission; configuration failure rejects startup. Saturated load can cause counted drops or acquisition failure; applications do not automatically change system IRQ, debug, or realtime quotas. Acceptance requires final health records and actual stored/received payloads; see [Data Contracts](development/data-contracts.md).
- H.265 or four-channel high-frame-rate playback depends on the client's decode and render capability.
- UART1/UART7 use `3.3V` logic, DEBUG_UART uses `1.8V`; see the corresponding guides for camera mapping and FOV. Independent PPS input defaults on. Complete V2 5-pin order, power-pin ratings, and hot-plug conditions still await official hardware confirmation; wire with power off by default. See [Hardware Connection and Safety](getting-started/hardware-and-safety.md). A shared camera/IMU trigger wire does not automatically associate samples and exposures.

## License and Support

| Item | Current status |
|---|---|
| Documentation/source license | Documentation, non-ROS example source, and ROS2 example source use Apache-2.0; governed by each repository's `LICENSE`. |
| Precompiled vendor dynamic-library license | Not covered by Apache-2.0; the current product binary restrictions are retained; delivered with the RoboBaton 4P product and licensed to run only on RoboBaton 4P hardware and its matching system; see `LICENSE_SCOPE.md` in the demo repository. |
| Technical support entry | WeChat: 189-2619-5421 |

## Problem Feedback Checklist

When submitting a problem, include the version, usage path, executed command, error text, and a necessary log summary: non-ROS attach the `manifest.sha256` verification result, camera ID, RTSP URL, codec/fps, and `ffprobe` output; ROS2 attach the launch command, topic names, `robobaton_imu_rate_monitor` output, and the `abi_manifest.sha256` verification result; UART attach the device node, baud, mode, and wiring description. Do not submit real IPs, accounts, credentials, internal paths, internal log packages, or unpublicized verification material.
