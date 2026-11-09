# Saving Data

## 1. Record and Save from Web (Recommended)

For everyday recording, use the Web workflow: **open the device homepage → select format and storage → start → stop and wait for finalization → check results and path → copy the data**. The preflashed system starts `sensor_demo` automatically at boot; there is no need to log in over SSH or start another instance. See [non-ROS Demo Usage](non-ros-demo.md) for Web access and manual startup.

Recording saves the device's four cameras and the same IMU. It is **not a screen recording and does not automatically download to your computer**. Only one ROS1 bag or H.264 MP4 session can run at a time.

### 1.1 Open the Recording Card

1. Connect the device as described in [First Boot](../getting-started/first-boot.md), then open `http://<device-ip>/` in your computer's browser.
2. Find the **Recording and Saving** card on the homepage. On wide screens it is beside the cameras, attitude, and telemetry; on narrow screens, scroll down without switching pages.
3. Wait for fresh device status. Before your first session it should be idle. If recording is already active, identify its purpose before stopping someone else's session.

```{figure} ../_static/images/recording-card.png
:alt: Web Recording and Saving card with format, storage, start/stop/query controls, duration, written size, and a collapsed details section
:width: 325px
:align: center

Recording card detail. Set format and storage first; after stopping, expand Recording details and guidance to check the outcome and device path.
```

Use only a trusted isolated LAN. This page has no authentication: anyone reaching the device can start or stop recording. Do not expose it to the Internet or an untrusted network. Before recording, confirm system time using [System Time Synchronization](../time-sync/system-time-sync.md); a common time axis does not establish physical synchronization.

### 1.2 Select Format and Storage

Choose **Format** according to your intended use:

| Format | Saved content | Intended use |
|---|---|---|
| ROS bag | One ROS1 bag v2.0 file with four JPEG image streams, camera info, frame metadata, and native IMU | ROS1 message tools or later extraction/analysis; recording itself does not require ROS installation |
| MP4 · Four-channel H.264 | One session directory with four `cameraN.mp4` files, timestamp indexes, camera parameters, native IMU CSV, and exposure/status/publication sidecars | Direct video playback with companion sensor data; requires four-channel H.264 encoding |

Prefer MP4 for directly playable video. If unavailable, check the page's capability message; working preview alone does not establish MP4 readiness. MP4 does not support frame skipping.

Choose device-side storage under **Storage location**:

| Option | Fixed save root | Notes |
|---|---|---|
| Runtime directory / eMMC | `/root/demo/save_data` | Fixed absolute path, independent of the executable location; not your computer's download directory |
| TF card | `/mnt/sdcard/recordings` | Confirm the actual mount using [TF Card Usage](../getting-started/tf-card.md); absent/unmounted TF fails without falling back to eMMC |

With Runtime / eMMC selected, the device allocates a bag file at `/root/demo/save_data/session-<id>.bag` or an MP4 session directory at `/root/demo/save_data/session-<id>`. The device generates `<id>`; use the actual output path in the details. Existing data remains in its original directory, without automatic moves or deletion. Fixed directories retain the existing symlink security checks; symlinks cannot bypass path constraints.

At start, the device checks that the target storage has at least `64 MiB` free; this does not guarantee enough space for the whole session. Free space in the details belongs to an assigned session path. Before the first recording it may remain at the initial `0 B`, and changing the storage selector does not immediately query that disk. See {ref}`Recording Details Explained <web-recording-details>`. Web does not accept custom paths, and YAML `save_data.save_path` does not change its fixed paths. CLI/YAML save-path semantics and the default `/root/demo/save_mp4/` are unchanged; use the advanced CLI/YAML startup instructions below for custom paths.

### 1.3 Start and Observe Recording

1. Leave Advanced options at their defaults for ordinary recording. Click **Start Recording** once and wait for device confirmation.
2. Confirm the device reports recording, then observe **Duration (device clock)** and **Written**. Command acceptance, advancing duration, or increasing bytes does not establish final data completeness.
3. Expand the details for actual session, format/storage, output path, and drop counts. Avoid storage stress, large copies/downloads, archive extraction, or data conversion during recording; keep this as the only high-throughput disk-writing task where possible.

Written size uses decimal MB, switches to GB at `1 GB`, and keeps two decimal places (`1 MB = 1,000,000 B`, `1 GB = 1,000,000,000 B`). This is display conversion only; device byte counters are unchanged.

Controls are disabled when status is missing/stale, a command is pending or uncertain, or the device cannot start. Use **Query Status** to inspect actual state. A timeout does not mean the command was not executed; do not blindly resend. Recording/storage faults report failed/partial results; source faults can still stop acquisition.

### 1.4 Stop, Wait for Finalization, and Check Results

