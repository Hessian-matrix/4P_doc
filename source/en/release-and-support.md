# Release, License, and Support

This page records the release status of public deliverables, the known limitations users will encounter, licensing, and problem-feedback information.

## Documentation Version Policy

This page defines the version policy for the entire public documentation set; [Changelog](changelog.md) records user-visible updates under this policy.

- Documentation versions use major.minor.revision. The final revision number identifies small bug fixes, build-script adjustments, or documentation corrections within the same release series, without automatically changing individual software versions.
- `4P_doc/VERSION` is the sole source of the documentation revision; both Sphinx language configurations read it directly. Each revision updates the latest versioned changelog entry and this page's version information in both languages.
- Software versions in the main, non-ROS, and ROS2 repositories remain identified by their own `VERSION`, ROS2 `package.xml`, package version, and `--version` output. Documentation revisions must not change these versions or require them to equal the documentation revision.
- SO SONAME/ABI versions are independent of documentation and software versions: `3` in `libicm42670.so.3` is the ABI major; real SO `3.0.0` and product `--version` are also distinct identifiers. Documentation revisions do not imply software re-release or a target-board update.


| Library | Real file | SONAME | Symbol nodes |
|---|---|---|---|
| ICM42670 | `libicm42670.so.3.0.0` | `libicm42670.so.3` | `ICM42670_X5_3.0` |
| SC132 | `libsc132.so.3.0.0` | `libsc132.so.3` | `LIBSC132_3.0` |
| PRRTSP | `libprrtsp.so.2.0.1` | `libprrtsp.so.2` | `LIBPRRTSP_2.0` |

Real-library revisions identify implementations; SONAME majors identify replaceable public contracts; symbol nodes distinguish compatible extensions from incompatible cutovers. They do not track product generations mechanically. SC132 currently uses ABI 3.0: rebuild consumers together against the current headers' time-domain, trigger-mode, and frame-info semantics; never add a `.so.2 -> .so.3` link. ROS2 includes only ICM42670 and SC132.

ICM42670 ABI 3.0 retains field layouts but changes host-time semantics: INT1 only wakes acquisition, FIFO/measured TMST define samples, and host time is the original burst-completion RAW observation converted to realtime using that observation's bridge; see [Data Contracts](development/data-contracts.md#imu). Rebuild every consumer, synchronize headers/SOs, and remove old `.2` libraries. All exports use only `ICM42670_X5_3.0`, without old aliases or cross-major shims. This ABI cutover does not automatically change software VERSION.

## Version Set

| Item | Current version | Status |
|---|---|---|
| Documentation revision | `2.0.57` | This site updates continuously; see [Changelog](changelog.md) for revision details. This does not indicate a software version upgrade. |
| non-ROS demo/runtime package | `v2.0.0` | Default installation path: `/root/demo`; verify the whole package with `manifest.sha256`. This does not establish that the target board has artifacts matching current source installed. |
| ROS2 package/install | `v2.0.0` | Default installation path: `/root/ros2_demo/install`, package name `robobaton_4p_ros2_demo`. Source updates or local rebuilds do not establish the target board's installed revision or an official upgrade; check its actual manifests and loaded libraries. Before use, complete the corresponding path's actual checks per [ROS2 Demo Usage](usage/ros2-demo.md), [non-ROS Demo Usage](usage/non-ros-demo.md), and [Saving Data](usage/save-data-guide.md). |

Feature additions, fixes, and compatibility changes are in [Changelog](changelog.md).

The online documentation continues to update based on user feedback; there is currently no separately pinned `stable` documentation version. Documentation revisions follow the policy above; Read the Docs `latest` is a deployment identifier, not a software version. An official software release does not mean target-board runtime checks can be skipped. The public camera parameter set supports `25/30/40/50/60fps`, default `30fps`; the saving and ROS2 paths should be judged by actual results, exit codes, manifest, and target-board environment checks.

Current guides cover V2 software identified as `2.0.0` and the explicitly unreleased source updates in the changelog. An identical version string does not prove an identical artifact composition: check runtime manifests, actually linked libraries, and matching instructions. Match ICM-42670-P headers, libraries, consumers, and configuration as one set. Native rates are `25/50/100/200/400/800/1600Hz`, default `800Hz`; unsupported rates are explicitly rejected, not silently resampled. Documentation revisions do not establish board or system acceptance.

