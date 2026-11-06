# non-ROS Demo Usage

[`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/tree/V2_main) is the public V2 non-ROS source repository. Its combined `sensor_demo` entry provides four-camera SC132 browser preview, ICM-42670-P six-axis data/temperature, attitude preview, and ROS1 bag / H.264 MP4 recording. Standalone camera RTSP, four-channel mosaic RTSP, IMU, UART, and SocketCAN CAN examples are also included.

Accepted parameters do not guarantee sustained throughput or zero loss for every path/load. Evaluate current contracts, terminal health, and actual payloads separately; old compositions do not certify IIO. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

## 1. Directory and Runtime Package

Common entries:

```text
<non-ros-demo-root>/
├── demo/                    # runtime package that can be deployed directly to X5 /root/demo
│   ├── cam_demo
│   ├── sensor_demo
│   ├── mosaic_rtsp_demo
│   ├── imu_reader_demo
│   ├── serial_port_demo
│   ├── can_demo
│   ├── start_sensor_demo.sh     # sensor_demo start, stop, restart, and boot-autostart management
│   ├── env.sh
│   ├── config/sensor_config.yaml
│   ├── bin/
│   └── lib/
├── config/sensor_config.yaml
├── include/
├── lib/
├── scripts/
└── src/
```

Deploy the full contents of `demo/`. The top-level `cam_demo`, `sensor_demo`, `mosaic_rtsp_demo`, `imu_reader_demo`, `serial_port_demo`, and `can_demo` are launcher scripts that set the required `LD_LIBRARY_PATH`; the real ELFs are under `bin/`.

The `bin/sensor_web` service and embedded page are started and reaped by `sensor_demo`, not a standalone Demo. Browser functionality requires the complete matched runtime package containing the helper, not an individual page, ELF, or library replacement.

Current `sensor_web` source uses Rust/str0m and static musl `1.2.5` / mallocng; the device needs neither Rust nor Go. Four-camera video, IMU SSE, recording control, and application lifecycle entry points are unchanged. This corrects the previous allocator's long-lived retention of freed small blocks, but closing the page guarantees neither zero RSS nor a return to its initial value, and does not stop cameras, native IMU, or device recording. Follow [Deployment](../development/deployment-and-upgrade.md) to rebuild, verify, and replace the complete matched runtime package and restart the application normally; a browser refresh is insufficient. See [Source Builds](../development/open-source-build.md) for toolchain and license requirements.

## 2. Run the Combined Entry `sensor_demo`

### Power-On Browser Entry

The release system pre-flashed on the supplied board starts `sensor_demo` automatically at boot. Normal preview and recording require no SSH login or duplicate application launch:

1. Complete power and networking per {ref}`First Power-On <first-boot-web>`, then open `http://192.168.1.12/` in a browser on the same trusted LAN. Use `http://<device-ip>/` if the address has changed.
2. Wait for the device connection and confirm CAM1–CAM4 keep updating and six-axis telemetry is valid before using attitude preview or recording. A connected page does not establish saved-data completeness or hardware synchronization.
3. Use Recording and Saving on the same homepage to record. Stopping recording leaves cameras, IMU, and the page running. Gracefully stop the whole application per {ref}`Stop, Restart, and Boot Autostart <non-ros-autostart>` only when switching applications or changing startup parameters.

```{figure} ../_static/4P_overview_en.png
:alt: RoboBaton 4P non-ROS browser workspace with four cameras, attitude, six-axis telemetry, and recording controls
:width: 100%
:align: center

The non-ROS combined-entry browser workspace (English interface example). Images, values, source parameters, and recording state depend on the current device.
```

Page assets are embedded offline, without Internet, plugins, or camera/microphone permission. Web defaults on and RTSP off. Browser video and optionally enabled RTSP share one hardware encoder per camera; native IMU acquisition is independent of browser preview.

**Mobile interface preview**: connect a phone or tablet to the same LAN with access to the board, then open the device address above directly in its browser, without an app or SSH login. Narrow screens stack panels vertically for scrolling through four cameras, attitude, and six-axis data; tap “Click to play” if autoplay is blocked. Networking, WebRTC/H.264 decoding support, and mobile-device performance affect smoothness; smooth four-stream playback is not guaranteed on every phone. See {ref}`First Power-On <first-boot-web>` for connection steps. Web recording still saves on the board, not on the phone.

**Connecting through the board AP**: after joining the board hotspot, run `ip -4 addr show wlan0` on the board and open `http://<AP-address>/` using its `inet` address, not the phone's assigned address or the board's wired address. The default Web bind is `0.0.0.0`, supporting AP/STA addresses configured after service startup. HTTP validates the actual connection's local IPv4; new WebRTC sessions enumerate current interface addresses. An explicit single-address bind remains restricted to that address. Refresh or reconnect after an address change; existing sessions are not migrated. Allow both TCP `80` and UDP/TCP `8189`, and use only a trusted isolated network.

The top-right language button shows the target language: `EN` on the Chinese page and `CH` on the English page. Chinese is the default, and the browser remembers the choice when local storage is available; switching still works within the current page when storage is blocked. It updates static text, dynamic status, and accessibility labels without reloading, recreating WebRTC/SSE/the attitude Worker, or resetting recording options, device recording, or accepted gyro bias. Reloading still restores options and clears calibration as described below, but retains a storable language preference. “在线文档 / Online Docs” opens the matching [Chinese documentation](https://4p-docs.readthedocs.io/zh-cn/4pv2.main/) or [English documentation](https://4p-doc-en.readthedocs.io/en/4pv2.main/) in a new tab. Online documentation requires Internet access; the device page and language toggle do not. Session IDs, output paths, API status codes, and raw device errors retain their original values.

### Homepage Features and Operation

All functionality is on **one homepage**, without switching between camera, IMU, diagnostics, and recording pages.

| Homepage area | Features and operation |
| --- | --- |
| Live summary | Camera connection count, source capture state, native/preview rates, and sensor temperature; assess connection and capture states separately. |
| Cameras | CAM1–CAM4 in a 2×2 grid, with source resolution, frame rate, and codec beside the heading; double-click an image to expand/restore it. |
| Inertial Attitude | Coordinate-model illustration, Roll/Pitch/relative Yaw, and automatic stationary bias-estimation status; Calibrate Gyro Bias and Reset Relative Heading affect browser preview only. |
| Raw Six-Axis Telemetry | X/Y/Z acceleration (`m/s²`), angular rate (`rad/s`), and last-second trends; native/preview rates, sample sequence, and temperature below. No GPIO/mapper counters absent from ABI5 are displayed. |
| Recording and Saving | ROS bag or MP4, runtime/eMMC or TF; start/stop/query, device-timed duration, and written size. Expand details for the output path and final outcome. |
| Diagnostics | Expand below the workspace for source state, per-camera browser reception/decoding, fps, and packet loss. Browser fields not reported show `unknown`. |

At **≥1440px** wide (CSS pixels), cameras, attitude, six-axis telemetry, and recording form four equal-height columns. At **1100–1439px**, recording sits below the first three columns; at **768–1099px**, cameras/recording each span a row while attitude/telemetry sit side by side; below **768px**, all cards stack. Only viewports both **≥1440px** wide and **≥680px** high use a compact viewport-filling workspace with panel-internal scrolling; other windows use normal page scrolling.

The video grid and expanded camera preserve the complete source aspect ratio without cropping/stretching, retaining source-image bars. Focus an image and press Enter/Space to expand/restore; `Esc` only returns to the grid, without stopping recording. If autoplay is blocked, use Click to Play on the image. CAM1–CAM4 correspond to internal `camera_id` 0–3; APIs, recording filenames, and indices still use internal IDs. Side-by-side images do not establish display synchronization or FSYNC accuracy.

Switching languages, expanding video, or expanding/collapsing advanced options, details, or diagnostics does not recreate WebRTC, SSE, or the attitude Worker, change device recording, or clear accepted bias in the current page. **Refreshing restores browser-local recording defaults and clears attitude bias, but does not stop device recording**; query actual state after reopening. The page does not control camera resolution, frame rate, exposure, or native IMU rate; configure these startup parameters through YAML/CLI and restart the application. Current IIO V3/ABI5 provides no FSYNC configuration or association.

### Web Recording Control

Use the homepage's always-visible Recording and Saving card to record successive sessions without restarting the application:

1. **Choose format and storage**: ROS bag saves JPEG image messages, camera information, and native IMU. MP4 saves four H.264 videos, timestamp indices, native IMU CSV, and sidecars, not a screen capture. Runtime/eMMC and TF both write on the device, not to the browser download directory.
2. **Adjust advanced options if needed**: ordinary recording can retain defaults. Bag supports frame skipping and minimum drop interval; MP4 does not support frame skipping. See constraints below.
3. **Start and observe**: use Start Recording, wait for device confirmation, and monitor actual recording state, device-timed duration, and written size. The form checks fresh state and device capabilities; starting is disabled for missing/stale state, pending or uncertain commands, or when the device disallows a start.
4. **Stop and verify**: use Stop Recording, wait for draining/finalization, and expand Recording Details and Usage to check the output path, final outcome, and completeness. Accepting a stop request does not mean files are complete; do not power off during finalization.

The written-size counter uses decimal MB and automatically switches to GB at 1 GB, with two decimal places (1 MB = 1,000,000 B; 1 GB = 1,000,000,000 B). This only changes display units; device statistics and raw byte counts in the API remain unchanged.

The native `<details>` “高级选项” (Advanced Options) section is initially closed and contains frame skipping and minimum drop interval (defaults 0 and 10 respectively); expand it when adjustments are needed. A second, initially closed “录制详情与使用说明” (Recording Details and Usage) section contains free space, dropped groups/encoded frames, final outcome, session ID, actual format/storage, device output path, integrity/cleanup, health scope, and use boundaries. **Actual errors, uncertain-command messages, and stopping/drain/remux messages always remain outside the folds** and are visible without expanding them. Invalid hidden advanced values open Advanced Options before browser `reportValidity()` displays validation feedback. Collapsing does not reset options. Choices remain local to the current page; **refresh resets them to page defaults, without persistence**.

To stop recording, use “停止录制” (Stop Recording) in the always-visible card, then wait for device drain and remux. Only the device's final `published_complete`, `data_complete=true`, and `cleanup_complete=true` establish complete publication for that session; expand Recording Details and Usage to inspect the final outcome and integrity fields. Cameras, IMU, and preview continue after recording stops, allowing another session.

The browser cannot supply arbitrary paths. Runtime / eMMC uses the fixed absolute root `/root/demo/save_data`, not a path derived from the executable location: bag files use `/root/demo/save_data/session-<id>.bag`, and MP4 sessions use `/root/demo/save_data/session-<id>`. TF storage remains `/mnt/sdcard/recordings` on a mounted card. The device allocates session names. MP4 requires four-camera H.264 encoding and does not support frame skipping. Bag retains strict drop spacing; skip 1 requires interval 2. Only one bag or MP4 session may run at a time.

TF must actually be mounted at `/mnt/sdcard`. A missing/unmounted card explicitly fails, **without falling back to eMMC**. Starting requires at least 64 MiB free, not a guarantee of sufficient space throughout recording; inspect free space in details first. YAML `save_data.save_path` does not override browser fixed paths. Use CLI or YAML startup recording for a custom path.

CLI/YAML `save_data.save_path` and its default `/root/demo/save_mp4/` are unchanged. Existing data stays in its original directory, without automatic moves or deletion. Fixed directories retain the existing symlink security checks; symlinks cannot bypass path constraints.

Closing the browser or losing the network does not stop recording; reopen the page and query actual state. A command timeout does not establish nonexecution: do not blindly retry. Recording/storage failures end that session with failure or partial status; source failures still stop through the failure path. Saving consumes native IMU, not browser-decimated/attitude-filtered data. Dynamic MP4 health is scoped to `callback_window`, not whole-producer final health after shutdown. Startup `--record-bag`, `--record-mp4-dir`, and YAML `save_data` automatic recording remain available. Web can request a stop, but see {ref}`Saving Data <startup-mp4-web-stop>` for the complete-publication limit when stopping startup-auto MP4 early.

**There is no authentication.** LAN users who can reach the device can start disk writes or stop recording; Origin checks are not user authentication. Use only a trusted isolated LAN, never the Internet or an untrusted network. Updates require a matched runtime rebuild and normal application restart, not a standalone webpage or ELF replacement.

### Six-Axis Preview and Runtime Diagnostics

Observe cameras, IMU telemetry, and saving separately. If the page opens without video, check H.264, reachability of TCP `80` and UDP/TCP `8189`, and each camera's playback/connection state. Check device state when connection/telemetry becomes stale. Do not stop `cam-service` or launch duplicate applications to restore the page. For maintenance, inspect package status and logs per {ref}`Stop, Restart, and Boot Autostart <non-ros-autostart>`.

- Axes are device-frame X/Y/Z in `m/s²` and `rad/s`, not attitude angles. Preview is limited to `50Hz` without changing native sampling/saving; deliberate extraction is not source loss. No fresh telemetry for `500ms` marks stale; preview sequence gaps alone cannot establish source loss. Side-by-side playback does not establish display or camera/IMU synchronization; trends are not for spectra/calibration.
- Trends show a fixed **1-second** window without a window selector. Acceleration and angular rate have separate charts; X/Y/Z share the time axis and vertical scale within each chart. Vertical limits automatically follow all three axes in the current window, with labeled numeric ticks and absolute raw values in the title's acceleration `m/s²` / angular-rate `rad/s` units. Horizontal ticks show seconds relative to browser now. There is no averaging or gravity/bias subtraction. Receive gaps over `250ms` break the trace without extrapolation. Only the bounded preview changes, not sampling, saving, attitude, or connections. Compact desktop overflow scrolls inside the telemetry panel.
- The trend explanation row below the telemetry heading is removed. Charts reduce left-side panel whitespace and reserve vertical-axis space from measured tick-label widths, keeping complete labels without cropping video or traces.
- The attitude card fuses dedicated ≤50Hz six-axis inputs into a quaternion in a browser Web Worker, showing Roll/Pitch/relative Yaw and positive device axes. The device only filters before decimation, without computing attitude or bias. SSE adds `attitude_accel_mps2` / `attitude_gyro_rps`; raw six-axis fields, native sampling, telemetry rate, saving, and public ABI are unchanged. Worker failure shows an explicit state while six-axis/video continue. See below for stationary gyro-bias calibration and accuracy limits.
- Hardware decoding depends on the browser, OS, drivers, and concurrent decoder resources. Missing diagnostics show `unknown`; a GPU or capability hint does not replace observed Video Decode evidence. This feature has not shipped as a new software version; host smoke results do not establish target-browser, two-computer steady-state, or GPU acceptance.
- There is no authentication; any reachable user may view video/IMU. Use only a trusted isolated LAN. HTTP assets, signaling, and telemetry lack transport authenticity, and SRTP does not protect HTTP signaling. Internet/untrusted-network use requires a separate HTTPS/authentication/access-control setup.

### Attitude Preview and Stationary Gyro-Bias Calibration

The device processes every native sample before decimation through four cascaded one-pole low-pass stages on all six axes. Each pole is `min(10Hz, telemetry limit×0.2, source rate×0.2)`, with about 64ms low-frequency group delay at the default 800→50Hz. This reduces high-frequency vibration aliasing, not an angular-rate deadband. Integration and bias means use filtered inputs; stationary-quality checks still use raw axes so filtering cannot conceal strong vibration. Raw values and traces are unchanged. Non-increasing time, a sequence reset, or a native-sample gap over 100ms reseeds the filter; invalid input makes attitude fields unavailable, without extrapolating missing samples. See [Data Contracts](../development/data-contracts.md#web-attitude-preview-inputs).

World +Z is up, and attitude initializes from current gravity. Both raw and filtered acceleration must pass the gravity band for tilt correction; otherwise only gyros integrate. On first use, after a new source session, or after a page reload, keep the **actual device completely stationary**. The Worker automatically initializes three-axis gyro bias after about **3 seconds** of continuous low-motion, gravity-consistent telemetry, without requiring a button click. It checks a minimum sample count, continuous timestamps, gravity/angular-rate magnitude, accelerometer/gyro variance, and first-versus-last segment changes in both accelerometer and gyro means. Detected motion, strong vibration, sparse data, or timestamp gaps reset the candidate window; no learning occurs during detected motion.

Once bias is known, automatic updates require a complete approximately 3-second stationary window whose **mean residual angular-rate vector magnitude is ≤0.002 rad/s (about 0.11°/s)**, with the same quality checks. Exponential tracking with a **6-second time constant** follows gradual bias changes; accepting an automatic estimate does not re-zero heading or jump attitude. After temperature changes, stationary dwell allows tracking, or you can manually re-estimate bias.

With known bias, raw mean residual angular rates are also checked over approximately 1-second sections and the final partial section, so filter latency cannot hide a turn beginning near the end. Excessive noise defers tracking updates rather than freezing heading. Invalid six-axis, attitude-input, or time fields discard partial automatic windows and interrupt manual calibration while retaining accepted bias within the same session.

Attitude status text indicates waiting/collection progress for automatic stationary estimation and estimated/tracking states. These states describe the checks, not proof of actual stillness or absolute-heading accuracy. Yaw remains relative only; see the accuracy limits below.

The “静置校准零偏” (Calibrate gyro bias while stationary) button remains available for explicit manual re-estimation:

1. Keep the **actual device completely stationary**, without rotating or translating it. A stationary-looking model in the browser is not enough.
2. Click “静置校准零偏” (Calibrate gyro bias while stationary), then keep the device stationary for about **3 seconds**, until the page reports success or rejection.
3. If motion, instability, or sparse data rejects the attempt, keep the device still, wait for stable telemetry, and retry. Strong vibration can also cause rejection. Failure does not replace any previously accepted bias.

Manual calibration likewise checks gravity/angular-rate magnitude, a minimum sample count, continuous timestamps, accelerometer/gyro variance, and first-versus-last segment mean changes. A rejected manual attempt preserves known bias. **Every quaternion integration step subtracts accepted three-axis bias first; there is no stationary Yaw freeze, hard angular-rate deadband, or display-only damping.** Automatic tracking adjusts bias only after a complete qualifying window, rather than directly zeroing small angular rates.

“Reset relative heading” reinitializes attitude from current gravity without zeroing tilt and retains accepted bias in the same application session. After `500ms` without valid attitude, the model freezes; reconnection, non-increasing timestamps, or gaps over `250ms` realign it. Time discontinuities cancel incomplete candidate windows/manual calibration and reinitialize attitude, but preserve accepted bias within the same source session. A new source session or page reload clears bias, which is automatically re-estimated after another approximately 3-second stationary dwell.

Six-axis data cannot fully distinguish bias from steady slow rotation: automatic tracking may absorb slow residual rotation below the threshold above. Initial estimation and manual calibration likewise require actual stillness; quality checks alone cannot establish it, and neither perfect motion detection nor preservation of arbitrarily slow motion is guaranteed. After calibration, genuine rotation ≥0.005 rad/s (about 0.29°/s) must remain measurable rather than being removed as bias. Without an external heading reference such as a magnetometer, Yaw is unobservable and still drifts. No absolute or drift-free heading is provided. This is not for navigation or a replacement for full sensor calibration. Motion acceleration, vibration, residual bias, and telemetry extraction affect accuracy; this is preview only.

To deploy this update, rebuild `sensor_demo`, the `sensor_web` helper containing the embedded page/Worker, and the full runtime package, replace the package as a matched set, and restart the application normally. A browser refresh alone does not update the running embedded code. These instructions do not establish board deployment or acceptance and do not constitute a new software release.

Deployment here means only an authorized local runtime-package update on the user's device, not a new software-version release or an expansion of the existing acceptance scope.


### Manual Runs and Network Outputs

These are SSH maintenance/parameter-override examples, not prerequisites for power-on browser use. Gracefully stop this package's background instance before a manual launch, keeping `cam-service` running:

```bash
cd /root/demo
./start_sensor_demo.sh stop
./sensor_demo
```

The following are independent startup examples. First exit the previous foreground instance with Ctrl-C, or stop a background instance with the script above:

```bash
./sensor_demo --sample-rate-hz 1600
./sensor_demo --print-rate-hz 50 --print-metrics
./sensor_demo --diagnostics
```

```bash
./sensor_demo --no-web --rtsp    # RTSP only, preserving ports/path
./sensor_demo --web --rtsp       # both outputs, still one encoder per camera
./sensor_demo --no-web --no-rtsp  # no network outputs; saving remains independent
./sensor_demo --web-port 8080    # explicit alternate HTTP port, use IP:8080
```

- Default HTTP uses TCP `80`; WebRTC media uses UDP/TCP `8189`. Allowing HTTP alone does not establish media reachability. Disabled RTSP creates no internal/loopback RTSP service; enabled RTSP retains its ports/path. Defaults for `cam_demo`, mosaic demo, and ROS2 do not change.
- `rtsp.bps/codec` are shared encoding parameters. Web video supports H.264 only: H.265 shows unsupported without transcoding, while HTTP/IMU may continue. MP4, bag, and tee are independent of network switches. With both off and no encoded-save consumer, VENC is not started; camera and IMU acquisition remain active.
- Port conflicts, Web exit, and slow clients degrade only Web without taking over services, using hidden RTSP fallbacks, or relaxing save integrity. Source failures retain the existing failure policy. Network recovery creates a new session and waits for a real keyframe; a frozen picture alone does not establish source failure.
- Transient UDP send-queue congestion is packet loss; only the affected video session waits for the next real IDR. Closing one session does not change the shared UDP socket write deadline or close other sessions. Persistent network loss can still trigger each session's own reconnection.
- Closing a spare passive TCP ICE connection does not terminate another selected media connection; closing the active connection can still trigger reconnection. Each RTC admits at most 64 distinct remote protocol/address endpoints over its lifetime. The limit rejects only new endpoints without evicting admitted endpoints or other sessions. This is not a capacity promise for 64 browser pages or a guarantee of reconnect-free, indefinitely lossless playback.

On exit it prints an IMU summary:

```text
SENSOR_IMU_RESULT samples=... invalid=... timestamp_duplicates=... timestamp_regressions=... set_odr_hz=... timestamp_hz=... acquisition_hz=... acquisition_valid=...
```
Camera realtime and saving/ROS2 bridges follow wall-clock steps; standalone IMU CLI statistics use native MONOTONIC. Do not mix these contracts. Inspect sequences, final IIO health, and actual payloads; assigned-timestamp frequency is not acquisition/integrity proof.

`--imu-sample-drop-policy allow-counted` is the default: invalid six-axis payloads are counted and dropped while acquisition continues; `strict` fails on invalid payloads. Inconsistent identity, scan, timing evidence, or hardware errors stop both policies. Host has no physical-error bound; tmst applies a `200µs` computational mapping-admission limit, not a physical-accuracy guarantee. `--imu-start-order camera-first|imu-first` controls startup order, default `camera-first`, without changing the timestamp contract.

(non-ros-yaml)=
## 3. YAML Configuration

At startup, `sensor_demo` reads `config/sensor_config.yaml` under `DEMO_DIR`, or the current directory when that environment variable is unset. Command-line arguments take precedence over YAML.

Default configuration structure:

```yaml
camera_timestamp_path: observer
imu_timestamp_mode: host
camera:
  # width/height: 1280x1088 (default), 640x480, 720x480, or 1280x720, either axial orientation
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
  auto_exposure: true
  exposure_time_us: 2000
  test_exposure_midpoint: false
rtsp:
  enabled: false
  bps: 4000
  codec: h264
  url: /PRR
web:
  enabled: true
  listen_address: 0.0.0.0
  port: 80
  imu_push_hz: 50
  max_video_sessions: 8
  max_imu_clients: 2
imu:
  sample_rate_hz: 800
  print_rate_hz: 10
  print_metrics: false
save_data:
  save: false
  format: mp4
  save_path: /root/demo/save_mp4/
  skip: false
  drop_min_interval: 10
```

Boundaries:

- Top-level `camera_timestamp_path` accepts `observer` (default) or `official`; top-level `imu_timestamp_mode` accepts `host` (default) or `tmst`. They are not fields under `camera`/`imu`. CLI `--camera-timestamp-path` and `--imu-timestamp-mode` override YAML. Stop and restart to change them; invalid values are rejected before hardware startup.

- `camera.width` / `camera.height` support `1280x1088` (default), `640x480`, `720x480`, `1280x720`, either axial orientation; other values are rejected before the camera starts.
- The full four-camera path is fixed to four channels; single-sensor diagnostics use `cam_demo --camera-id`.
- The non-ROS public frame-rate set is 25/30/40/50/60fps; default `30`, other values rejected before the camera starts.
- `camera.auto_exposure` is a boolean, default `true`: ignore the exposure duration and preserve the SDK tuning's automatic-exposure policy. Set `false` to use `camera.exposure_time_us` (default `2000`): each enabled camera enters ISP `HBN_ISP_MODE_MANUAL`, with analog, sensor digital, and ISP gains fixed to `1x` for repeatable calibration.
- `camera.exposure_time_us` must be an integer in `1..4294967295` microseconds; zero, negatives, fractions, overflow, and trailing text are rejected. Divide by `1000000` for SDK seconds; the SDK/profile limits the usable range, and configuration failure fails startup without silently reverting to auto. Settings are startup-only: stop and restart after changes, and rebuild both the application and a supporting `libsc132.so`.
- `camera.test_exposure_midpoint` defaults to `false`; set `true` and restart `sensor_demo` to use estimated exposure-midpoint image timestamps: trigger time plus half exposure duration. An explicit YAML value overrides `SC132_TEST_EXPOSURE_MIDPOINT`; older files omitting the field preserve the environment setting (off when unset). Rebuild both the application and a supporting `libsc132.so`. IMU stamps and bag record time are unchanged. Use the image `header.stamp` for ROS1 bag alignment; do not add half exposure again. Unavailable exposure stops acquisition; this is not a calibrated actual midpoint. See {ref}`Data Contracts <test-exposure-midpoint>`.
- `rtsp.codec` supports `h264` and `h265`.
- `web.enabled` and `rtsp.enabled` are independent; CLI `--web/--no-web` and `--rtsp/--no-rtsp` take precedence. Limits are 2 video readers per camera, 8 globally, and 2 SSE subscriptions. `imu_push_hz` is `1..50`, without inventing samples at low ODR. Settings apply at application restart; there are no browser hardware controls.
- IMU native sample rates are `25/50/100/200/400/800/1600Hz`, default `800Hz`; other values are rejected, not resampled.
- `save_data.format` defaults to `mp4` and also supports `rosbag`; the save path must be an absolute path.

`save_data.save: false` disables automatic startup recording, not browser recording. With `true`, a session starts using the YAML format and absolute path. Web can request a stop, subject to the {ref}`early-stop limitation for startup-auto MP4 <startup-mp4-web-stop>`. YAML automatic recording and browser fixed-storage selection are separate entry points; browser choices do not write back to YAML.

### Manual Exposure Example

Change these two fields in the existing `camera` section, then restart `sensor_demo`. Set `auto_exposure: true` to restore automatic exposure:

```yaml
camera:
  auto_exposure: false
  exposure_time_us: 2000
```

The library reads `SC132_AUTO_EXPOSURE=1|0` and decimal `SC132_EXPOSURE_TIME_US` at frame-set startup. Explicit or default `sensor_demo` YAML options always override inherited environment values. Manual exposure is independent of `camera.test_exposure_midpoint`: timestamp formulas and the C ABI are unchanged, without certifying applied-frame identity or a physical exposure midpoint. No board deployment or verification has been performed for this feature. See the {ref}`Manual Exposure Contract <manual-exposure>`.

### Four Timestamp Combinations

The same binary and the same kernel IIO reads/owner serve all four combinations; only the timestamp axes change. Run one command at a time and exit normally before selecting another:

```bash
./sensor_demo --camera-timestamp-path observer --imu-timestamp-mode host
./sensor_demo --camera-timestamp-path observer --imu-timestamp-mode tmst
./sensor_demo --camera-timestamp-path official --imu-timestamp-mode host
./sensor_demo --camera-timestamp-path official --imu-timestamp-mode tmst
```

For YAML use, choose one row and set the two top-level keys in `config/sensor_config.yaml`, then run `./sensor_demo` without selector overrides:

| Combination | `camera_timestamp_path` | `imu_timestamp_mode` |
|---|---|---|
| Default | `observer` | `host` |
| Observer + sensor TMST | `observer` | `tmst` |
| Official + host | `official` | `host` |
| Official + sensor TMST | `official` | `tmst` |

Camera consumers set `SC132_TIMESTAMP_PATH` explicitly before startup; direct library use defaults to observer when the variable is unset. Observer retains the `500µs` SIF capture-window admission. Official uses the same frame's RAW IRQ `timestamps − (tv − trig_tv) × 1000`, never starts the SIF observer, and reports timing validity `0` with uncertainty `UINT32_MAX` (unknown physical bound). Host preserves MONOTONIC with unknown physical error. TMST unwraps kernel-owned FIFO/UI transition evidence into bounded affine RAW sample time with a `200µs` computational admission, not physical accuracy. No mode restores FSYNC, spidev, or automatic fallback. See [Data Contracts](../development/data-contracts.md).

**Prerequisite for every pair:** a matching kernel IIO V3 capture module must already be bound. The existing V2 module is incompatible even for host; app deployment does not upgrade it. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for the current non-ROS HO short smoke and unverified scope.

(non-ros-save)=

## 4. Saving Four-Channel Images and IMU

For normal power-on use, prefer [Web Recording Control](#web-recording-control) above. See [Saving Data](save-data-guide.md) for whole-package verification, mutually-exclusive ROS1 bag/MP4 configuration, graceful exit, acceptance, offline conversion, and recovery. The CLI examples below are for custom paths or unattended startup; gracefully stop any existing `sensor_demo` first.

ROS bag saving is suitable for keeping JPEG image frames, camera parameters, and IMU data:

```bash
cd /root/demo
./start_sensor_demo.sh stop
./sensor_demo --record-bag /root/save_demo/record.bag
```

MP4 saving reuses each camera's hardware-encoded H.264 access units, without requiring RTSP network output, and saves four videos plus IMU CSV:

```bash
cd /root/demo
./start_sensor_demo.sh stop
./sensor_demo --record-mp4-dir /root/save_demo/mp4_session
```

MP4 mode requires `rtsp.codec: h264`, the full four-channel camera mask `0x0f`, and must not enable `--record-bag` or `record-frame-skip` at the same time. The configured final output directory must not end with `.partial`; if the target directory or a same-named `.partial` already exists, the program automatically writes to the sibling `<dirname>-YYYYMMDDTHHMMSSZ[-NNNN]`, and the exit summary `SENSOR_MP4_RESULT path=` gives the real directory.

Current MP4 sessions contain `camera0.mp4` through `camera3.mp4`, four `cameraN_timestamps.csv`, extended `imu.csv`, `exposure.jsonl`, `camera_params.yaml`, `session_status.json`, and `publication_receipt.json`, without an FSYNC sidecar. Image CSV uses microsecond-quantized realtime group times; exposure sidecars retain per-camera input observations. IMU CSV `sample_realtime_ns` comes from the output bridge and retains MONOTONIC, RAW, burst/sequence/generation, origin, and bridge bases/half-width. See [Data Contracts](../development/data-contracts.md). `.partial` is recovery only.

To convert to a JPEG dataset offline, use the scripts in the public demo repository on the host:

```bash
python3 scripts/rosbag_extract.py /root/save_demo/record.bag /data/record_dataset
python3 scripts/mp4_extract.py /root/save_demo/mp4_session /data/mp4_dataset
```

## 5. Run Camera RTSP Alone

On an autostart system, gracefully stop the combined entry with `./start_sensor_demo.sh stop` before running the standalone camera Demo; do not stop `cam-service`.

```bash
cd /root/demo
pgrep -a cam-service
./cam_demo
```

Default behavior: four channels, `1280x1088`, `30fps`, H.264, RTSP path `/PRR`.

Common parameters:

```text
--fps <25|30|40|50|60>
--codec <h264|h265>
--rotate <0|90|180|270>
--bps <kbps>
--url <path>
--trigger-mode vin_lpwm
--camera-timestamp-path <observer|official>
--diagnostics
--max-skew-ns <ns>
--frame-timeout-ms <ms>
```

Trigger mode status:

| Mode | Current status |
|---|---|
| `vin_lpwm` | The only supported mode, VIN LPWM hardware triggering; other values are rejected. |

Limits: `--width/--height` accepts `1280x1088` (default), `640x480`, `720x480`, `1280x720`, either axial orientation; other combinations are rejected; scaling is performed by `libsc132` VSE hardware full-frame stretch and does not change the FOV. `--rotate 180` supports only `30fps`, not `25fps`, `40fps`, `50fps`, or `60fps`. The external NV12/RTSP canvas keeps width/height unchanged under rotation `0/180` (e.g. `1280x1088`, `640x480`) and swaps them under `90/270` (e.g. `1088x1280`, `480x640`). Camera, RTSP, ROS1 bag, and H.264 MP4 share the same `25/30/40/50/60fps` public frame-rate set.

Default four-channel RTSP:

```text
CAM1 / cam0 -> rtsp://192.168.1.12:554/PRR
CAM2 / cam1 -> rtsp://192.168.1.12:555/PRR
CAM3 / cam2 -> rtsp://192.168.1.12:556/PRR
CAM4 / cam3 -> rtsp://192.168.1.12:557/PRR
```

CAM1/CAM2/CAM3/CAM4 are the physical silkscreen labels on the board, and cam0/cam1/cam2/cam3 are the software camera IDs.
The above uses the factory default IP; replace the address in the URLs when the board address has been changed.

Single-sensor diagnostics:

```bash
./cam_demo --camera-id 0 --diagnostics
./cam_demo --camera-id 1 --diagnostics
./cam_demo --camera-id 2 --diagnostics
./cam_demo --camera-id 3 --diagnostics
```

Run only one `cam_demo` at a time. This mode is for isolating a single sensor, FPC, power, I2C, and MIPI/VIN link; it does not represent a 2- or 3-channel combination capability.

`cam-service` is a dependency of camera operation; keep it running. Before switching between `sensor_demo`, `cam_demo`, or a custom camera application, exit the old camera application normally to avoid camera/VIO/encoding resource conflicts.

(non-ros-mosaic)=

## 6. Four-Channel Mosaic RTSP (mosaic_rtsp_demo)

`mosaic_rtsp_demo` composites four SC132 `1280x1088` NV12 frame-sets in CPU into one `2560x2176` hbmem NV12 DMA output buffer and outputs fixed H.264 RTSP through `libprrtsp.so`'s external-NV12 input, avoiding a full-frame copy by PRRTSP.

```bash
cd /root/demo
./mosaic_rtsp_demo
./mosaic_rtsp_demo --fps 40
./mosaic_rtsp_demo --fps 50
```

Fixed RTSP address:

```text
rtsp://<x5-ip>:558/PRR
```

This program is a fixed form and does not provide camera-resolution, bitrate, codec, or RTSP port/path configuration:

- Fixed four channels, H.264, 8000kbps, upright orientation, output `2560x2176`, RTSP port `558`, path `/PRR`.
- `--fps` supports `25|30|40|50|60`, default `30`.

On exit it prints run statistics:

```text
queue_full_drop=... invalid_group=... copy_failure=... send_failure=...
retain_release_balance=... copy_duration_avg_ms=... send_duration_avg_ms=...
```

- `retain_release_balance=0` means all cross-thread retained SC132 frames were returned, with no frame leak.
- `queue_full_drop`, `invalid_group`, `copy_failure`, `send_failure` equal to `0` means no queue drops, no invalid frame groups, and no compositing or send failures during the run.
- `copy_duration_avg_ms`, `send_duration_avg_ms` are the per-frame average times for compositing and RTSP sending, used to judge headroom at a given fps.

Like `cam_demo`/`sensor_demo`, `mosaic_rtsp_demo` exclusively holds the four-camera resources; exit other camera applications before running it and keep `cam-service` running.

## 7. Run IMU Alone

First gracefully stop `sensor_demo` or other applications holding the IMU. Stopping browser recording does not release the IMU device.

```bash
cd /root/demo
./imu_reader_demo
./imu_reader_demo --sample-rate-hz 1600 --count 10000
./imu_reader_demo --imu-timestamp-mode tmst --print-metrics
```

It prints sampled records at `10Hz` by default; the program still consumes all IMU samples. To view metrics use:

```bash
./imu_reader_demo --print-metrics
```

After normal stop, `imu_reader_demo` emits one `IMU_RUNTIME_HEALTH final=yes` record with session validity, producer/consumer sample counts, output drops, and final acquisition diagnostics. Samples and the final record use best-effort nonblocking output; a missing summary does not establish healthy completion. `--print-rate-hz 0` disables sample printing, not the final record. See [Data Contracts](../development/data-contracts.md#imu) for field interpretation.

Key fields:

- `sample_monotonic_ns`: kernel-assigned MONOTONIC host estimate, retained without Unix conversion by standalone CLI; `sample_seq` is the sequence. `TIME_BASE domain=monotonic` declares the native clock.
- `timestamp_mode`, `fifo_tmst`, `sample_raw_ns`, `timestamp_uncertainty_ns`: mode and raw FIFO low16; host leaves RAW sample zero and uncertainty `UINT32_MAX`, tmst adds mapped RAW sample and computational uncertainty without replacing MONOTONIC. Standalone output never converts either mode to Unix time.
- `accel_mps2`: acceleration in `m/s^2`.
- `gyro_rps`: angular velocity in `rad/s`.
- `--print-metrics` adds generation, evidence, source, packet/burst flags, MONOTONIC observation, independent RAW burst completion, estimated period, and same-domain MONOTONIC differences. Never directly subtract RAW and MONOTONIC.

V2 `accel_mps2` outputs `[X, Y, Z]`; PCB orientation and signs still need six-face/rotation board verification. Axis signs and transforms relative to the main board or cameras are not currently declared.

The library, standalone demos, and checked-in default YAML all use `800Hz`; explicit CLI values can override YAML. Distinguish supported rates, defaults, and the actual configuration after site-specific changes.

The kernel IIO V3 driver owns IMU SPI/INT1; the older V2 module is incompatible. Discover the unique `icm42670-capture` instance and validate its control node without fixed device numbers. Buffer defaults to4096, API accepts powers of two in256..8192; watermark1 and seven native ODRs. Both modes use this same capture path, without userspace SPI/spidev, FSYNC, or automatic fallback.


Realtime scheduling requires camera `observer` `SCHED_FIFO/60` (not started in `official`), IMU owner `SCHED_FIFO/20`, and consumers `SCHED_RR/3`. Failure rejects startup without automatic IRQ/debug/realtime-quota changes. The observer window remains `500µs`; official has unknown physical error. Neither IMU mode guarantees physical accuracy or zero loss.

## 8. Serial Demo


UART1/UART7 use `3.3V` logic at `/dev/ttyS1` and `/dev/ttyS7`; DEBUG_UART uses `1.8V` and is not for `serial_port_demo`. UART1 uses CN1 GH1.25 4-pin and UART7 CN2 GH1.25 5-pin; UART7 pin 4 is the independent PPS input without RX/TX switching. See the {ref}`Interface Wiring Diagram <wiring-diagram>` for pin numbers and signal order. Power-pin load ratings and hot-plug conditions still await confirmation. Wire with power off by default, leave adapter VCC disconnected, and prevent reverse feed. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart).

```bash
cd /root/demo
./serial_port_demo
```

The default configuration is `/dev/ttyS1`, `115200`, `txrx`. Common examples:

```bash
./serial_port_demo --port /dev/ttyS1 --mode tx --baud 115200 --text "hello-x5"
./serial_port_demo --port /dev/ttyS7 --mode rx --baud 115200
./serial_port_demo --port /dev/ttyS1 --mode txrx --baud 115200 --count 10 --text "ping"
./serial_port_demo --port /dev/ttyS7 --mode echo --baud 115200
```

The UART signal-exit fix covers RX waits only: `SIGINT`/`SIGTERM` exits normally and restores serial settings, other signals do not extend the RX deadline, and genuine I/O errors remain failures. This does not establish every UART mode or hardware reliability.

## 9. Verification Suggestions


- Browser: confirm all four actual images keep updating, six-axis telemetry is valid, and attitude state is available; expand diagnostics for reception/decoding information. `unknown` does not establish software- or hardware-decoding acceptance.
- RTSP: use `ffprobe`/a player to check all four codecs, resolutions, and frame rates only with RTSP explicitly enabled or `cam_demo` running; default browser mode does not require RTSP ports to exist.
- Recording: check device final outcome, completeness/cleanup fields, and actual files. Button acknowledgments or written size do not replace completeness criteria; see [Saving Data](save-data-guide.md).
- IMU: after graceful application shutdown, inspect final health counters, sample sequence, and actual payloads. Realtime regressions across system-clock corrections alone do not establish hardware timing failures.
- Runtime/resources: deploy matched whole packages without mixing same-named `.so` files; gracefully exit the old instance before switching camera/IMU applications, keeping `cam-service` running.

(non-ros-autostart)=

## 10. Stop, Restart, and Boot Autostart

The top-level runtime-package script `start_sensor_demo.sh` manages foreground startup, stop/restart, and boot autostart for `sensor_demo`:

The release system pre-flashed on the supplied board already enables autostart; normal power-on use does not require another `enable`. The commands below are for maintenance as needed. Gracefully stop any background instance before a manual foreground launch.

```bash
cd /root/demo
./start_sensor_demo.sh            # start sensor_demo in foreground (equivalent to ./sensor_demo)
./start_sensor_demo.sh stop       # gracefully stop this package and wait for recording/Web cleanup
./start_sensor_demo.sh restart    # start in the background using package config after a successful stop
./start_sensor_demo.sh enable     # install boot autostart (requires root)
./start_sensor_demo.sh disable    # cancel boot autostart (requires root)
./start_sensor_demo.sh status     # view autostart and running status
```

The matching new system entry `/etc/init.d/S98sensor_demo_autostart` calls this package's `--boot` directly. It reads `enabled`/`disabled` from system-partition `/etc/4p/sensor-demo-autostart`, defaulting to enabled when absent; malformed state, symlinks, or unsafe permissions refuse startup. `enable`/`disable` write the policy atomically, without editing `/userdata/startup.sh` or reading old registration markers. Legacy calls to this script's `--boot` obey the new policy too, without modifying other application commands. Normal reboot retains choices; reflashing system restores image defaults. Install the matching system entry and runtime together, not just the script. Boot uses package `config/sensor_config.yaml`; edits apply at next startup. Wi-Fi has an independent entry.

`stop`/`restart` identify this package's `bin/sensor_demo` and `bin/sensor_web` through `/proc/<pid>/exe`, using Linux pidfds to bind process identity; same-named processes from other directories are outside their scope. `stop` sends `SIGINT` only to the main process, which finalizes recordings, releases resources, and reaps the Web child. Stopping an already stopped program succeeds. The default wait is at most 1800 seconds; set `SENSOR_DEMO_STOP_TIMEOUT_S` to a positive number of seconds to adjust it. A timeout returns nonzero without force-killing; `restart` does not launch a replacement after stop failure. Runtime management requires Linux with pidfd support and Python 3.10 or newer.

`restart` uses the package's `config/sensor_config.yaml`, not the previous command-line arguments. Background output defaults to `/userdata/sensor_demo_autostart.log`; override it with `SENSOR_DEMO_LOG_FILE`. Success means only that the new process did not exit within 2 seconds of startup, not camera/IMU/Web readiness; inspect the log and actual page. `stop`/`restart` do not change autostart registration or stop/restart `cam-service`; do not run them concurrently with manually launched camera applications.

Boot autostart and `restart` override YAML with `--print-rate-hz 0`, disabling high-rate IMU sample blocks, including their metrics, while retaining startup information, errors, recording results, and final health summaries. Native IMU sampling, browser telemetry, and saved data are unchanged. Foreground `./sensor_demo` and argument-free `./start_sensor_demo.sh` still use YAML print settings. For detailed output, first stop the background instance gracefully, then run `./sensor_demo --print-rate-hz 10 --print-metrics` in the foreground. Logs remain append-only: existing logs are not cleared and no size limit is imposed.

(non-ros-can)=

## 11. CAN Demo

`can_demo` uses Linux SocketCAN `CAN_RAW` on network devices registered by the TCAN4550 driver. Classical CAN is the default (`0..8` payload bytes); `--fd` explicitly enables CAN FD transmission (up to `64` bytes) or mixed classical/FD reception. Both formats support 11-bit standard and 29-bit extended IDs. Classical CAN can receive remote frames; FD has no remote frames. Error-frame subscriptions and automatic replies are not supported. The program does not directly access SPI or change device tree, GPIO, bitrate, or interface state, and does not depend on camera/IMU runtime libraries or `cam-service`.

### Prerequisites and Interface Setup

- The BSP must enable CAN, CAN_RAW, and M_CAN/TCAN4550 drivers, with correct SPI, IRQ, clock, power, and pinmux configuration. If `can0` is absent, fix the BSP; the application does not create it.
- With power off, connect CAN_H, CAN_L, and reference ground according to official V2 labels, not UART/TTL wiring. Use appropriate `120Ω` termination at both bus ends after checking existing terminators. Do not guess connector pin order or onboard termination state.
- The peer must use the same bitrate and be able to receive/ACK. `500000` below is an example, not a fixed board default. Use the interface name actually enumerated on your system.

The following commands require root or network-management privileges and interrupt that CAN interface. First ensure no other CAN application or control workload uses it, then execute manually:

```bash
ip -details -statistics link show can0
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 fd off
ip link set dev can0 up
ip -details -statistics link show can0
```

For CAN FD, both nodes must support FD and match arbitration/data bitrates and ISO/non-ISO mode. The `500000` / `2000000` values below are examples only. After ensuring no other workload uses the interface, configure FD manually before running the demo with `--fd`:

```bash
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 dbitrate 2000000 fd on
ip link set dev can0 up
ip -details -statistics link show can0
```

An FD interface must have MTU `72`. `--fd` fails on a classical interface with MTU `16` rather than reconfiguring it. `--brs` selects whether transmitted frames switch bitrate in the data phase; the peer must accept that frame format. The default classical mode also works on an FD interface but does not receive FD frames.

If CAN parameters are unsupported, install CAN-capable iproute2. For probe failures, absent interfaces, or BUS-OFF, check the BSP, wiring, terminators, peer, and bitrate first; do not stop or reconfigure `cam-service`. The program explicitly fails on absent, non-CAN, or non-UP interfaces.

### Receive and Transmit Examples

Receive in terminal A; wait indefinitely by default, and use Ctrl-C for normal shutdown:

```bash
cd /root/demo
./can_demo --interface can0 --mode rx
# Receive 10 frames, with a 5-second idle timeout for each wait.
./can_demo --interface can0 --mode rx --count 10 --timeout-ms 5000
```

Transmit examples (prepare the external receiver first):

```bash
cd /root/demo
./can_demo --interface can0 --mode tx --id 123 --data 0102030405060708 --count 10 --interval-ms 100
./can_demo --interface can0 --mode tx --extended --id 1ABCDE --data AABB
./can_demo --interface can0 --mode tx --id 123 --data ''
```

CAN FD examples (configure the FD interface and prepare the external receiver first):

```bash
# Receive mixed classical data/remote and FD data frames, not FD-only filtering.
./can_demo --interface can0 --mode rx --fd --count 10 --timeout-ms 5000
# 12-byte FD without a data-phase bit-rate switch.
./can_demo --interface can0 --mode tx --fd --id 123 --data 000102030405060708090A0B
# 16-byte extended-ID FD with BRS.
./can_demo --interface can0 --mode tx --fd --brs --extended --id 1ABCDE --data 000102030405060708090A0B0C0D0E0F
```

| Option | Meaning |
|---|---|
| `--interface <name>` | Default `can0`; operates only on an existing, UP CAN device |
| `--mode <rx\|tx>` | Default `rx`; no transmission by default |
| `--id <hex>` | TX ID, default `123`; optional `0x`, standard range `0..7FF`, extended range `0..1FFFFFFF` |
| `--extended` | Explicitly select the TX 29-bit format; numeric ID size does not select it automatically |
| `--fd` | TX uses FD frames; RX accepts mixed classical/FD frames; requires an FD-enabled interface with MTU `72` |
| `--brs` | TX data-phase bit-rate switch; requires both `--mode tx --fd`; not an RX filter |
| `--data <hexbytes>` | TX default `0102030405060708`; classical `0..8` bytes; FD accepts `0..8,12,16,20,24,32,48,64` bytes, rejecting other lengths without implicit padding; even hex-digit count without separators; empty string means zero payload |
| `--count <n>` | RX default `0` (continuous), TX default `1`; explicit `0` runs until Ctrl-C |
| `--interval-ms <n>` | TX inter-frame wait, default `1000`, range `1..3600000` ms; not a realtime-period guarantee |
| `--timeout-ms <n>` | RX idle timeout per wait, default `0` (infinite), range `0..3600000` ms; not a whole-session timeout |
| `--help` / `--version` | Use alone; no CAN hardware access |

TX-only options require `--mode tx`; `--fd` applies to TX or RX, and `--brs` also requires `--fd`. Invalid arguments exit `2`; interface/I/O/receive-timeout failures exit `1`; count completion or normal SIGINT/SIGTERM interruption exits `0`. Classical output is unchanged: `rx 123#0102030405060708`, 8-digit extended IDs, or remote frames such as `rx 123#R8`. FD output is `ID##<flags><data>`, with a single hex digit for flags: bit 0 is BRS and bit 1 is ESI. For example, `rx 123##1000102030405060708090A0B` is a 12-byte FD frame with BRS set. ESI is reported by the transmitting controller; the demo has no ESI-setting option. `--extended` changes only the ID format, not FD mode.

### Verification and Limits

`tx_queued=N` means only that the kernel accepted N frames, not that the peer received them or each transmission completed on the bus. Default SocketCAN local loopback may let another receiver on the same host see transmitted frames; this does not prove external wiring, transceiver, or ACK operation. External acceptance requires a second physical node to verify ID, format, payload, and count, then reverse transmission to verify reception on this board. Also inspect errors, drops, and BUS-OFF with `ip -details -statistics link show can0`. Host datagram logic tests, vcan, and `--help` do not replace this step.

Application FD support is not board-level BSP integrity or sustained-throughput acceptance. Long FD payloads may be corrupted on affected BSPs; complete frame counts, no bus errors, or passing short frames do not establish reliability. Use the matching repaired BSP first, then verify long payloads byte-for-byte, FD/BRS flags, and bidirectional counts at a second physical node. Combined-load, latency, and error recovery are not fully closed; no throughput is promised for the current system composition. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

Use `scripts/build_can_demo.sh` for a standalone build and `scripts/package_runtime.sh` for a full package; see [Building the Public Demo Source](../development/open-source-build.md).