1. Click **Stop Recording** once. The device must drain queues, close files, and finalize MP4 when selected. **Do not cut power, remove TF, or delete output files during finalization.**
2. Wait for the stopping/finalization message to finish, then expand **Recording details and guidance**.
3. Check **Final outcome** is `published_complete` and **Completeness / cleanup** shows both **Data complete: Yes · Cleanup complete: Yes** (`data_complete=true`, `cleanup_complete=true` in the API). Then cross-check actual payloads using the format-specific acceptance instructions below.
4. Note the **Session ID** and **Output path (on device)** for this session. The device allocates paths; use the final displayed value rather than guessing a session name. Complete MP4 output is a directory; bag output is one `.bag` file.

An accepted stop request, a stopped timer, playable MP4, or readable bag alone does not prove completeness. `partial`, `failed`, `aborted`, `.partial`, or incomplete cleanup is not complete data. Keep outputs and errors for recovery/diagnosis; incomplete cleanup blocks a new session.

Web-created dynamic sessions provide their final result without exiting the acquisition process and also log `SENSOR_RECORDING_RESULT`. Cameras, IMU, and Web preview continue after recording stops, so another session can be started. **Collapsing details, closing or refreshing the page, and network loss do not stop recording.** Reopen the page and query actual device state. Refresh resets browser-local options and clears preview gyro bias without changing device recording state. `Esc` only exits single-camera expansion; it does not stop recording.

(web-recording-details)=
### 1.5 Recording Details Explained

Click **Recording details and guidance** at the bottom of the recording card to expand it; click again to collapse. This only changes visibility and does not start or stop recording. The following is the real device's idle Web interface with only its session ID redacted. No recording was started for this screenshot; it is not an example of a successful recording.

```{figure} ../_static/images/recording-details.png
:alt: Expanded recording details on the real device, with eight status fields and four guidance notes; session ID redacted
:width: 574px
:align: center

Real idle state with details expanded. Interpret `0 B`, empty format/outcome, the unassigned path, and Data complete: No in context; they do not establish a failed recording or a full disk.
```

#### Status Fields

| Field | Meaning and interpretation | Limits |
|---|---|---|
| Free space | Available bytes reported by the device, in `B`, queried on the filesystem containing the current/last session path | May remain at the initial `0 B` before a path is assigned. This is neither your computer's free space nor a preflight check of the currently selected storage. After selecting TF, do not use the previous eMMC session's value to judge TF capacity |
| Dropped groups | Recorder image-group drop count for a bag session, counting groups rather than individual camera frames | Not browser preview drops or IMU sample loss. `0` does not prove end-to-end losslessness; check final outcomes and payloads |
| Dropped encoded frames | For an MP4 session, this replaces the previous label and counts dropped H.264 encoded frames across all four cameras | Not common four-camera groups or IMU samples; do not compare directly with bag groups. The idle screenshot has no MP4 session yet, so it shows Dropped groups |
| Final outcome | Publication result returned after stop/finalization; `—` when idle without a result, or No final result yet for an unfinished active session | Complete publication requires `published_complete`. `published_partial`, `aborted`, `cleanup_incomplete`, or bag's `published_durability_unproven` is not complete success. Also check completeness/cleanup below and actual payloads |
| Session ID | Device recording-control identifier used to distinguish sessions and correlate status with `SENSOR_RECORDING_RESULT` | The controller already has an ID at initialization; a number alone does not mean recording was created. It is neither a timestamp nor the bag's internal session UUID. Record the actual value; do not copy the screenshot or guess paths |
| Format / storage | Device-reported format and storage for the current/last session; format is `rosbag` or `mp4`, or may be `—` before a session | Not the selectors preparing the next recording; changing selectors does not move existing files. Runtime directory / eMMC in the initial idle state does not mean output has been created |
| Output path (on device) | Device-assigned bag file or MP4 session directory; The device has not assigned a path yet means none is available | Not a computer path or download link. Note the final value after stopping. Abnormal outputs are for recovery/diagnosis; an existing path does not prove completeness. Do not delete during recording or finalization |
| Completeness / cleanup | Data complete is the recorder's completeness result; Cleanup complete describes internal finalization/resource cleanup | Cleanup complete: Yes does not mean files were deleted or data is complete. Initial idle No / Yes means there is no complete recording result yet; do not declare failure from this field during recording either. Both must be Yes at completion; incomplete cleanup blocks new sessions |
| Health scope | `callback_window` describes health checks scoped to a dynamic recording callback window, not a health-pass indicator | Does not establish losslessness outside the window, for the whole producer, or physical synchronization. The current Web/API always displays this value and cannot identify the actual scope of an adopted startup-auto MP4. For that case, check sidecar `imu_health_scope` and final outcomes under {ref}`Startup-Auto MP4 Limits <startup-mp4-web-stop>` |

#### The Four Guidance Notes

