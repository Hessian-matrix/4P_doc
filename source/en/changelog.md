# Changelog

This file records user-visible updates in the RoboBaton 4P public delivery, following the shared [Documentation Version Policy](release-and-support.md#documentation-version-policy). Documentation revisions on this page do not automatically change software versions and are distinct from SO SONAME/ABI versions.

## 2.0.62 - 2026-11-06

- Document the independent calibrated four-camera `panorama_demo`, trusted-LAN read-only Web preview, offline JPEG input, and build/packaging workflow, distinct from four-tile mosaic RTSP and the combined-capture homepage.
- Specify schema 7 KB4/extrinsics, fixed mounting/pixel orientation, infinity/finite-sphere projection, blind regions/near-field parallax, latest-only drops, and pending human review. Add no board, performance, or seam-accuracy acceptance claims; software versions and SO ABI remain unchanged.
- Describe reliable-overlap exposure balancing and low-frequency illumination transitions for RGB/NV12 and the 360° join, preserving single-view high-frequency detail and blind regions. This neither controls camera exposure nor removes arbitrary-depth parallax or guarantees flicker-free motion.

## 2.0.61 - 2026-11-05

- Fix the public exposure estimate's frame-association semantics: each acquisition worker exclusively owns zero-initialized per-session state; a getter obtained while acquiring raw hardware frame N estimates adjacent N+1 only. Match acquired hardware frame-ID adjacency with uint32 wrap, never normalized group IDs or SDK `source_frame_id`. Frame-set warmup primes the state without extra image buffering or delivery delay.
- The first acquired frame without a predecessor, hardware gaps, or invalid predecessor queries yield UNAVAILABLE/all-zero exposure, never stretched across gaps. Query failure at N makes N+1 unavailable; a valid predecessor can still estimate N. `duration_ns` comes from SDK seconds. Source identity, opaque source time, and RAW query-completion time retain the older getter's original values rather than target-image values. Bag/tee/MP4/ROS2 forward unchanged; consumers must not shift another frame.
- Default trigger timestamps remain unchanged. Opt-in midpoint testing uses the matched estimate and still fails closed when unavailable, without fallback. Align the three public-header comments and bilingual current contracts without public ABI-layout, SONAME, or software-version changes. Only documentation revision becomes `2.0.61`; preserve historical entries.
- This fixes estimated association semantics only and remains ESTIMATED: no applied-exposure certificate or measured physical-error bound, and no physical-accuracy, AE behavior/convergence-performance, or real-board acceptance claims. Validation results are supplied separately; this entry is not passing evidence.
- Fixed N→N+1 is only the chosen estimated-association rule. Real AE can have a different effective lag; do not interpret the rule as a universal AE application delay or a per-frame applied-exposure guarantee.

## 2.0.60 - 2026-11-05

- Move the public IMU contract to matching kernel IIO V4 / ABI6.0: `libicm42670.so.6.0.0`, SONAME `.6`, and nine `ICM42670_X5_6.0` exports. Config remains32 bytes; sample retains its original160-byte prefix and expands to192 bytes. Update headers/libraries/consumers/modules together.
- Independent FSYNC diagnostics default on and can be disabled through non-ROS YAML/CLI and a ROS2 startup parameter. Timing JSON becomes `robobaton_imu_timing_v3`; bag/ROS2/MP4 IMU CSV preserve original time fields and append six real per-sample diagnostic fields. Tagged FIFO fields retain delta microseconds, never absolute ticks; unavailable edges retain0/unknown uncertainty.
- FSYNC diagnostics never correct ordinary host/tmst or camera time, perform nearest-neighbor frame/group matching, or certify physical synchronization accuracy. Camera and Web time contracts retain their meanings. This documentation revision adds no real-board acceptance claims and does not change product software VERSION.

## 2.0.59 - 2026-11-04

- Integrate remote `2.0.58` Web preview/attitude/recording, official hardware, and USB/system-image documentation with parallel IIO/manual-exposure changes. Preserve remote versioned history; label parallel former `2.0.16`–`2.0.18` entries as topic-specific checkpoints instead of assigning competing topics the same revision heading. Historical ABI3/ABI4 and measurement scope remain historical, not current evidence.
- Current IMU contract is kernel IIO V3 / public ABI5: `libicm42670.so.5.0.0`, SONAME `.5`, and nine `ICM42670_X5_5.0` exports. V2 modules are incompatible; match headers/libraries/consumers/modules without cross-major shims, userspace SPI/spidev, FSYNC, or failure fallback.
- Final default is HO (camera observer + IMU host); the other three startup pairs remain for comparison. Host preserves MONOTONIC estimates, tmst adds RAW sample mapping, and output explicitly bridges realtime, without certifying physical sampling/exposure synchronization accuracy. Default YAML retains Web on, RTSP off, IMU `800Hz`, and auto exposure on. Explicit manual exposure and restart boundaries remain.
- Web IMU SSE cleanly moves to schema2 with explicit realtime/MONOTONIC/RAW and bridge evidence, string u64 values, and null host sample uncertainty. Remove old time aliases and GPIO/mapper source counters. Axes/filter arrays remain unchanged; attitude integrates selected native-clock time. Distinguish dynamic `callback_window` from startup-auto `producer_session` health.
- Fix dependent-frame drops from the fixed four-frame WebRTC queue while pacing a large keyframe: retain backlog according to frame rate and the existing age budget, still subject to byte, age, and global-memory bounds. The matched integrated package passes a short non-ROS HO smoke covering four-camera 30fps Web preview/attitude, dynamic bag/MP4 recording, complete file readback, and normal shutdown. This does not establish ROS2, four-way, physical-accuracy, pressure, or long-recording acceptance.
- Synchronize bilingual usage, APIs, data contracts, build/deployment guidance, and READMEs. Only documentation revision becomes `2.0.59`; software versions and release status are independent. This update does not certify system reboot or a new software release.

## 2.0.58 - 2026-11-03

- Update matching V2 Buildroot USB3 Host/Device commands, RNDIS/ECM addressing and DHCP, real four-camera UVC, ADB permission, dedicated MSD, and boot defaults. State exclusive ownership, safe ejection, independent management, and the unflashed real-board verification boundary.
- The image candidate preinstalls complete current-source non-ROS `/root/demo/` and ROS2 `/root/ros2_demo/install/` packages, including config, launch, matching producers, and runtime dependencies. The ROS2 underlay is preinstalled at `/opt/ros/humble`, without first-boot extraction. Only non-ROS retains the existing boot-start policy; the two acquisition paths cannot run concurrently.
- This documentation revision does not change software versions or SO ABI/SONAME. Building an image candidate is not public release, flashing, or USB/sensor system acceptance.

## 2.0.57 - 2026-11-03

- Remove “no GND on this 2P port” and its Chinese equivalent from the CAN note in both wiring diagrams, retaining H-to-H/L-to-L, pin mappings, and other wiring guidance.
- Update images and the documentation revision only; software versions, public SO ABI/SONAME, and hardware definitions remain unchanged.

## 2.0.56 - 2026-11-03

- Correct USB guidance against the matching V2 Buildroot system: RNDIS on the USB3 controller by default, USB-specific addressing/DHCP without gateway/DNS, and distinctions between controller selection, physical routing, function classes, and negotiated speed.
- Remove the unintegrated `switch_usb_gadget` five-mode menu and `/etc/usb_gadget_default` persistence steps. Explain ECM network configuration, the missing UVC video backend, ADB acceptance limits, and MSD ownership/unmounting risks. Retain the independent-management prerequisite and no switching during acquisition/saving.
- Align First Power-On, release boundaries, and version information. Documentation only: no system-default, SDK/board artifact, software-version, or public SO ABI/SONAME changes; no mode-switching, re-enumeration, reboot, or performance acceptance.

## 2.0.55 - 2026-11-03

- Add a browser-workspace illustration to Product Introduction. English pages use a translated English-interface image, also reused by First Power-On and non-ROS usage, retaining the original camera images and example state.
- Document direct phone/tablet browser preview on the same LAN in Product Introduction, First Power-On, and non-ROS usage: no app/SSH, narrow-screen scrolling, network reachability, autoplay and WebRTC/H.264/device-performance limits, plus device-side recording and trusted-network boundaries.
- Reverse GH1.25 Ethernet pin numbering 1–8 in both wiring diagrams and synchronize wire colors and RJ45 annotations. Warn that the supplied cable is not twisted pair, may lose packets, and is for testing/temporary use only; reliable Gigabit connections require a suitable user-prepared twisted-pair cable.
- Update documentation and illustrations only; software versions and public SO ABI/SONAME remain unchanged. This is not mobile-compatibility or network-reliability acceptance.

## 2.0.54 - 2026-11-03

- Update non-ROS Demo features and usage order around the actual browser workspace: boot-autostart entry, four videos, attitude/bias, six-axis data/temperature/trends, language and diagnostics, Web recording, and final-outcome checks. Reuse the workspace illustration.
- Distinguish browser fixed storage from YAML/CLI startup recording, no eMMC fallback for unmounted TF, and stopping recording from releasing camera/IMU resources. Require graceful shutdown of autostart before manual or standalone Demo runs; MP4 needs no RTSP network output. Complete the YAML drop-interval example and update verification guidance.
- Revise bilingual documentation only; software versions and public SO ABI/SONAME remain unchanged. No board deployment, process control, reboot, or new hardware-acceptance claim.

## 2.0.53 - 2026-11-03

- Add the supplied board's pre-flashed system, automatic boot startup of `sensor_demo`, factory browser URL, four-camera/IMU preview, and Web recording steps to First Power-On, with an interface illustration excluding browser chrome. Distinguish factory pre-flashing from public image-download status.
- Align Quick Start and non-ROS guidance to avoid duplicate launches, distinguish stopping recording from exiting the application, and clarify recording completeness, fixed storage, and trusted-LAN boundaries. The manual RTSP example explicitly passes `--rtsp`.
- Update only the documentation revision; software versions and public SO ABI/SONAME remain unchanged. This documentation update does not flash, deploy, or reboot a board or add hardware-acceptance claims.

## 2.0.52 - 2026-11-03

- Use `CH` / `EN` target-language abbreviations on the page language button, retaining full accessibility labels, language preference, and existing switching behavior. Synchronize bilingual usage guidance; software versions and public SO ABI/SONAME remain unchanged.

## 2.0.51 - 2026-11-03

- Synchronize bilingual guidance for the page language toggle, browser language preference, and matching online documentation. Switching does not reload, recreate WebRTC/SSE/the attitude Worker, or reset options, recording, or accepted bias.
- Distinguish the Internet requirement for online documentation from the device page's embedded offline assets. Only the documentation revision changes; software versions and public SO ABI/SONAME remain unchanged, without board deployment or hardware-acceptance claims.

## 2.0.50 - 2026-11-03

- Synchronize bilingual guidance for the compact camera heading aligned with source parameters and removal of per-camera header rows/expansion buttons; CAM labels overlay top-left corners and playback states bottom-right corners.
- Document double-click or focused Enter/Space expansion/restore and `Esc` returning to the grid, without recreating WebRTC, SSE, or the attitude Worker or changing device recording.
- Maximize the four-video grid against remaining width/height while preserving source aspect ratio and the complete uncropped, unstretched image. Software versions, APIs, filenames, and public SO ABI/SONAME remain unchanged. Only the documentation revision changes; this is not a software release or hardware-acceptance claim.

## 2.0.49 - 2026-11-02

- Synchronize bilingual guidance for the always-visible single-form recording card and responsive four-column workspace: at ≥1440px, equal-height columns prioritize cameras, with attitude slightly wider than telemetry. At 1100–1439px, recording spans a row below three columns; at 768–1099px, cameras/recording each span a row while attitude/telemetry sit side by side; mobile stacks. Compact viewport filling and panel-internal scrolling apply only at ≥1440px wide and ≥680px high.
- Document default-visible recording controls/state/duration/bytes, initially closed advanced options and detailed state/use boundaries, and errors, uncertain-command messages, and stopping/finalization notices outside the folds. Invalid hidden advanced values open the section before validation feedback.
- Clarify that collapsing does not navigate, recreate connections/the Worker, or reset options/bias; refresh still resets browser-local state, and `Esc` only exits video expansion. Closing the page/network does not stop recording; storage/API/native-data contracts and the unauthenticated trusted-LAN boundary remain unchanged.
- Only the documentation revision changes. Historical version entries, software versions, and public SO ABI/SONAME remain unchanged, without a software-release, deployment, or hardware-acceptance claim.

## 2.0.48 - 2026-11-02

- Label cameras CAM1–CAM4 for internal indices 0–3. Enlarge compact-desktop frames at the source aspect ratio, reduce the camera card's horizontal whitespace, and remove its explanatory footer while keeping all three outer cards equal in height.
- APIs, recording filenames, software versions, and public SO ABI/SONAME remain unchanged; only the documentation revision changes, without a software-release or hardware-acceptance claim.

## 2.0.47 - 2026-11-02

- At widths ≥1100px, give the camera, attitude, and raw six-axis telemetry card frames equal heights with aligned top and bottom edges. Compact desktops still fill the workspace; video retains its source aspect ratio and narrower screens still stack the cards.
- Only the documentation revision changes; software versions and public SO ABI/SONAME remain unchanged, without a software-release or hardware-acceptance claim.

## 2.0.46 - 2026-11-02

- Move camera titles, states, and expansion buttons into their own row above the image to avoid obscuring the source. Preserve source aspect ratio, expansion, and `Esc`.
- Fill the compact-desktop workspace with equal-height attitude and telemetry cards. Make attitude slightly wider and grow the model/traces with available space; scroll overflow inside each card while narrower screens retain normal stacking.
- Only the documentation revision changes; software versions and public SO ABI/SONAME remain unchanged, without a software-release or hardware-acceptance claim.

## 2.0.45 - 2026-11-02

- Synchronize the wider Web homepage layout: at widths ≥1100px, attitude is on the left and raw six-axis telemetry/traces on the right, aligned at the top; narrower windows still stack them.
- Preserve source-aspect four-video playback, calibration/reset, the recording modal, and diagnostics. Only the documentation revision changes; software versions and public SO ABI/SONAME remain unchanged, without a software-release or hardware-acceptance claim.

## 2.0.44 - 2026-11-02

- Synchronize bilingual single-homepage guidance, removing left-side page navigation, separate hash views, and the outside recording shortcut from current instructions while preserving historical version entries.
- Prioritize the four-video grid beside a narrow sidebar containing attitude, calibration/reset, raw six-axis values, and traces, with inline expandable diagnostics below. Preserve source-aspect `contain`, single-camera expansion/`Esc`, compact desktop/scrollable-sidebar behavior at ≥1100px wide and ≥680px high, and normal document scrolling in smaller windows.
- Document the single form in the native “录制与保存” (Recording and Saving) modal, always-visible homepage device status/options summary, and Close/`Esc` focus restoration without stopping recording, resetting options/bias, or recreating connections/the Worker. Refresh still resets browser-local options and bias.
- Existing APIs, recording limits, freshness/uncertain-command safeguards, storage paths, native saving, and security boundaries remain unchanged. Only the documentation revision changes; software versions and public SO ABI/SONAME remain unchanged, without a software-release, deployment, runtime-acceptance, hardware-synchronization, or accuracy claim.

## 2.0.43 - 2026-11-02

- Synchronize camera-first desktop Overview guidance: at viewport width ≥1100px and height ≥680px, narrow left-side vertical navigation accompanies a compact title and four health summaries on the top row. A larger 2×2 video grid is centered in the camera column, with its panel hugging the grid.
- The narrow right sidebar shows a small IMU model, three angle readings, and vertical calibration/reset controls. A separate recording shortcut card retains current options, status, and full configuration/stop access. Cameras maximizes its centered grid; IMU retains full readouts and traces.
- Preserve full-source-aspect `contain` video, single-camera expansion and `Esc`, and connections/bias across view switches. Narrow and short screens use stacked content and normal document scrolling. Only the documentation revision changes; software versions and public SO ABI/SONAME remain unchanged, without a software-release, board-deployment, hardware-synchronization, or accuracy claim.

## 2.0.42 - 2026-11-02

- Shrink the desktop camera panel around its 2×2 grid to reduce empty side margins. Overview gives remaining width to the attitude panel; Cameras centers the complete group.
- Preserve full-image aspect ratio, single-camera expansion, short-screen panel scrolling, and narrow-screen responsiveness. Acquisition, encoding, recording, and attitude computation are unchanged.
- Synchronize bilingual guidance and update only the documentation revision. Software versions and public SO ABI/SONAME are unchanged; this is not a software release or board-deployment claim.

## 2.0.41 - 2026-11-02

- Correct desktop four-video frames to shrink to the source aspect ratio in a compact centered grid, instead of widening containers and adding bars. The full image remains uncropped and unstretched; source-image bars remain.
- Allow camera-panel scrolling on short screens to keep titles and expand controls readable. Small windows and mobile devices retain normal document scrolling; single-camera expansion remains aspect-preserving.
- Synchronize bilingual usage guidance and update only the documentation revision. Software versions and public SO ABI/SONAME are unchanged; this is not a software release or board-deployment claim.

## 2.0.40 - 2026-11-02

- Synchronize bilingual height-adaptive desktop workspace guidance: compact chrome at viewport width ≥1100px and height ≥680px, full-image aspect-preserving `contain` video, and panel scrolling for long errors/help. Smaller windows and mobile devices retain normal document scrolling.
- Document that Overview's start-recording shortcut directly uses the current Recording-page control values and reuses validation, live-state/capability limits, command locking, and device acknowledgment/queries. Overview shows only the selected format/storage/frame-skip summary, status, and a configuration/stop link, without duplicate configuration or a stop button.
- Clarify that choices remain page-local and reset to page defaults on refresh, without persistence. Stopping remains a Recording-page action; closing the page or switching views does not stop device recording.
- Update only the documentation revision. Software versions and public SO ABI/SONAME remain unchanged; no authentication is added, and this is not a software release, deployment claim, or long-recording/zero-loss acceptance claim.

## 2.0.39 - 2026-11-02

- Synchronize the Web recording page, ROS bag/four-camera H.264 MP4 start/stop/status, and fixed storage paths. CLI/YAML startup recording remains; cameras, IMU, and preview run independently.
- Clarify final drain/remux results, recording-failure isolation, timeout-state queries, recording across disconnects, and the unauthenticated trusted-LAN boundary. Dynamic MP4 health covers only its callback window, not whole-process final health.
- Update only documentation revision, without software-version or public SO ABI/SONAME changes. This is not a software release, TF fault-matrix acceptance, or long-term-stability acceptance.

## 2.0.38 - 2026-11-01

- Synchronize bilingual guidance for preview-only filtering before decimation, separate SSE arrays, approximately 64ms default low-frequency group delay, gap/invalid-input handling, and matched runtime rebuilding.
- Clarify that the device only filters; attitude and bias remain browser computations. Raw stationary-quality checks and the 0.002 rad/s gate remain, with a 6-second bias-tracking time constant after qualifying windows.
- Short-window motion admission retains raw angular rates so filter delay cannot hide late turns; invalid observations discard partial automatic windows and interrupt manual calibration without replacing accepted bias.
- Update only the documentation revision. Native sampling, raw axes, saving, software versions, and public ABI/SO SONAME are unchanged. This is not a software release or absolute-heading/long-term-stability acceptance.

## 2.0.37 - 2026-11-01

- Synchronize bilingual source-intrinsic-aspect-ratio layout guidance for Overview, the camera grid, and single-camera expansion: no cropping, stretching, or viewport-dependent fixed height; bars already present in the source remain.
- Synchronize approximately 3-second automatic stationary three-axis bias estimation, window-quality checks, resets after detected motion/vibration/sparse data/gaps, and the ≤0.002 rad/s residual gate and rate-limited exponential tracking once bias is known. Accepting an automatic estimate neither jumps attitude nor re-zeros heading. Status text indicates automatic estimation/tracking; manual calibration remains available and rejection preserves known bias.
- Clarify that all integration uses corrected gyro rates, without Yaw freezing, a hard deadband, or display damping. Same-session reset retains bias; a new source/reload clears it for stationary re-estimation. Slow rotation below the threshold may be absorbed, while genuine rotation ≥0.005 rad/s after calibration must remain measurable. Six-axis preview still provides no absolute or drift-free heading.
- Update only the documentation revision. Native sampling, telemetry schema/rate, saving, device-side computation, HTTP API, software versions, and public ABI/SO SONAME are unchanged. This is not a software release, board-deployment claim, or long-term-stability/system-acceptance claim.

## 2.0.36 - 2026-10-31

- Synchronize bilingual four-view layout, direct hash navigation, responsive top navigation, and the contents and actual diagnostic fields of Overview/Cameras/IMU/Diagnostics.
- Clarify that view switching reuses WebRTC, SSE, and the attitude Worker while preserving browser gyro-bias calibration. Calibration is available in Overview and IMU; refresh still clears it. Six-axis relative Yaw and the absence of absolute heading remain unchanged.
- Update only the documentation revision. No new HTTP API, authentication, or hardware controls; software versions and public ABI/SO SONAME are unchanged. Deployment means only an authorized local runtime-package update on the user's device, not a software-version release or a full-acceptance claim.

## 2.0.35 - 2026-10-31

- Synchronize bilingual instructions for explicit stationary gyro-bias calibration, quality checks and rejection, retention/clearing across relative-heading resets, time discontinuities, and source sessions, plus actual-stillness, temperature, and unobservable-heading limits.
- Clarify that there is no automatic Yaw freeze/deadband or continuous bias learning during motion. Deployment requires rebuilding the embedded helper and full runtime package and restarting the application normally; a browser refresh alone is insufficient.
- Update only the documentation revision. Native sampling, telemetry schema/rate, saving, device-side computation, software versions, and public ABI/SO SONAME are unchanged, without implying board deployment, acceptance, or a new software release.

## 2.0.34 - 2026-10-31

- Synchronize bilingual client-side attitude preview, gravity alignment/relative heading, stale/reconnection behavior, computation location, and accuracy limits.
- Update only the documentation revision; software versions and SO SONAME/ABI are unchanged, without implying deployment or a new software release.

## 2.0.33 - 2026-10-31

- Synchronize bilingual Windows vertical-stripe troubleshooting, the H.264 transform fix, whole-package update/application-restart requirements, and SDK/hardware-decoder compatibility limits.
- Update only the documentation revision; software versions and SO SONAME/ABI are unchanged.

## 2.0.32 - 2026-10-30

- Record the limited scope of the real four-video/IMU smoke and document Web pacing, IPC resume, and fresh-frame age-race fixes.
- Update only the documentation revision; software versions and SO SONAME/ABI remain unchanged. No expanded two-computer, GPU, resource, or saving/FSYNC acceptance claim.

## 2.0.31 - 2026-10-30

- Synchronize Chinese/English LAN preview usage, switches, ports, trusted-LAN/hardware-decoder boundaries, troubleshooting, and pinned Go build instructions.
- Update documentation independently; software `VERSION` and SO SONAME/ABI remain unchanged. Host synthetic streams do not establish board or GPU acceptance.

## 2.0.30 - 2026-10-30

- Simplify Wi-Fi configuration wording to focus on device-side commands, configuration, and troubleshooting.
- Simplify pin explanations in Time Synchronization and PPS Sync while retaining PPS wiring, logic levels, device identification, and usage steps.
- Update only the documentation revision to `2.0.30`; software versions and SO SONAME/ABI are unchanged.

## 2.0.29 - 2026-10-30

- Simplify the TF card introduction by removing board-applicability and non-boot/flashing scope notes.
- Remove hardware minor-revision labels from hardware guidance and wiring-diagram artwork. Interfaces, pin numbers, signal order, and electrical parameters are unchanged.
- Update only the documentation revision to `2.0.29`; software versions and SO SONAME/ABI are unchanged.

## 2.0.28 - 2026-10-30

- Simplify TF card usage and support guidance to data safety: no removal during recording or writes, normal finalization, synchronization, and unmounting.
- Update only the documentation revision to `2.0.28`; software versions and SO SONAME/ABI are unchanged.

## 2.0.27 - 2026-10-30

- Simplify PPS guidance to wiring, 3.3V logic and safety requirements, device identification, and `ppstest` usage; remove voltage derivation and align hardware and support pages.
- Maintain usage instructions in `4P_doc`, adding debug-console passwordless-login controls and standalone IMU final-status guidance. Reduce non-ROS Chinese/English READMEs and the ROS2 README to repository overviews, minimum run commands, and documentation links.
- Update only the documentation revision to `2.0.27`; software versions and SO SONAME/ABI are unchanged.

## 2.0.26 - 2026-10-30

- Add eMMC/TF recording write-pressure guidance: choose bag or MP4, avoid other concurrent high-throughput disk writes, and defer copying, extraction, and conversion until normal finalization. A single recording still depends on media capability and actual payload size; zero loss is not guaranteed.
- Align recording and long-recording support boundaries. Update only the documentation revision to `2.0.26`; software versions and SO SONAME/ABI are unchanged, with no new real-board or sustained-recording acceptance claims.

## 2.0.25 - 2026-10-30

- Document 3.3V logic for the independent PPS input on CN2 pin 4, level conversion, and prevention of back-feed when unpowered; align hardware and known-limitations pages.
- Update only the documentation revision to `2.0.25`; software versions and SO SONAME/ABI are unchanged. No new voltage measurements or external PPS acceptance claims.

## 2.0.24 - 2026-10-30

- Use an English-labeled wiring diagram on the English hardware page and update the full-resolution download. The Chinese diagram is unchanged; pin numbers, signal order, and board orientation remain consistent.
- Update only the documentation revision to `2.0.24`; software versions and SO SONAME/ABI are unchanged.

## 2.0.23 - 2026-10-30

- Add the full-resolution interface wiring diagram, original-image download, and reading guidance to both hardware-and-safety pages, with direct links from first power-on.
- Align XT30 `12–27 V DC`, UART1 CN1 4-pin, UART7 CN2 5-pin, and independent PPS pin numbers with the diagram. Correct old wiring descriptions in serial, PPS, data-contract, and troubleshooting pages; retain power-pin load, PPS electrical, and hot-plug limits.
- Update only the documentation revision to `2.0.23`; software versions and SO SONAME/ABI are unchanged, with no new real-board acceptance claims.

## 2.0.22 - 2026-10-30

- Add bilingual external 1 Hz PPS usage examples covering safe wiring, provider identification, `ppstest`, event interpretation, and stopping observation. Input events do not establish system-clock discipline or camera/IMU synchronization.
- Update only the documentation revision to `2.0.22`; software versions and SO SONAME/ABI are unchanged. Example output is quoted from LinuxPPS documentation, without new real-board acceptance claims.

## 2.0.21 - 2026-10-30

- Rename the final Wi-Fi troubleshooting section to “Stop Wi-Fi” to match `wifi_setup --disable`; this operation does not change wired network configuration.
- Update only the documentation revision to `2.0.21`; software versions and SO SONAME/ABI are unchanged.

## 2.0.20 - 2026-10-30

- Describe configuration and boot restore through the built-in Wi-Fi command in the unified system image, without additional script installation for normal use.
- Update only the documentation revision to `2.0.20`; software versions and SO SONAME/ABI are unchanged, with no new real-board acceptance claims.

## 2.0.19 - 2026-10-30

- Align bilingual Wi-Fi usage guidance around `/usr/bin/wifi_setup` and `/etc/init.d/S99wifi_setup` as the configuration and boot-restore entries.
- Clarify that saved configuration is in `/userdata/wifi/current.conf` and boot restore still requires explicit opt-in through `/userdata/wifi/autostart.enabled`.
- Update only the documentation revision to `2.0.19`, independently of software versions and SO SONAME/ABI, with no new real-board acceptance claims.

## 2.0.18 - 2026-10-30

- Reframe NTP documentation as a board-side usage guide: automatic synchronization, server changes, private LAN sources, temporary start/stop, synchronization checks, and manual recovery. Remove production instructions intended for system integrators.
- Align bilingual first-use instructions, the time synchronization overview, and Demo READMEs; distinguish automatic discipline from manual one-shot calibration. Documentation only; software versions and SO ABIs are unchanged.
- Align bilingual specification tables with the latest product information, including the DC 12 V / 1.5 A adapter. Normalize interface names, units, spacing, and quantity notation; keep the composition table's quantity column on one line and preserve the responsive drawing layout.
- Use RoboBaton 4P V2 consistently in HTML site titles, correcting the sidebar site name, browser tabs, and English home-page heading without changing actual product parameters.
- Vertically center content in all bilingual documentation tables so short entries align with multiline cells. Keep Product Introduction parameter names on one line and preserve existing horizontal alignment and wrapping elsewhere, including horizontal scrolling within tables on narrow screens. Parameter and body content are unchanged.

## 2.0.17 - 2026-10-30

- Add the V2 main-board dimensions and mounting-hole drawing to Product Introduction and fix the old image reference. Reduce the main-board drawing and place it beside the camera-board drawing, wrapping on narrow screens. Both drawings identify the board and millimeter units.
- Synchronize bilingual product composition and parameters, correct the NV12 format description, and distinguish the non-ROS default YAML's `1600Hz` from the ROS2 default YAML's `800Hz`. Correct the Chinese home-page heading format. Documentation only; software versions, configuration, and SO ABIs are unchanged.

## 2.0.16 - 2026-10-30

- Document a private LAN chrony server and usage boundaries without Internet or any networking. Distinguish manual one-shot calibration from persistent time-source configuration.
- Clarify that saving configuration without a battery does not retain time, an isolated server's local clock does not certify UTC, and system-clock discipline services must not compete. Software remains `2.0.0`, with unchanged SO ABIs; no additional real-board acceptance is claimed.

## 2.0.15 - 2026-10-29

- Align bag and ROS2 stop, admission, and drain contracts; distinguish fixed shutdown defects from the historical DDS difference that still cannot be exactly attributed.
- Software remains `2.0.0`, with unchanged SO ABIs. Short smoke runs do not replace sustained-pressure, high-frame-rate, long-recording, or release acceptance.

## 2.0.14 - 2026-10-29

This revision synchronizes public documentation in both languages only. Software remains `2.0.0`; it changes no software behavior, releases no new software, and establishes no additional hardware, load, or long-duration acceptance.

### Documentation Synchronization

- Centralize accepted parameters, independent software/hardware/documentation/SO ABI versions, and verification boundaries on the support page. Align complete rebuild and migration requirements for ICM42670/SC132 ABI `3.0` and PRRTSP ABI `2.0`.
- Align FIFO/TMST, wake-only INT1, original burst host observations, backward realtime steps, default trigger stamps and explicit exposure-midpoint test mode, plus FSYNC, exposure, and realtime-scheduling contracts.
- Synchronize strict bag drop spacing, partial stops, producer/sink/DDS count distinctions, and JPEG/record-time semantics. High frame rate, pressure recording, and the current composition's `8h` recording do not establish complete acceptance; historical results cannot certify this composition.
- Add user-facing LPWM, RTSP, SHM, USB, CAN, RTC/UTC, and runtime-dependency limits. Retain single-camera diagnostics as user-confirmed.


## 2.0.13 - 2026-10-23

Record bag overload fixes and the added FIFO/TMST-led IMU ABI 3.0 migration. Documentation revision and software VERSION remain unchanged; IMU SONAME/ABI independently move for the incompatible semantics described below.

### Improvements and Fixes

- At image-burst or IMU high-water service points, the bag writer drains a snapshot of the current IMU backlog in bounded batches. Later arrivals wait for the next round, preventing a growing high-ODR deficit or indefinite image starvation. Queue capacities are unchanged; unbounded storage stalls can still lose data.
- Repeated oldest-complete-group replacement retires head eviction markers and checks the full committed record-order window before eviction. A claimed group's remaining frames stay protected; unready groups are not bypassed and ring slots are not overwritten. Evictions/rejections remain counted partial data. The bag fixes themselves change neither LPWM nor uncertainty checks; see below for the IMU architecture cutover.
- Clarify bag queue/writer-latency diagnostics and system-wide disk counters. Aggregate counters are not saving-device utilization or proof of payload completeness.
- IMU moves to ABI `3.0`, real file `libicm42670.so.3.0.0`, SONAME `.3`, and only `ICM42670_X5_3.0` for every current export. Field names/layouts remain unchanged; no old aliases, reexports, or compatibility shims exist. Synchronize headers, libraries, and every rebuilt consumer, remove old `.2` artifacts, and never substitute a lone SO or cross-major link.
- FIFO order and measured chip TMST define samples; FSYNC retains chip tags/deltas and measured endpoints, while INT1 only wakes acquisition. `host_timestamp_ns` becomes the RAW observation at the successful SPI FIFO burst completion, converted to realtime using that observation's bridge. Packets may share it; FSYNC deferral retains the converted value, it may precede publication, and it follows wall-clock steps. It is not IRQ-edge, sample, or exposure time. `sample_timestamp_ns` remains measured TMST-to-RAW-to-realtime, with unchanged `200µs` admission.
- GPIO notification sequence gaps are diagnostic, not proof of physical-edge/sample loss or independently fatal. Actual FIFO overflow, bad packets, ambiguous clocks, and invalid epochs still fail. This architecture changes neither LPWM nor kernel and does not fix the underlying GPIO/IRQ cause or guarantee zero loss under arbitrary load. Rebuild, synchronize, and repeat target-board acceptance; software version strings are not passing evidence.

## 2.0.12 - 2026-10-23

Clarify acquisition-latency troubleshooting conditions. Software versions and SO SONAME/ABI are unchanged.

### Improvements and Fixes

- Explain BSP per-transfer spidev dynamic-debug versus application logging, authorization for comparison experiments, and restoration of original flags. Passing with debug disabled is not a pass in the original environment; FIFO/INT1 identity, the `500µs`/`200µs` gates, and fail-closed behavior remain unchanged.
- Normal first FIFO packets also reject nonexistent fractional phases after Arm without consuming GPIO identity. GPIO event-gap detection remains active after the sequence wraps to zero. Both FSYNC modes retain the same timestamp and uncertainty gates.
- Fixed concurrent mutable-metadata access between a frame-set producer and group finalization. Internal dumps use the raw frame counter and RAW capture time; public consumers retain normalized frame IDs and the realtime timestamp contract.
- Arm uses only measured clock transitions accepted by the mapper. An incompatible bounded observation invalidates the old clock certificate instead of combining a new counter with a stale mapping. The `200µs` gate remains unchanged; neither nominal ODR nor arrival time replaces measured timestamps.

## 2.0.11 - 2026-10-22

Document acquisition-startup fixes. Software versions and SO SONAME/ABI are unchanged.

### Improvements and Fixes

- Frame-set warmup now discards unpublished frames before clock-map admission, exposure queries, and image transforms, avoiding startup failure on an unavailable first-frame capture map. Delivered frames still require exact capture matches with the unchanged `500µs` window limit.
- Retain leading FSYNC packets until a later absolute TMST arrives, then reconstruct bounded intervals using the measured startup clock transition instead of failing solely because no preceding FIFO endpoint exists. No nominal-ODR timestamps are synthesized; GPIO identity, unique rollover, the `200µs` limit, and drop policies remain unchanged.
- LPWM fatal diagnostics distinguish a rejected exact record from an absent trigger and snapshot that lookup's counter values, RAW bracket, and history endpoints. Timestamps, bounds, ABI, and fail-closed behavior are unchanged; this does not claim a sustained-acquisition fix.
- Fixed an uninitialized frame-set release risk when realtime bridging or exposure-midpoint validation fails. Clear the output descriptor before validation, preserving pending-frame ownership without delivering a partial group.
- Startup reconstruction checks the shared-Arm and one-full-ODR-later hypotheses separately, accepting only a unique feasible hypothesis and rejecting nonexistent fractional phases between them. Document sustained FIFO/INT1 identity failures and fail-closed boundaries; repeated-start success is not a sustained-stability guarantee.

## 2.0.10 - 2026-10-22

Add bilingual instructions for TF cards as data disks. Software versions and SO ABI are unchanged.

### Improvements and Fixes

- Document TF (microSD) versus system eMMC identification, filesystem selection, manual mounting, acquisition output paths, normal unmounting, and enumeration troubleshooting. Check SD type and mount device number before saving to avoid writing into RAM or the system disk after a failed mount. No automatic formatting or mounting.

## 2.0.9 - 2026-10-22

This revision aligns both public language trees with the current V2 product. Software remains `2.0.0`; SO versions and ABI are unchanged, without a new hardware-acceptance claim.

### Improvements and Fixes

- Remove obsolete product-version history, download instructions, main-board and UART photographs, and flashing screenshots; retain applicable camera dimensions and the RTSP playback example.
- Replace migration comparisons with current V2 interface, data, and runtime-library contracts. Preserve UART logic levels, pending complete pin order and power ratings, power-off wiring, and hot-plug safety boundaries.

## 2.0.8 - 2026-10-22

Document independent SO revisions and the incompatible camera migration. Software remains `2.0.0`, without a new hardware-acceptance claim.

### Improvements and Fixes

- ICM42670 real SO is `2.1.0` (SONAME `2`), SC132 is `3.0.0` (SONAME `3`, `LIBSC132_3.0`, public ABI `3.0`), and PRRTSP is `2.0.1` (SONAME `2`). Align producers, consumers, packaging, and verification. Old camera consumers must be rebuilt; never link `.so.2` to `.so.3`. Each family retains one real file and two relative links.
- Incremental ROS2 installs remove obsolete revisions and majors of the same producer family; the verifier rejects extra libraries, dangling old links, and cross-major compatibility aliases. The staged ICM C link probe consumes both `ICM42670_X5_2.0` and `ICM42670_X5_2.1`, rather than treating producer version definitions as consumer version needs.

## 2.0.7 - 2026-10-22

This revision documents canonical shared-library chains and link-preserving delivery in both languages. Software versions and SO ABI are unchanged; this is not new board-level functional acceptance.

### Improvements and Fixes

- Producer synchronization, non-ROS packages, and ROS2 installs retain one real library with exact relative links instead of flattening `.so`/`.so.2` aliases into duplicate files. Document link-preserving archives/copies, metadata versus byte verification, and the requirement to regenerate non-ROS v3 provenance packages.

## 2.0.6 - 2026-10-22

Synchronize bilingual instructions for the image-provided Wi-Fi command and dedicated boot restore. Software versions and SO ABI are unchanged; no cold-boot acceptance claim for a newly flashed image.

### Improvements and Fixes

- Use the `wifi_setup` system command, dedicated boot entry, and persistent opt-in marker instead of the shared application startup file; document static Ethernet carrier-down routing, image dependencies, credential permissions, and acceptance boundaries.

## 2.0.5 - 2026-10-21

This revision documents YAML configuration for the non-ROS exposure-midpoint test switch. Software versions and SO ABI are unchanged.

### Improvements and Fixes

- Non-ROS `sensor_demo` adds YAML `camera.test_exposure_midpoint`, default off in packaged and auto-generated configurations, with explicit YAML taking precedence over the environment. Document estimated midpoints, ROS1 bag image stamps, and rebuild/restart requirements.

## 2.0.4 - 2026-10-21

This bilingual documentation revision covers the exposure-midpoint test switch. Software versions and SO ABI are unchanged; no calibrated-exposure-midpoint or hardware acceptance claim.

### Improvements and Fixes

- Synchronize bilingual usage, default-off behavior, estimated midpoint formula, failure boundaries, and group/per-camera timestamp semantics for the test switch.

## 2.0.3 - 2026-10-21

This revision completes the bilingual API reference for public image output structures. Documentation only; software versions, SO ABI, and hardware acceptance scope are unchanged.

### Improvements and Fixes

- Complete per-frame, frame-group, and exposure fields, units, sequence/time semantics, NV12 padding, reference lifetime, and ROS2/encoded-output differences; add a direct link from Data Contracts.

## 2.0.2 - 2026-10-20

This revision adds bilingual CAN usage documentation. Software remains `2.0.0`; this does not declare CAN hardware or system acceptance.

### Improvements and Fixes

- Add CAN wiring prerequisites, manual interface setup, transmit/receive commands, options, build, and deployment entries.

## 2.0.1 - 2026-10-20

Documentation-only synchronization with current source; software remains `2.0.0`. The unreleased changes above do not become a software release or system acceptance through this documentation revision.

### Improvements and Fixes

- Align realtime timestamps, opt-in FSYNC, camera ABI 2.2 exposure observations, and IMU ABI 2.1; complete configuration, topic, and saved-sidecar entry points.
- Distinguish ISP exposure estimates, trigger-to-sample association, storage completeness, and actual DDS delivery; document realtime permissions, final health counters, and high-load rejection boundaries.
- Correct MP4/bag frame-rate completeness guarantees, the exposure-accuracy interpretation of `max_skew_ns`, and timestamp checks during backward clock steps.

## 2.0.0 - 2026-10-15

V2.0.0 release: software and documentation versions unified to 2.0.0, with default trigger mode switched to LPWM.

### Improvements and Fixes

- All camera acquisition entries support only `vin_lpwm` (VIN LPWM hardware triggering); software GPIO and free-run paths are removed.
- Camera timestamps preserve frame-propagated `trig_tv` trigger captures in the native SIF counter domain, not RAW/UTC. Sharing the camera/IMU wire does not establish sample/exposure association.
- V2 images are explicitly unreleased. Independent PPS IO defaults on without UART7 RX/TX multiplexing. Camera mapping, FOV, factory networking, and UART levels follow their corresponding usage guides.
- The PTP master PHC uses the PTP/TAI time scale; `phc2sys -w` follows the UTC offset from `ptp4l` instead of using `-O 0`. Hardware `hwts_filter full` lets the master receive Delay_Req timestamps and return Delay_Resp. Passing master/packet checks does not establish slave lock or absolute UTC accuracy.
- Bags use a separate, nondecreasing common recording clock. Images and CameraInfo retain camera capture times; IMU messages retain sample times. Session configuration declares the three domains separately, preventing cross-domain numeric comparisons from corrupting record order. Missing LPWM captures produce at most one terminal callback, serialized by the dispatcher, with callback-side stop requests supported.

## Parallel Development Checkpoints and Unreleased History

These entries retain their original parallel-branch documentation identifiers, ABI versions, and verification boundaries. They are not additional release revisions; use `2.0.59` and current API/data pages for the present contract.

### Manual Exposure Checkpoint (Parallel Documentation Formerly 2.0.18, 2026-10-30)

- Document non-ROS `sensor_demo` manual-exposure YAML: `camera.auto_exposure` defaults to `true`, preserving the SDK tuning's auto policy; `false` uses positive integer `camera.exposure_time_us` (default `2000`, range `1..4294967295`), selecting ISP manual mode for each enabled camera with all three gains fixed to `1x`. The SDK/profile limits the usable range; configuration failure does not fall back to auto.
- Explain startup-only `SC132_AUTO_EXPOSURE=1|0` / decimal `SC132_EXPOSURE_TIME_US`, explicit/default YAML overriding inherited environment values, stop/restart requirements, and requested values versus per-frame exposure estimates. Manual exposure is independent of the existing midpoint test; timestamp formulas, the C ABI, and SONAME are unchanged.
- Synchronize Chinese/English READMEs, usage, and data contracts. Increment the documentation revision once from `2.0.17` to `2.0.18`, without changing software versions or release status. No board deployment or verification has been performed for this feature; no physical exposure-midpoint or synchronization-accuracy claim is made.

### IIO V3 / ABI5 Checkpoint (Parallel Documentation Formerly 2.0.17, 2026-10-30)

- Document same-binary four-way startup selection: top-level non-ROS YAML `camera_timestamp_path: observer|official` and `imu_timestamp_mode: host|tmst`, CLI `--camera-timestamp-path`/`--imu-timestamp-mode`, and the same top-level read-only ROS2 parameters. Defaults remain observer/host; stop/restart to change. All pairs retain the same IIO reads/kernel owner.
- IMU moves to ABI5.0: `libicm42670.so.5.0.0`, SONAME `.5`, nine `ICM42670_X5_5.0` exports. Config adds HOST=0/TMST=1; samples retain raw FIFO low16, separate RAW sample time/uncertainty, and the unchanged MONOTONIC host estimate. Match headers, libraries, and every rebuilt consumer without shims.
- A matched kernel IIO V3 capture module is required for both modes; existing V2 is incompatible and application deployment does not upgrade it. TMST uses kernel-owned FIFO/UI transition evidence and userspace unwrapping/bounded affine RAW mapping; its `200µs` computational admission is not physical accuracy. No FSYNC restoration, userspace SPI/spidev, or fallback.
- Official camera time uses same-frame RAW IRQ `timestamps − (tv − trig_tv) × 1000`, never the SIF observer, with validity0/uncertainty `UINT32_MAX` and unknown physical error. Observer keeps its `500µs` admission. Exposure observations/test mode do not establish physical synchronization.
- Saving/ROS2 bridge the selected native mode to realtime; preserve MONOTONIC host evidence in tmst and keep RAW/MONOTONIC bridge bases separate. Timing schema is `robobaton_imu_timing_v2`; bag session config and MP4 IMU columns record selectors/native timing.
- Synchronize Chinese/English user, API, data, build, compatibility, deployment, time, and troubleshooting guidance. No board testing or deployment occurs in this update; no four-way board/physical-accuracy acceptance is claimed. Only documentation VERSION changes, independently of software versions/release status. ABI4 revision2.0.16 remains below as history, not the current contract.

### IIO V2 / ABI4 Checkpoint (Parallel Documentation Formerly 2.0.16, 2026-10-30)

- Public IMU moves to kernel IIO ABI4.0: `libicm42670.so.4.0.0`, SONAME `.4`, nine `ICM42670_X5_4.0` exports; every consumer migrates together without cross-major shims.
- Library/standalone demos retain MONOTONIC host estimates and independent RAW burst observations; seven native ODRs, watermark1, buffer powers of two in256..8192. Remove userspace SPI, TMST/FSYNC, old read_mode/mapper/precision fields, and association options/topics/sidecars.
- sensor_demo saving/ROS2 explicitly bridge realtime per burst. Bags/ROS2 add `/robobaton/imu/timing`; MP4 extends `imu.csv` with native times/identity/bridge columns. Bracket half-width bounds observations, not physical precision. Camera timing is unchanged.
- STOP retains admission and drains/ACKs the complete cohort; count is a stop threshold, not truncation. Final health retains failed-stop diagnostics; transport_complete does not certify all physical tail data or absence of fatal errors.
- START requires a non-null callback; replacement/removal is rejected through capture and STOP drain until join. Callback-side registration returns `INVALID_STATE` without deadlock. Local transport reconciliation failures retain obtained terminal kernel diagnostics without ACKing undelivered records.
- Callback-side start/health queries also return `INVALID_STATE` during STOP drain, avoiding a lifecycle-lock/join cycle.
- Synchronize current Chinese/English documentation. Only the documentation revision increases; software VERSION is unchanged, without implying release or target-environment acceptance.


### Earlier Unreleased Source Changes (Historical)

The entries below preserve pre-migration history and do not define the current IMU contract. Use the latest revision and current data/API pages.

#### Improvements and Fixes

- The Web homepage adds a top-right `CH` / `EN` language toggle and language-matched online documentation. Static text, dynamic status, and accessibility labels switch without reloading or recreating connections/the Worker or changing recording/attitude state. The browser retains language preferences when local storage is available; online documentation opens in a new tab while the device page remains usable offline.
- Runtime `start_sensor_demo.sh` adds `stop`/`restart`, identifying processes by this package's executable paths and Linux pidfds, and waiting for recording/Web cleanup after a graceful stop. A timeout fails without force-killing or launching a replacement; restart uses package YAML and writes background logs. Lifecycle commands do not change boot-autostart settings or manage `cam-service`. Linux pidfds/Python ≥3.10 are required; surviving the first 2 seconds does not establish hardware or Web readiness.
- Current `sensor_demo` source adds default-on Web/default-off RTSP for four H.264 videos and read-only six-axis LAN preview, sharing one encoder per camera. Web child/IPC/session backpressure is independent of saving; pinned tooling, embedded assets, licenses, and ELF provenance join the runtime. A short real four-video/IMU smoke passed with one board and one Chromium receiver; two-computer/GPU and resource acceptance remain incomplete. This is not a new software release. Existing other entries retain RTSP defaults.
- The Web page adds browser-Worker six-axis quaternion fusion, an animated board, Roll/Pitch/relative Yaw, reset, and stale freezing. It reuses ≤50Hz telemetry without device-side attitude computation or changes to sampling/saving. No absolute heading or navigation accuracy is guaranteed; rebuild the runtime and restart normally to update embedded assets.
- The Web attitude Worker automatically initializes three-axis gyro bias after about 3 seconds of continuous low-motion, gravity-consistent telemetry, checking a minimum sample count, timestamp continuity, accelerometer/gyro variance, and first-versus-last segment mean changes. Detected motion, strong vibration, sparse data, or gaps reset the window; no learning occurs during detected motion. Once bias is known, conservative rate-limited exponential tracking requires a complete approximately 3-second stationary window with mean residual angular-rate vector magnitude ≤0.002 rad/s (about 0.11°/s); accepting an automatic estimate neither jumps attitude nor re-zeros heading. Status text indicates automatic stationary estimation/tracking. Explicit approximately 3-second “静置校准零偏” (Calibrate gyro bias while stationary) remains available; rejection preserves known bias. All integration uses corrected gyro rates, without Yaw freezing, a hard deadband, or display damping. Same-session reset retains bias; a new source/reload clears it for stationary re-estimation. Slow residual rotation below the threshold may be absorbed, so motion detection is not perfect; genuine rotation ≥0.005 rad/s after calibration must remain measurable. No absolute or drift-free heading is guaranteed; this does not establish board deployment or acceptance.
- The Web page brings four-video playback, attitude, raw six-axis values/traces, and an always-visible recording card onto one homepage, removing left-side page navigation and separate hash views without old-view compatibility routes. At widths ≥1440px, four equal-height columns prioritize cameras; telemetry is widened to slightly exceed attitude while reducing camera side margins. At 1100–1439px, the first three columns sit above a full-width recording row. At 768–1099px, cameras/recording each span a row while attitude/telemetry sit side by side; mobile stacks all cards. Only viewports ≥1440px wide and ≥680px high use a compact viewport-filling workspace with panel-internal overflow; other windows use normal document scrolling. Diagnostics expand inline below with actual decoder/fps/loss text.
- The always-visible “录制与保存” (Recording and Saving) card has one form, defaulting to format/fixed storage, start/stop/query, device state, device-timed duration, and bytes written. Native advanced options are initially closed and contain frame skipping/minimum drop interval. A second initially closed section contains space, drop counts, final outcome, session, path, integrity/cleanup, health scope, and use boundaries. Actual errors, uncertain-command messages, and stopping/finalization notices stay outside the folds. Invalid hidden advanced values open the section before validation feedback. Expanding/collapsing does not navigate, reset options/accepted bias, or recreate WebRTC/SSE/the attitude Worker; refresh still resets browser-local options and bias. Closing the page/network does not stop recording. Existing APIs, limits, fresh-state/uncertain-command safeguards, storage paths, native saving, and the unauthenticated trusted isolated LAN boundary are unchanged.
- The Web camera card uses a small single-line “相机” (Cameras) heading aligned with source parameters, removing the eyebrow, per-camera header rows, and expansion buttons. CAM labels/playback states overlay the top-left/bottom-right corners. Double-click an image or focus it and press Enter/Space to expand/restore; `Esc` only exits expansion, not recording. Grid and expansion retain full-image source-aspect `contain`, without cropping or stretching; compact desktops maximize images against remaining width/height and retain source-image bars. Actions do not recreate connections/the Worker or change recording. All four outer cards stay equal-height, without new authentication, hardware controls, or synchronization/accuracy guarantees.
- Web six-axis trends use a fixed 1-second window without a selector. Acceleration and angular rate each overlay X/Y/Z on shared time and vertical axes, with vertical limits automatically following all three axes in the current window; numeric vertical ticks, title units, and relative-second ticks remain. The short relative-heading drift note is removed from the attitude card; the attitude algorithm and accuracy boundaries are unchanged. Traces retain absolute raw values without smoothing or gravity/bias subtraction; receive gaps over 250ms break the trace. Sampling/saving/attitude and connections are unchanged; compact desktop overflow scrolls within the panel.
- Removed the trend explanation row below the six-axis telemetry heading, tightened left-side panel whitespace, and sized the vertical-axis gutter from measured tick-label widths while retaining complete numeric ticks. The 1-second window, shared-axis autoscaling, raw data, and full-image video aspect ratio are unchanged.
- Web recording written size now uses decimal MB and automatically switches to GB at 1 GB, with two decimal places. Conversion preserves the full 64-bit byte count; device statistics, APIs, and recorded data are unchanged.
- Web attitude inputs now pass through four native-rate one-pole low-pass stages before decimation, adding separate `attitude_accel_mps2` / `attitude_gyro_rps` SSE fields. Raw axes, traces, saving, and driver ABI are unchanged. Browser integration and bias means use filtered inputs while raw axes retain stationary-quality checks. Accepted stationary-window bias tracking uses a 6-second time constant with the unchanged 0.002 rad/s residual gate, without Yaw freezing or a deadband.
- Shared Web UDP sends are nonblocking. Independent media workers use bounded pacing; IPC preserves its chunk position across transient backpressure and resumes within the original frame-age deadline. Fixed a race between fresh-frame publication and age sampling. Transient congestion makes only the affected RTP session wait for IDR; deleting one session does not interrupt other peers through a shared write deadline.
- The H.264 producer explicitly disables the SDK's default 8×8 transform that conflicts with its Main declaration, fixing corruption on some Windows hardware decoders. Read/set failures reject startup; H.265, public ABI, and SONAME are unchanged. Update the whole package and restart the application normally. Increasing decode counters do not prove correct pixels; universal GPU compatibility or strict Main PPS syntax conformance is not guaranteed.
- Added standalone `can_demo`: classical CAN by default, explicit `--fd` for up-to-64-byte FD transmission and mixed classical/FD reception, and `--brs` for TX data-phase bit-rate switching, with standard/extended IDs. FD transmission accepts exactly encodable lengths without implicit padding. Integrated into builds, full runtime packaging, and verification. Users/BSP still configure the interface; application support does not replace BSP long-payload integrity acceptance, and local loopback or queued sends do not constitute external-bus acceptance.
- Camera, IMU, CLI, saving, and ROS2 public sensor timestamps now use `CLOCK_REALTIME` system time. Bounded VSYNC cross-sampling and the same-counter trigger delta reconstruct camera hardware trigger edges, without IRQ/arrival-time fallbacks; missing valid mappings stop acquisition.
- RAW remains internal to mapping/grouping. Sensor sample/trigger publication refreshes realtime bridges and follows backward clock steps; IMU host time instead retains the original burst-completion observation without rebridging at deferred publication. Bag record time independently reads realtime without a monotonic clamp; chunk indexes are time-sorted. A common domain does not establish hardware sample/exposure synchronization. Consumers of old time semantics must migrate headers, SOs, and applications together.
- Added opt-in LPWM-to-ICM-42670-P FSYNC trigger-to-sample association: hardware FIFO tags, bounded reconstruction from adjacent absolute TMSTs, unique RAW candidate matching, and missing/ambiguous statuses. Non-ROS `--fsync` and YAML/ROS2 `imu.fsync_enabled` default off and support only `800/1600Hz`; the `200µs` admission policy remains, without guaranteeing every trigger or exposure synchronization. Results reach stdout, bag `/robobaton/fsync`, MP4 `fsync.jsonl`, and the same ROS2 topic.
- Current ICM ABI is `3.0`: every export, including the FSYNC callback, uses only `ICM42670_X5_3.0`, with real file `libicm42670.so.3.0.0` and SONAME `libicm42670.so.3`. Field layouts remain unchanged, but host-time semantics are incompatible. Rebuild all consumers and remove old `.2` artifacts, without old symbol aliases or cross-major shims. Camera frame-set reserved fields carry RAW trigger, group uncertainty, and generation; public time remains realtime.
- Association records retain original per-camera realtime stamps for exact joins with ROS2 Image/CameraInfo; integer JSON requires lossless parsing. MP4 timestamp CSV contains microsecond-quantized group-trigger times expressed in ns; original per-camera values are in opt-in `fsync.jsonl`, not the CSV.
- Fixed acquisition blocking through cross-priority queue locks. IMU consumers/ROS2 publication use explicit realtime scheduling, SPI uses `10MHz`, and INT1 uses a `100µs` asynchronous-reset pulse. Failed starts release resources; final health snapshots retain trailing invalid-FIFO-packet counts. Phase, unique-match, and `200µs` checks remain; high-load results still depend on system IRQ/debug and subscriber scheduling, without guaranteeing every trigger or zero loss under arbitrary load.
- Final IMU health records include timing-drop and FSYNC captured/dropped totals. Non-ROS terminal summaries use post-stop counters, and invalid FIFO packets remain counted when timing rejection overlaps.
- FIFO order, measured TMST, and FSYNC tags/deltas now lead IMU acquisition. INT1 is wake-only: GPIO edge-time conversion, per-packet edge pairing, and the independent INT1 clock observer are removed. Bounded waits still check FIFO without notifications. Detectable missing notification sequence values are diagnostic, not proof of physical-edge/sample loss or independently fatal. FIFO overflow, bad packets, ambiguous clocks, and invalid epochs still fail; the `200µs` admission gate is unchanged.
- FIFO startup bounds measured Arm-to-enable completion by the shortest legal ODR interval. Late enable rejects startup rather than aliasing a whole TMST wrap; neither GPIO nor nominal ODR fabricates time.
- Camera ABI 3.0 includes frozen per-frame ISP exposure observations and frame-info prefix-size reads, with SONAME `libsc132.so.3`. Bag/tee metadata, MP4 `exposure.jsonl`, and ROS2 `/robobaton/camN/exposure` carry estimates separately from unavailable values, without certifying applied-frame identity, an error bound, or actual exposure midpoint; default trigger stamps remain unchanged. The capture observer inherits the allowed CPU mask rather than forcing CPU0.
- Fixed an unreleased MCLK reference acquired during sensor probing: release it before VIN takes ownership without clearing historical references. Camera capture uses FIFO/60 and handles in-scan VSYNC transitions. IMU fitting constrains read intervals, and overwide observations cannot poison unwrapping. The camera `500µs` and IMU `200µs` gates remain unchanged; high load can still cause explicit rejection or acquisition failure.
- IMU interval observations that contradict the retained clock certificate now invalidate it before further publication; overwide observations remain individually rejected. Fixed a bag shutdown race that mistook a final encoded frame arriving after prefetch for an order gap; real gaps still fail. Realtime threads remain subject to system scheduling and IRQ latency; system realtime quotas are unchanged, without a zero-loss guarantee under arbitrary load.
- Camera adds default-off `SC132_TEST_EXPOSURE_MIDPOINT`: test timestamps use trigger time plus half exposure duration, ignoring trigger-to-integration-start delay; unavailable exposure stops acquisition. Group admission, trigger skew, and FSYNC RAW audit remain unchanged; disabling restores original logic. Requires a current-source library rebuild, not a software release or hardware acceptance claim.
- UART RX waits now exit normally on `SIGINT`/`SIGTERM` and restore the original serial settings. Other signals do not extend the RX deadline; genuine I/O errors remain failures.
- With ROS2 rate metrics disabled, final IMU sink publication count is explicitly `unavailable` / `imu_publish_count_valid=no`; enabled metrics retain the actual successful `publish()` count. Producer, sink, and DDS reception counts remain distinct; producer counts do not substitute for an unmeasured sink count.
- ROS2 FastDDS SHM profile now reserves `256 MiB` per participant, leaving capacity headroom for three processes. Each extra daemon/CLI/subscriber process still counts separately; this does not establish that all historical SHM initialization errors are resolved.
- Native bag X5 hardware JPEG omits only the length-4 APP9 immediately after SOI containing a private frameIdx, preserving other APP markers and coded payload to avoid generic-decoder APP structure warnings. The ROS2 JPEG plugin output contract is unchanged.
- `rosbag_info.py --freq` explicitly identifies its bag record-time basis; new `--header-freq` separately reports saved IMU/CompressedImage/CameraInfo `Header.stamp` rates. Batched-write frequency is not sensor sampling rate or proof of losslessness.
- ROS1 bag overload now selects candidates with a strict default minimum drop interval of 10 consecutive frame-set arrival ordinals, not sparse producer IDs; all cameras share each retain/evict decision. If neither an old nor incoming group can legally be dropped, recording explicitly stops, drains to a partial bag, and exits nonzero. Bag metadata and final status expose ordinals, intervals, and the reason; source/IMU losses are outside this guarantee. Intentional alternate saving explicitly requires interval 2.
- Fixed premature IMU admission closure on strict bag image stops and ROS2 callback rejection before producer shutdown completes. Normal finalization keeps IMU input open until acquisition is quiescent, then drains queues. On SIGINT/SIGTERM, ROS2 cleans up the node while its context remains valid and shuts down the context last. A normal `publish()` return is not DDS receipt, nor a zero-loss guarantee under arbitrary load.
- Document automatic boot-time NTP, board-side server settings, and manual recovery, without per-board script installation for normal use. UTC is not retained over power loss without a battery; check system synchronization before recording.