Hardware identity, software `2.0.0`, documentation revision, and each SO ABI are independent dimensions, not substitutes for compatibility or acceptance. This change synchronizes documentation only; it changes no software behavior or release status.

## Current Implemented Capabilities

These are parameters and output contracts accepted by current public source, not acceptance of every mode, load, and duration combination.

| Path | Current capability | Constraints |
|---|---|---|
| Camera | `25/30/40/50/60fps`, default `30fps`; native NV12 `1280x1088`, discrete VSE `640x480`/`720x480`/`1280x720` | Full four-camera operation or single-sensor diagnostics only, not 2/3 cameras; rotation `180` only at `30fps`. Every entry uses only `vin_lpwm`. |
| IMU | Native `25/50/100/200/400/800/1600Hz`, default `800Hz` | `500/1000/2000Hz` are explicitly rejected, not resampled. FIFO order and measured TMST define samples; INT1 only wakes acquisition, without per-packet GPIO identity or an independent INT1-to-RAW observer. |
| non-ROS | Four H.264/H.265 RTSP streams, with either ROS1 bag or H.264 MP4 saving | Bag and MP4 are mutually exclusive; MP4 requires H.264 and all four cameras. Standalone UART/CAN examples do not establish peripheral or combined-load acceptance. |
| ROS2 | raw/compressed Image, CameraInfo, exposure observations, IMU, temperature, optional FSYNC | No RTSP, TF, or calibration; successful publication is not actual DDS reception. |
| Exposure/FSYNC | Exposure freezes the latest post-acquisition ISP estimate; FSYNC defaults off, only `800/1600Hz` | Exposure `status=1` is estimated and `status=0` unavailable; FSYNC uses chip tags/deltas, bounded measured endpoints, and unique RAW association, not certified frame-effective exposure or exposure synchronization. Explicit exposure-midpoint test mode remains only an estimate; see [Data Contracts](development/data-contracts.md). |

Camera capture uses `SCHED_FIFO/60`, the IMU acquisition owner `SCHED_FIFO/20`, and non-ROS IMU consumers and ROS2 IMU publication `SCHED_RR/3`; the old IMU `SCHED_FIFO/30` observer is removed. Required realtime scheduling failure rejects startup without silent downgrade or automatic IRQ, debug, or system realtime-quota changes. The camera `500µs` capture window and IMU `200µs` admission gate remain, without IRQ, current-host-time, or nearest-neighbor fallback. Public time is `CLOCK_REALTIME` and may repeat or step backward; RAW is internal identity/association only, and host burst observations must not substitute for sample/trigger times. See [Data Contracts](development/data-contracts.md).

(capability-verification-boundary)=
## Capability and Verification Boundaries