1. **Trusted LAN and permissions:** there is no login authentication; anyone reaching the device can control recording. Use a trusted isolated LAN only, without Internet port forwarding or exposure to untrusted networks.
2. **Device-allocated fixed paths:** Runtime / eMMC uses the fixed absolute directory `/root/demo/save_data`, not a path derived from the executable location; TF still uses `/mnt/sdcard/recordings`. Web accepts no custom path and has no download button. Unavailable TF does not fall back to eMMC. Existing data is not automatically moved or deleted, and symlink security constraints are unchanged.
3. **One session and native data:** only one bag or MP4 can record at a time. Native IMU and the corresponding camera data are saved; Web preview decimation, filtering, and attitude gyro-bias calibration affect preview only, not saved data. MP4 saves four H.264 files, not a Web screen capture.
4. **Network loss does not stop recording; stop still needs finalization:** closing the page or losing the network sends no stop command. After a command timeout, use Query Status instead of blindly resending. After stopping, wait for the device's final outcome without cutting power or removing TF. Then copy the data as described next.

### 1.6 Copy Saved Data to Your Computer

Wait until recording has stopped and finalization has completed, then copy data from the device using SSH/SCP file transfer. **The current Web page has no file-download button.** Connect a file-transfer tool to the device, open the final output path you noted, and copy the bag file or the entire MP4 session directory. Do not copy only the four MP4s and omit timestamps, IMU, camera parameters, or other sidecars.

Alternatively, run the following in a **terminal on your computer**. Set `DEVICE_IP` to the device address and `REMOTE_PATH` to the actual final path shown on the page. `session-123` is only an example, not a fixed session name:

```bash
DEVICE_IP='<device-ip>'
mkdir -p ./recordings

# ROS bag: copy one file
REMOTE_PATH='/root/demo/save_data/session-123.bag'
scp "root@${DEVICE_IP}:${REMOTE_PATH}" ./recordings/

# MP4: copy the entire session directory (choose the matching format)
REMOTE_PATH='/root/demo/save_data/session-123'
scp -r "root@${DEVICE_IP}:${REMOTE_PATH}" ./recordings/
```

For TF, use the actual `/mnt/sdcard/recordings/...` path from the details. Clean up only identified historical sessions after copying and checking the data. Never delete staging, markers, or output paths during recording. See section 6 for offline MP4-to-JPEG conversion and section 8 for bag inspection/extraction.

### 1.7 Advanced Options and Completeness Boundaries

Advanced options is initially collapsed; ordinary recording does not require changes. For bag, frame skip defaults to `0` (save every group) and minimum drop interval to `10`. Explicit frame skip `1` (alternate groups) requires interval `2`. MP4 does not support frame skipping. The interval constrains drop policy, not sustained losslessness. Invalid hidden values automatically open the section for validation feedback.

Expanding or collapsing advanced options/details does not stop recording, reset current options or gyro bias, or recreate WebRTC, SSE, or the attitude Worker. Saved data uses native IMU; Web preview decimation, filtering, and attitude calibration do not change saved values.

Sections 2–5 and 7 below are **advanced deployment checks, custom parameters/paths, and CLI/YAML startup recording**, not prerequisites for everyday Web recording. They apply to complete packages whose `sensor_demo --help` includes both `--record-bag <absolute-path>` and `--record-mp4-dir <absolute-directory>`. Do not start a duplicate `sensor_demo` while the boot-started instance is active. Before manual operation, stop this package's instance normally using {ref}`Stop, Restart, and Boot Autostart <non-ros-autostart>`, keeping `cam-service` running.

(startup-mp4-web-stop)=
```{warning} Early Web Stop of Startup-Auto MP4
[INFERENCE] In the current implementation, an MP4 session created by CLI `--record-mp4-dir` or YAML `save_data.save: true` is adopted by Web control. An early Web stop uses neither a valid dynamic callback window nor producer final health, which is supplied at application shutdown. Even successful remux therefore cannot satisfy the complete criterion and publishes partial. This has not been reproduced on the newly flashed device or fixed in this update.

Create dynamic MP4 from Web for independently started/stopped complete sessions. For startup-auto MP4 with a custom path, keep the session active until normal application shutdown, then check final health, outcomes, and payloads. The current fixed Web/API `health_scope=callback_window` label does not identify an adopted session's actual health scope; use the MP4 sidecar's `imu_health_scope` and final outcome. Normal shutdown does not guarantee completeness; other errors still produce failed/partial results.
```

Dynamic MP4 uses `imu_health_scope=callback_window` to check native samples, sequence continuity, counter differences, and queue writes for that window. It waits for the first valid IDR and boundedly waits for a common encoded group at stop. This does not establish losslessness outside the window or for the whole producer. Final producer health after process shutdown applies only to a still-active startup-auto session. Supported frame rates are a parameter range, not a zero-loss guarantee; see section 9 for load boundaries.

Pressure bags may legally end as partial when strict drop policy is exhausted; this is not a sustained-pressure pass. Normal application-exit finalization retains IMU input through producer STOP/drain and consumer drain before closing the writer. Dynamic stop ends its callback window without stopping the producer. The historical DDS publication/reception difference remains unattributed; continuous saved sequences do not prove losslessness at every path's head/tail. Historical FSYNC/long-recording results certify neither the integrated IIO V3/ABI5 composition nor current V4/ABI6. The earlier non-ROS HO saving smoke applies only to its original composition, not long-recording acceptance. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

