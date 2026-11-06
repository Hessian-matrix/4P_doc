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
| Documentation revision | `2.0.85` | This site updates continuously; see [Changelog](changelog.md) for revision details. This does not indicate a software version upgrade. |
| non-ROS demo/runtime package | `v2.0.0` | Default installation path: `/root/demo`; verify the whole package with `manifest.sha256`. This does not establish that the target board has artifacts matching current source installed. |
| ROS2 package/install | `v2.0.0` | Default installation path: `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. Source updates or local rebuilds do not establish the target board's installed revision or an official upgrade; check its actual manifests and loaded libraries. Before use, complete the corresponding path's actual checks per [ROS2 Demo Usage](usage/ros2-demo.md), [non-ROS Demo Usage](usage/non-ros-demo.md), and [Saving Data](usage/save-data-guide.md). |
| System image package | `V2.0.0` | [4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz); see [System Flashing](ops/system-flashing.md) for the procedure, checksums, and hardware-matching requirements. |

Feature additions, fixes, and compatibility changes are in [Changelog](changelog.md).

V2 source and documentation repositories use the `V2_main` main branch. Repository browsing, source links, and clone examples select it explicitly; the branch name does not replace version, manifest, or compatibility checks. Remote links require the branch and revision to be pushed; Read the Docs build configuration is managed separately.

The online documentation continues to update based on user feedback at the [Chinese](https://4p-docs.readthedocs.io/zh-cn/4pv2.main/) and [English](https://4p-doc-en.readthedocs.io/en/4pv2.main/) entry points; there is no separately pinned `stable` documentation version. Documentation revisions follow the policy above; Read the Docs `4pv2.main` is a deployment identifier, not a software version or immutable release snapshot. An official software release does not mean target-board runtime checks can be skipped. The public camera parameter set supports `25/30/40/50/60fps`, default `30fps`; the saving and ROS2 paths should be judged by actual results, exit codes, manifest, and target-board environment checks.

Current guides cover V2 software identified as `2.0.0` and the explicitly unreleased source updates in the changelog. An identical version string does not prove an identical artifact composition: check runtime manifests, actually linked libraries, and matching instructions. Match ICM-42670-P headers, libraries, consumers, and configuration as one set. Native rates are `25/50/100/200/400/800/1600Hz`, default `800Hz`; unsupported rates are explicitly rejected, not silently resampled. Documentation revisions do not establish board or system acceptance.

Current `sensor_web` source uses Rust/str0m with static musl `1.2.5` / mallocng, retaining the application-owned child process and WebRTC/SSE/recording entry points. Updating requires a complete matched runtime package and normal application restart, not a kernel, SO ABI, or published-image upgrade. It establishes neither arbitrary-duration leak freedom nor reconnect-free operation or closure of all capture failures. See [Source Builds](development/open-source-build.md), [non-ROS Usage](usage/non-ros-demo.md), and [Troubleshooting](troubleshooting.md) for requirements and limits.

Hardware identity, software `2.0.0`, documentation revision, and each SO ABI are independent dimensions, not substitutes for compatibility or acceptance. This change synchronizes documentation only; it changes no software behavior or release status.

UVC source, standalone build, USB management, and offline installation tools are under non-ROS Demo `scripts/env_setup/x5_usb/`. See {ref}`USB Development Entry Points <usb-uvc-development>` for commands and update boundaries. New online source links become accessible after the corresponding Demo revision is published. Moving sources and adjusting the installer CLI add no runtime functionality, software version, or ABI, and do not establish board deployment or acceptance.

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
| High frame rate | Accepted settings do not promise sustained throughput for every saving, streaming, and ROS2 combination. Historical non-ROS `60fps` + `1600Hz` FSYNC console association for approximately `300s` under CPU/BPU load certifies only that composition's association observation, not saved-image decoding, ROS2 throughput, or losslessness of the new IIO composition. Current software provides no FSYNC. |
| Bag pressure and group drops | Default minimum drop interval is `10`, measured by contiguous `source_group_order`, not producer `group_id`. Only fully encoded, unclaimed complete four-camera groups are eligible; writer-claimed groups stay protected. Without a legal old or incoming group, stop, drain to a readable partial bag, and exit nonzero. Intentional alternate saving requires explicit interval `2`. Historical high CPU/storage pressure exhausted the policy before `300s`; that failure retains its original scope. Keep bag or MP4 as the only high-throughput eMMC/TF writer where possible, without added storage write stress. This reduces contention risk, not a guarantee of sustained losslessness. Every dropped group means `data_complete=false`; see {ref}`Saving Data <persistence-fps-boundary>`. |
| Early stop of startup-auto MP4 | [INFERENCE] Current source lacks final producer health when Web stops CLI/YAML startup-auto MP4 early, preventing complete publication; the fixed Web `health_scope` label also does not establish an adopted session's health scope. Not fixed or reproduced on-device in this update. Judge Web-created dynamic sessions and startup-auto sessions retained until normal shutdown separately; see {ref}`Saving Limitation <startup-mp4-web-stop>`. |
| Sample completeness | Historical premature IMU admission closure and normal ROS2 exit ordering defects are fixed. Current STOP retains admission and drains; check final generation, fatal, scans, records/ACK, stop status, and actual payloads. `transport_complete` certifies only the stop cohort, not all physical tail data. Exact historical DDS loss identity/cause remains unrecoverable; equal short-smoke counts or continuous saved sequences do not prove every hardware sample was saved. `allow-counted` only counts invalid six-axis payloads; `strict` fails on them. Neither guarantees zero loss under arbitrary load. |
| ROS2 rate and SHM | Historical equal producer/sink/DDS counts in a `30fps`/`1600Hz` short smoke do not certify this composition, establish the earlier difference's root cause, or accept sustained `60fps` across all paths. Per-participant `256 MiB` SHM is capacity budgeting, not an initialization-root-cause fix or arbitrary-load guarantee. Disabled metrics mean unavailable; enabled metrics count normal sink `publish()` returns, not DDS receipt. |
| Long recording | No final integrated-composition long-duration or all-pressure-mode acceptance is supplied in this update. Historical FSYNC/`8h` results cannot certify current IIO operation. Sustained capability still needs verification with one recording write workload; extra storage stress is not a prerequisite. |
| Timestamp selectors and short smoke | Final default HO is camera observer + IMU host; the other three startup pairs remain for comparison. A matched IIO V3/ABI5 integrated package completes a short non-ROS HO smoke at four-camera 30fps/IMU800Hz, covering Web preview/attitude, dynamic bag/MP4 recording, complete payload readback, and normal shutdown. It does not certify the other three pairs, ROS2 target operation, physical accuracy, pressure, long recording, or reboot. Examples and historical evidence do not expand this scope. |
| Capture and startup | Selected camera-path failures stop without fallback; IIO migration does not close observer LPWM `500µs` long-tail stops. IIO requires the matched V3 module (V2 incompatible), a unique device, and valid scan/control identity. Overflow, push/evidence, I/O, quiesce, timing-evidence, and fatal errors must not be hidden by a successful prefix. Old userspace FSYNC/Arm special branches are historical, not the current startup contract. |
| Encoding | Native bag JPEG strips private JPU APP9 without changing the ROS2 JPEG plugin. Clean bag JPEG decoding does not close H.264 RTSP `60fps` missing-reference/slice warnings. |
| USB/CAN | The matching new V2 Buildroot image candidate integrates USB3 Host/Device switching with CDC NCM, RNDIS, CDC ECM, four-camera UVC, ADB, and dedicated MSD, with factory-default NCM managed by system tool `switch_usb_gadget`. Older firmware may still default to RNDIS or lack NCM; installer updates preserve an existing boot choice. The computer must support CDC NCM; Windows compatibility is not certified. RNDIS/ECM remain manually selectable without automatic fallback; see [USB Interface Functions and Switching Limits](usage/usb-gadget-switch.md). It uses the image's existing `usb_f_ncm.ko` without kernel changes. Integration does not certify computer enumeration, video reception, disk ejection, repeated switching, or reboot behavior, and existing RNDIS checks do not certify NCM. State-dependent and asymmetric USB throughput remain unresolved. CAN application features do not establish matching-BSP payload integrity, sustained throughput, combined-load, latency, or error-recovery acceptance; no throughput is promised for the current system composition. |
| TF and single-sensor diagnostics | Do not remove the TF card or cut power during recording or writes. Finalize normally, sync, and successfully unmount before removal; see [TF Card Usage](getting-started/tf-card.md). Single-camera diagnostics are user-confirmed. |
| System image, time, and runtime dependencies | The V2 image has been built. Checks on a flashed, booted device cover Buildroot/kernel identity, preinstalled application manifests, non-ROS loaded libraries, Python `3.10.12`, and ROS2 version/package queries in the package environment. Current firmware supports holding SW1 during power-on or reset, then flashing with XBurn over USB3 Fastboot, without a debug UART connection. See [System Flashing](ops/system-flashing.md) for the image download, procedure, checksums, and hardware-matching requirements. The device has boot-started `ntpd`, but no time association and `stratum=16`, not certified UTC. Check peer selection and system synchronization before acquisition per [NTP Sync](time-sync/ntp-sync.md). UTC is not retained over power loss without a battery; cold boot, late connectivity, and sustained lock still need verification. Preinstallation, version queries, and package verification do not validate ROS2 topic/DDS, every saving path, USB, or the whole system. |

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
- UART1/UART7 use `3.3V` logic, DEBUG_UART uses `1.8V`; see the corresponding guides for camera mapping and FOV. UART1 uses CN1 4-pin and UART7 CN2 5-pin. Independent PPS input defaults on and uses `3.3V` logic; see [PPS Sync](time-sync/pps-sync.md) for wiring and input checks. UART power-pin load ratings and hot-plug conditions still await confirmation; wire with power off by default. See [Hardware and Safety](getting-started/hardware-and-safety.md) for pin numbers and signal order. A shared camera/IMU trigger wire does not automatically associate samples and exposures.

## License and Support

| Item | Current status |
|---|---|
| Documentation/source license | Documentation, non-ROS example source, and ROS2 example source use Apache-2.0; governed by each repository's `LICENSE`. |
| Precompiled vendor dynamic-library license | Not covered by Apache-2.0; the current product binary restrictions are retained; delivered with the RoboBaton 4P product and licensed to run only on RoboBaton 4P hardware and its matching system; see `LICENSE_SCOPE.md` in the demo repository. |
| Technical support entry | WeChat: 189-2619-5421 |

## Problem Feedback Checklist

When submitting a problem, include the version, usage path, executed command, error text, and a necessary log summary: non-ROS attach the `manifest.sha256` verification result, camera ID, RTSP URL, codec/fps, and `ffprobe` output; ROS2 attach the launch command, topic names, `robobaton_imu_rate_monitor` output, and the `abi_manifest.sha256` verification result; UART attach the device node, baud, mode, and wiring description. Do not submit real IPs, accounts, credentials, internal paths, internal log packages, or unpublicized verification material.