| Area | Current conclusion and user-facing limits |
|---|---|
| High frame rate and FSYNC | The current composition has non-ROS `60fps` + `1600Hz` FSYNC console association observations for approximately `300s` under CPU/BPU load. This supports only that association observation, not saved-image decoding, ROS2 throughput, or losslessness of all data. |
| Bag pressure and group drops | Default minimum drop interval is `10`, measured by contiguous `source_group_order`, not producer `group_id`. Only fully encoded, unclaimed complete four-camera groups are eligible; writer-claimed groups stay protected. Without a legal old or incoming group to drop, stop, drain to a readable partial bag, and exit nonzero. Intentional alternate saving explicitly requires setting the minimum interval to `2`. Historical high CPU/storage pressure exhausted the policy before `300s`; that result is not rewritten as a fix or pass. On eMMC/TF, keep bag or MP4 as the only high-throughput disk-writing task where possible, without added storage write stress. This reduces contention risk, not a guarantee of sustained losslessness. A correct policy stop is not sustained or all-sensor acceptance; every dropped group means `data_complete=false`. See {ref}`Saving Data <persistence-fps-boundary>`. |
| Sample completeness | Fixed premature IMU admission closure at bag image stop, ROS2 callback rejection before producer quiescence, and context shutdown before normal signal cleanup. Normal finalization quiesces the producer before draining consumers. Exact historical DDS loss identity/cause remains unrecoverable; equal short-smoke counts do not close sustained-integrity gaps. Neither continuous saved sequences nor bag completeness prove every hardware sample was saved. `allow-counted` permits observable rejections; `strict` fails on rejection. Neither guarantees zero loss under arbitrary load. |
| ROS2 rate and SHM | After the fix, a `30fps`/`1600Hz` short smoke has equal producer, sink, and DDS counts. This does not establish the historical difference's root cause or promise sustained `60fps` across all paths; earlier high-rate operation missed its target. Per-participant `256 MiB` SHM is capacity budgeting, not a historical initialization-root-cause fix; specialized investigation is paused. Disabled metrics mean unavailable; enabled metrics count normal sink `publish()` returns, not DDS receipt. |
| Long recording | The current composition's `8h` MP4 + FSYNC recording has not started. Sustained operation still needs verification with a single recording write workload; added storage write stress is not a prerequisite. Historical `8h` results cannot certify this composition; current long-recording acceptance is not claimed. |
| Capture and startup | Long-tail LPWM `500µs` window fail-closed stops remain unresolved. FIFO/TMST redesign does not establish a BSP GPIO/IRQ or LPWM repair. The leading FSYNC-tagged packet branch waiting for an absolute right endpoint and measured Arm is implemented, but explicit real-board execution of that special branch is not proven. FIFO enabling past the earliest measured ODR guard rejects startup; overflow, bad packets, and clock/epoch ambiguity remain fail-closed. |
| Encoding | Native bag JPEG strips private JPU APP9 without changing the ROS2 JPEG plugin. Clean bag JPEG decoding does not close H.264 RTSP `60fps` missing-reference/slice warnings. |
| USB/CAN | The updated matching V2 Buildroot image integrates USB3 Host/Device switching with RNDIS, CDC ECM, four-camera UVC, ADB, and dedicated MSD, defaulting to RNDIS. Application updates do not add it to older images; see [USB Interface Functions and Switching Limits](usage/usb-gadget-switch.md). Image integration does not certify computer enumeration, video reception, disk ejection, repeated switching, or reboot behavior. State-dependent and asymmetric USB throughput remain unresolved. CAN application features do not establish matching-BSP payload integrity, sustained throughput, combined-load, latency, or error-recovery acceptance; no throughput is promised for the current system composition. |
| TF and single-sensor diagnostics | Do not remove the TF card or cut power during recording or writes. Finalize normally, sync, and successfully unmount before removal; see [TF Card Usage](getting-started/tf-card.md). Single-camera diagnostics are user-confirmed. |
| System time and runtime dependencies | [NTP Sync](time-sync/ntp-sync.md) covers automatic boot-time synchronization, board-side server changes, private LAN sources, and manual recovery. UTC is not retained over power loss without a battery. A running process and realtime semantics do not certify absolute UTC; check peer selection and system synchronization before acquisition. Real-board cold boot, late connectivity, and sustained lock still need verification. Complete availability of other runtime dependencies such as `python3`/`libstdc++` remains to be confirmed; package verification does not validate every runtime dependency. |

Judge functionality, actual saved/received payloads, exit status, and the target environment separately. Accepted parameters, association JSON, complete containers, and historical individual results do not substitute for current-composition acceptance.


## Known Limitations

- TF extrinsics, camera intrinsics, and distortion calibration are currently not provided.
- ROS2 does not provide RTSP; use non-ROS `/root/demo` when RTSP is needed.
- Camera applications exclusively hold camera/VIO/encoding resources; before switching, exit the old application and keep `cam-service` running.
- non-ROS camera, RTSP, ROS1 bag, H.264 MP4, and the ROS2 image node publicly support `25/30/40/50/60fps`, default `30fps`; `--rotate 180` still supports only `30fps`.
- Every camera acquisition entry supports only `vin_lpwm` (VIN LPWM hardware triggering); `none`, free-run, and `software_gpio` paths are no longer available.
- CameraInfo only has width/height, and IMU orientation is unavailable.
- Camera ABI 3.0 `exposure` freezes the latest ISP observation per frame; `status=1` is only an estimate and `0` means unavailable. Applied-frame identity, an error bound, and actual exposure midpoint are not guaranteed.
- FSYNC defaults off and can be enabled only at `800/1600Hz`; only `status=1` is a unique trigger-to-sample association. It changes neither IMU phase nor exposure-sync guarantees. Container completeness is not association completeness or full DDS delivery.
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