| Mode | Entry | Main output | Complete-save criterion |
|---|---|---|---|
| H.264 MP4 | `--record-mp4-dir` | One session directory | `SENSOR_MP4_RESULT ... outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |
| ROS1 bag | `--record-bag` | One `.bag` file | `SENSOR_BAG_RESULT ... bag_outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |

For startup command-line recording, also check process exit code 0 and an explicitly complete corresponding `SENSOR_*_RESULT`. Dynamic Web sessions use the session final result described above. Partial, `data_complete=no`, or relevant errors are recovery/diagnostic data only.

Complete is first the recorder publication result, not proof of saving every physical sample or exposure observation. Default `allow-counted` counts only invalid six-axis payloads; strict fails on them. Bag checks session/queue/write errors. Dynamic MP4 uses `imu_health_scope=callback_window` to check window-local samples, sequences, counter differences, and queue writes, without awaiting producer STOP or certifying outside-window completeness. A still-active startup-auto session uses `imu_health_scope=producer_session`; after application exit it additionally requires valid final health, published=observed=admitted=written>0, scan=published, records=ACK, continuous sequences, and zero fatal/overflow/invalid/push/evidence/quiesce errors. Old mapper-health fields are absent; tmst still applies separate `200µs` computational admission, not physical accuracy. `transport_complete` certifies only the STOP cohort, excluding its physical tail. Check each mode against its actual health scope and payloads.

Camera images/metadata use the selected observer/official realtime trigger estimate or opt-in exposure-midpoint estimate. Saving bridges IMU host MONOTONIC→REALTIME or tmst RAW→REALTIME per burst, according to startup `imu_timestamp_mode`; it never overwrites the original MONOTONIC host estimate in tmst mode. Bag `/imu/data` Header and MP4 `imu.csv` `sample_realtime_ns` are output values. Bag `/robobaton/imu/timing` JSON and CSV retain mode, raw FIFO low16 `fifo_tmst`, `sample_raw_ns`, `timestamp_uncertainty_ns`, native host/burst evidence, identity/origin, and correctly labeled separate MONOTONIC/RAW bridge bases/half-width. Host RAW sample is zero and sample uncertainty is `UINT32_MAX`; bridge uncertainty and tmst `200µs` computational admission are not physical precision. Image CSV remains microsecond-quantized group time; exposure sidecars retain per-camera input times. Bag record time reads realtime independently and preserves backward steps; MP4 playback remains relative/nominal. A common epoch is not physical synchronization; synchronize before recording.

Bag timing schema `robobaton_imu_timing_v3` matches ROS2 `/robobaton/imu/timing`; bag `/robobaton/session_config` records `camera_timestamp_path`, `imu_timestamp_mode`, and `imu_fsync_diagnostics`. Choose any of the four startup pairs through [non-ROS YAML/CLI](non-ros-demo.md), then stop/restart to change; all use the same binary and IIO capture/owner. Every pair requires the matched kernel IIO V4 capture module; the existing V2/V3 module is incompatible and app deployment does not upgrade it. Independent FSYNC diagnostics default on; there is no separate topic/sidecar, trigger association, spidev, or fallback. Official never uses SIF observer timing and has validity0/uncertainty `UINT32_MAX`. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for the current non-ROS HO short smoke and unverified scope. See [Data Contracts](../development/data-contracts.md#imu). Control diagnostics with YAML `imu.fsync_diagnostics: true` or CLI `--imu-fsync-diagnostics on|off`. JSON/CSV preserve per-sample `fifo_header,fsync_flags,fsync_sequence,fsync_raw_ns,fsync_uncertainty_ns,fsync_delta_us`. Without a valid edge RAW=0/uncertainty=`UINT32_MAX`; ordinary packets have sequence/delta=0; tagged `fifo_tmst` is delta microseconds. Camera-frame/group diagnostics remain unchanged, without online matching claims.

Bag `/cameraN/frame_metadata`, tee `camN/frames.jsonl`, and MP4 `exposure.jsonl` save frozen per-frame `exposure` unchanged. A getter obtained while acquiring raw hardware frame N estimates adjacent N+1 only, allowing uint32 wrap, matched by acquired raw hardware frame IDs rather than normalized group IDs or SDK source frame IDs. Recorders must not shift another frame. `status=1` is a fixed one-hardware-frame association estimate without a measured physical-error bound or certified applied exposure; no predecessor, hardware gaps, or invalid predecessor getters yield `0`/all zero, never stretching a value across gaps. Query failure at N affects N+1; a valid predecessor can still estimate N. Provenance fields retain the older getter's original values, not target-image identity or time. Each worker's zero-initialized per-session state is primed during warmup without extra image buffering or delivery delay. Default trigger stamps are unchanged; opt-in midpoint uses the matched estimate and stops when unavailable. The MP4 sidecar describes input frames and may outnumber encoded frames; join by camera and microsecond-quantized group delivered time against timestamp CSV. See [Exposure Observations](../development/data-contracts.md#per-frame-exposure-observations) for fields, join keys, and limits.

Fixed N→N+1 is only an estimated-association rule. Real AE can have a different effective lag; there is no per-frame applied-exposure guarantee or AE acceptance claim.

## 2. Advanced: Version and Runtime Package Consistency

Every deployment must copy the complete `demo/` runtime package, not just replace `sensor_demo` or a single `.so`.

Verify the runtime package in the public non-ROS repository on the host:

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # change to the actual repository directory
cd ${NON_ROS_ROOT}
python3 scripts/verify_runtime_package.py demo
```

After entering this deployment's directory on-device, verify:

```bash
DEMO_DIR=/root/demo  # change to the actual full runtime package directory
cd ${DEMO_DIR}
sha256sum -c manifest.sha256
cat VERSION
./sensor_demo --version
```

`VERSION`, program `--version`, and loaded `libsc132`, `libprrtsp`, `libicm42670` product versions and ABI information must belong to the same V2 package. Do not mix same-named dynamic libraries from system directories, old deployments, or other projects.

The runtime package's AArch64 ELFs, `runtime-provenance.json`, and `manifest.sha256` must be consistent. Follow the actual `VERSION` inside the deployment package, not a version inferred from the document title.

## 3. Pre-Run On-Device Checks

### 3.1 Hardware and Processes

The current four-camera saving path requires:

- All four cameras connected;
- ICM-42670-P SPI/FIFO acquisition available; INT1 only wakes acquisition, with bounded FIFO checks even without notifications;
- `cam-service` running normally;
- No other `cam_demo` or `sensor_demo` occupying the cameras at the same time;
- Trigger mode is only `vin_lpwm`.

Check:

```bash
pgrep -a cam-service
pgrep -a -f '(^|/)(cam_demo|sensor_demo)( |$)' || true
```

Do not use a fuzzy `killall` or `pkill -f` to clean up unknown processes. If another camera application is found, first confirm its identity and purpose, then stop it per that application's own exit protocol.

### 3.2 Storage Directory

The save path must be an absolute path. The program tries to create missing parent directories, but the final path and its parent must be writable; for ROS1 bag the parent directory also cannot bypass path constraints through symlinks:

```bash
mkdir -p /root/data/robobaton
findmnt -T /root/data/robobaton
df -h /root/data/robobaton
df -i /root/data/robobaton
```

Before starting, reserve enough capacity for video, temporary staging, final publication, and failure recovery.

For TF storage, follow [TF Card Usage](../getting-started/tf-card.md) to identify the SD device, partition, and exact mount backing first. Do not create the save directory or start recording when unmounted, to avoid writing into tmpfs or the system disk.

**eMMC/TF write-pressure warning:** Four-camera bag/MP4 recording is itself a sustained high-volume write workload. Keep it as the only high-throughput disk-writing task where possible, choosing either bag or MP4. Avoid concurrent recording, storage stress tools, large file copies/downloads, archive extraction, or dataset extraction/conversion, especially writes to the same target medium. Copy, extract, and convert data after recording has stopped normally and finalization has completed.

Reducing concurrent writes lowers bandwidth contention and write-stall risk, but does not guarantee that a single recording cannot build a backlog. Actual JPEG size, bit rate, sustained media throughput, free space, and filesystem state still affect the result. After changing eMMC/TF storage or recording parameters, check final status and actual payloads. Existing whole-group drops, partial output, and explicit-stop semantics remain; this advice is not a zero-loss guarantee.

### 3.3 Environment and External Tools

Prefer the runtime package's top-level launcher; it sets `LD_LIBRARY_PATH` and `PATH`:

```bash
DEMO_DIR=/root/demo  # change to the actual full runtime package directory
cd ${DEMO_DIR}
. ./env.sh
```

ROS1 bag saving does not depend on a ROS installation.

MP4 saving requires an executable `ffmpeg` on the device PATH. The runtime package ships the `bin/ffprobe` helper for recording-link frame-count verification, but it is not a full offline `ffprobe`:

```bash
command -v ffmpeg
command -v ffprobe
ffmpeg -version | sed -n '1p'
```

If any check fails, do not start formal MP4 recording.

The device also needs usable `python3` and matching `libstdc++`. The current matching Buildroot image supplies Python `3.10.12` and C++/SDK runtime libraries; application packages do not replace system dependencies. Available tools or passing manifests do not validate every saving path; see [Current Image Contents](../ops/system-flashing.md).

## 4. Parameters and YAML Precedence

`sensor_demo` first reads:

```text
${DEMO_DIR:-current directory}/config/sensor_config.yaml
```

then parses the CLI; the CLI only overrides explicitly provided fields. The default configuration is `save_data.save: false`, so nothing is saved automatically.

Save configuration structure:

```yaml
save_data:
  save: false
  format: mp4
  save_path: /root/demo/save_mp4/
  skip: false
```

Constraints:

- `format` can only be `rosbag` or `mp4`;
- `save_path` must be an absolute path;
- `rosbag` uses a `.bag` file path;
- `mp4` uses a session directory path;
- `skip: true` applies only to ROS1 bag;
- CLI `--record-bag` and `--record-mp4-dir` are mutually exclusive;
- MP4 only supports H.264, the full four-channel camera mask `0x0f`, and no frame skip;
- The MP4 final directory name cannot end with the reserved suffix `.partial`.

If the CLI is used to manage save tasks long-term, it is recommended to keep in YAML:

```yaml
save_data:
  save: false
```

This avoids accidental data from forgetting that YAML already enabled saving.

## 5. Advanced: CLI/YAML H.264 MP4 Recording

### 5.1 Foreground Start

```bash
DEMO_DIR=/root/demo  # change to the actual full runtime package directory
cd ${DEMO_DIR}
./sensor_demo \
  --fps 30 \
  --codec h264 \
  --sample-rate-hz 800 \
  --print-rate-hz 0 \
  --record-mp4-dir /root/data/robobaton/run_30fps_mp4
```

Do not add `--record-bag` or `--record-frame-skip` at the same time.

If the configured final directory or its corresponding `.partial` already exists, the recorder selects a sibling candidate directory with a UTC timestamp. Follow the final log:

```text
SENSOR_MP4_RESULT path=<actual path> configured_path=<configured path>
```

### 5.2 Start with YAML Configuration

Configure the parameters in the YAML file, then run `sensor_demo` directly.

```yaml
camera:
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 800

  print_rate_hz: 0
  print_metrics: false
save_data:
  save: true
  format: mp4
  save_path: /root/data/robobaton/run_30fps_mp4
  skip: false
```

### 5.3 Normal Stop and Acceptance

Stop the same way as ROS1 bag: prefer one `Ctrl+C`/`SIGINT` and wait for finalize.

A complete MP4 session must satisfy:

```text
process exit code = 0
SENSOR_MP4_RESULT ...
outcome=published_complete
data_complete=yes
cleanup_complete=yes
success=yes
```

Also check:

- The four channels' selected/admitted/written counts are each equal, and the four written counts are equal and nonzero;
- `encoded_frames_dropped=0`;
- `imu_samples_admitted == imu_samples_written > 0`;
- The producer final-health snapshot is valid, and published samples equal consumer-observed samples;
- Final `transport_complete=1`, records=ACK, zero fatal/overflow/invalid/push/evidence/quiesce errors, and continuous sample sequences;
- A matching `publication_receipt.json` exists in the session;
- No `.publication_incomplete` marker exists in the session directory.

Typical complete directory:

```text
run_30fps_mp4/
├── camera0.mp4 ... camera3.mp4
├── camera0_timestamps.csv ... camera3_timestamps.csv
├── imu.csv
├── exposure.jsonl
├── camera_params.yaml
├── session_status.json
└── publication_receipt.json
```

MP4 uses nominal playback timing; `cameraN_timestamps.csv` joins encoded `frame_index` to microsecond-quantized realtime group time, not original per-camera nanosecond stamps. Match input observations in `exposure.jsonl` by camera/group time; do not use source frame_id directly as file index.

`exposure.jsonl` always saves input observations including status=0 and may outnumber saved encoded frames. There is no FSYNC sidecar. Unavailable exposure alone does not stop default-mode images or make output partial; check status and input/encoded joins separately if every frame needs an estimate.

Exit code 2, `published_partial`, a `.partial` directory, a marker, or a receipt mismatch is not a complete session.

## 6. Convert MP4 to Timestamp-Named JPEG

Offline conversion should run on a Host with a full `ffmpeg` and `ffprobe`. The ffprobe helper in the runtime package cannot replace the offline tools.

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # change to the actual repository directory
cd ${NON_ROS_ROOT}
command -v ffmpeg
command -v ffprobe

python3 scripts/mp4_extract.py \
  /root/data/robobaton/run_30fps_mp4 \
  /root/data/robobaton/run_30fps_mp4_dataset
```

Recovery data can also be converted:

```bash
python3 scripts/mp4_extract.py \
  /root/data/robobaton/run_30fps_mp4.partial \
  /root/data/robobaton/run_30fps_mp4_recovery_dataset
```

But `conversion_summary.json` keeps the source outcome, with `source_data_complete=false`; successful conversion does not equal complete source data.

The default requires all four channels `0,1,2,3`. Do not use `--expected-cameras` to select a subset to disguise an incomplete source as complete; a complete source must exactly match the four-channel MP4s and timestamp inventory in status/receipt.

The output directory must not exist. Final publication uses atomic no-replace and does not overwrite concurrently created directories.

## 7. Advanced: CLI/YAML ROS1 Bag Recording

### 7.1 Foreground Start

The following is a default `30fps` startup example, not an advance guarantee of complete saving. For `25/40/50/60fps`, replace `--fps` and check completeness in the actual target environment:

```bash
DEMO_DIR=/root/demo  # change to the actual full runtime package directory
cd ${DEMO_DIR}
./sensor_demo \
  --fps 30 \
  --sample-rate-hz 800 \
  --print-rate-hz 0 \
  --record-bag /root/data/robobaton/run_30fps.bag \
  --record-frame-skip 0
```

If the business explicitly allows saving once every other complete synchronized frame-set:

```bash
./sensor_demo \
  --fps 30 \
  --record-bag /root/data/robobaton/run_30fps_skip.bag \
  --record-frame-skip 1 --record-drop-min-interval 2
```

`record-frame-skip=1` saves one group and skips one group using consecutive complete frame-set arrival ordinals at the recorder, with all four cameras sharing the decision; it does not change RTSP frame rate. Intentional alternate saving must explicitly use `--record-drop-min-interval 2`; the default interval of 10 conflicts with alternate saving and is rejected at startup.

### 7.2 Start with YAML Configuration

Configure the parameters in the YAML file, then start directly.

```yaml
camera:
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 800

  print_rate_hz: 0
  print_metrics: false
save_data:
  save: true
  format: rosbag
  save_path: /root/data/robobaton/run_30fps.bag
  skip: false
  drop_min_interval: 10
```

Then run:

```bash
./sensor_demo
```

### 7.3 Normal Stop

In the foreground press `Ctrl+C` once, or send `SIGINT`/`SIGTERM` to the exact PID from a confirmed control terminal:

```bash
SENSOR_DEMO_PID="$(pgrep -xo sensor_demo)"
test -n "$SENSOR_DEMO_PID"
kill -INT "${SENSOR_DEMO_PID}"
```

After sending the signal you must wait for the program to finish: camera admission close, consumer join, RTSP close, SC132 blocking stop, IMU stop/join, queue drain, writer close, file fsync, and atomic publication. Do not send `SIGKILL` immediately, and do not cut power before seeing the final result.

### 7.4 Result Acceptance

Accepting a complete bag requires simultaneously:

```text
process exit code = 0
SENSOR_BAG_RESULT ...
bag_outcome=published_complete
data_complete=yes
cleanup_complete=yes
success=yes
```

And check:

- `image_frames_by_camera=cam0:N,cam1:N,cam2:N,cam3:N` all equal and `N > 0`;
- Retain final `IMU_RUNTIME_HEALTH` after stop, including failed-stop diagnostics; inspect status and nonzero generation, then compare published, consumer-observed, recorder-admitted/written counts, and actual bag IMU messages;
- Check sequences, invalid payloads, overflow, fatal/push/evidence/quiesce, STOP transport, and records/ACK, then compare producer/consumer/saved payloads. Never directly subtract MONOTONIC and RAW; realtime bridges preserve wall-clock steps without fabricated monotonic values.
- The final path comes from `SENSOR_BAG_RESULT path=`, not from guessing the configured path.

A nonzero exit, `published_partial`, `.partial.bag`, or quarantine is not formally complete data, but should be kept for diagnostics — do not auto-overwrite or delete it.

### 7.5 Queue and Storage Diagnostics

`SENSOR_BAG_RESULT` fields `frame_queue_*`, `encoded_queue_*`, and `imu_queue_*` report capacity, peaks, time at capacity, and rejections. `encoded_queue_oldest_evicted_*` counts complete groups evicted to admit newer groups. The default strict policy is `--record-drop-min-interval 10` (YAML: `save_data.drop_min_interval`): scan fully encoded groups not yet claimed by the writer from oldest to newest and select only candidates at least 10 arrival ordinals from every previous drop. Without an eligible old candidate, dropping the incoming group requires the same spacing. If neither is legal, recording explicitly stops, drains accepted data, publishes `*.partial.bag`, records a reason, and exits nonzero rather than relaxing the interval. The guarantee covers recorder drops only, not acquisition-source, hardware, or IMU losses; it does not guarantee sustained target frame rate under pressure. Evictions or rejections preclude complete-data acceptance.

`source_group_order` in each `/cameraN/frame_metadata` is the zero-based recorder frame-set arrival ordinal used to compare retained groups across cameras and calculate drop spacing. Producer `group_id` remains unchanged; its gaps must not inflate the interval. `/robobaton/session_config` records `drop_policy_min_group_interval`; `/robobaton/session_status` records `drop_policy_stopped`, `drop_policy_stop_group_order`, `drop_policy_dropped_groups`, `drop_policy_min_observed_interval` (0 for fewer than two drops), and `error`. On a policy stop, the terminal ordinal is the exclusive upper bound of recorded coverage, not a legal drop.

At image-burst or IMU high-water service points, the writer drains the current IMU backlog snapshot in bounded batches; later arrivals cannot extend that service indefinitely. The reorder bound includes all committed orders, even frames not yet encoded. A group partially claimed by the writer cannot be evicted.

Drops must apply the same decision to the complete four-camera group and report `data_complete=false`. Legal spacing proves policy compliance only; an early stop, partial bag, or readable playback is not sustained-pressure or all-sensor acceptance.

`chunk_*` and `record_*` latencies include the writer/buffered-write path, not just storage-media latency. `dirty_kb`/`writeback_kb` come from system `/proc/meminfo`. `diskstats_*_delta` sums every `/proc/diskstats` row, potentially counting both disks and their partitions; it is not I/O attributable to this recording or one mount device. Do not derive disk busy percentage from aggregate `io_time`. Diagnose using the actual mounted device, final health, and payload readback.


## 8. View and Unpack a ROS1 Bag

The runtime package includes `bin/rosbag_info.py`, a Python standard-library implementation requiring usable `/usr/bin/python3` on-device. The current matching image provides Python `3.10.12`. After saving, view the bag status directly on-device:

```bash
DEMO_DIR=/root/demo  # change to the actual full runtime package directory
cd ${DEMO_DIR}
python3 bin/rosbag_info.py /root/data/robobaton/run_30fps.bag
python3 bin/rosbag_info.py --yaml --freq /root/data/robobaton/run_30fps.bag
```

With `--freq`, `frequency` is the inverse median interval of bag-index **record times**, explicitly identified by `frequency_basis`. Batched writes can make it much higher than the sensor sampling rate; this does not mean the IMU ran too fast or the payload is damaged. Current source adds `--header-freq` (implies `--freq`): scan payloads of `sensor_msgs/Imu`, `CompressedImage`, and `CameraInfo`, reporting `Header.stamp` frequency separately as `header_frequency`. All connections of a topic must share the same type and MD5. Other types, mixed schemas, fewer than two messages, or a nonpositive median period have no such value. Intervals are computed after sorting timestamps; this cannot check publication order or prove losslessness or hardware synchronization. Scanning reads the complete bag and retains the original record-time statistics.

```bash
python3 bin/rosbag_info.py --yaml --header-freq /root/data/robobaton/run_30fps.bag
```

Using the host repository script on the Host:

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # change to the actual repository directory
cd ${NON_ROS_ROOT}
python3 scripts/rosbag_info.py /root/data/robobaton/run_30fps.bag
```

Unpack into IMU CSV, camera parameters, and four-channel JPEG (run on the Host using the public source-repo script):

```bash
python3 scripts/rosbag_extract.py \
  /root/data/robobaton/run_30fps.bag \
  /root/data/robobaton/run_30fps_dataset
```

The output directory must not exist. The current tool supports uncompressed, fully-indexed ROS1 bag v2.0; `.partial.bag` can be used for recovery analysis but cannot be upgraded to complete data.

(persistence-fps-boundary)=

## 9. Frame Rate and Stress Boundaries

Both modes accept `25/30/40/50/60fps`, but frame rate alone cannot guarantee complete saving:

- H.264 MP4 reuses RTSP-encoded access units. Completeness depends on encoding, storage, and final IMU health; high load or source errors can produce `published_partial` even when all four MP4s play.
- ROS1 bag uses separate JPEG encoding and queues. CPU, encoder throughput, storage, and RTSP preview load affect losses; no frame-rate threshold guarantees complete saving or only a small loss at higher rates.
- After changing fps, IMU ODR, dimensions, media, or scheduling, separately check sustained four-channel rates, final health, IMU timing/bridge metadata, and actual payloads. Exposure coverage and container completeness are separate.

Accepted settings or older compositions do not certify decoding, DDS, or sustained saving of current IIO operation. Native bag JPEG removes private JPU APP9 without changing the ROS2 JPEG plugin; one encoding/saving path does not certify another.

## 10. Common Issues

### Bag and MP4 Configured Simultaneously

The program rejects this before starting hardware:

```text
--record-bag and --record-mp4-dir are mutually exclusive
```

Retry after choosing one mode.

### ffmpeg/ffprobe Error at MP4 Start

Confirm you started from the complete runtime package's top-level launcher, or run `. ./env.sh` first. The device must have a full `ffmpeg`; the package only provides the ffprobe helper required for recording.

### Output Becomes `.partial` or Exit Code 2

This means the recorder could keep recovery data but the completeness gate failed. Keep the logs, session status, receipt/marker, and data; do not rename them to disguise them as complete.

### RTSP Handle Fails to Close Three Times

The program terminates immediately with exit 1, to avoid destructing the callback owner while the SC132 callback is not yet quiescent. That run's data is recovery-only; keep the logs and check `cam-service` and the camera application state, then confirm the service has recovered before starting the next task.

### Insufficient Storage Space or Inodes

Stop new save tasks, keep the current partial/quarantine, and expand or clean up confirmed historical data. Do not delete staging, markers, or target paths while the recorder is running.

### No Final Result Line After Exit

Treat that run as failed or not proven complete. Keep the full stdout/stderr, exit code, and process/service state.
