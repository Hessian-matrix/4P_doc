# Saving Data

## 1. Scope

This document explains how to use the non-ROS `sensor_demo` to save the following two kinds of data:

1. ROS1 bag v2.0: four-channel synchronized images, camera info, frame metadata, and independent IMU;
2. H.264 MP4 session: four MP4s, encoded-frame timestamp indexes, camera parameters, independent IMU, exposure and FSYNC sidecars, session status, and publication receipt.

This document applies to runtime packages whose `sensor_demo --help` includes both of the following parameters:

```text
--record-bag <absolute-path>
--record-mp4-dir <absolute-directory>
```

ROS1 bag and MP4 are two mutually exclusive save modes and currently cannot be enabled simultaneously in the same process.

### Dynamic Web Sessions

With a complete runtime supporting Web recording, open `http://<device-ip>/` and use the always-present “录制与保存” (Recording and Saving) card on the homepage. Its single form shows format, fixed storage, start/stop/query, device state, duration, and bytes written by default. Frame skipping and minimum drop interval are in the initially closed Advanced Options section; free space, drop counts, session, path, final integrity, and other details are in the initially closed Recording Details and Usage section. Actual errors, uncertain commands, and stopping/finalization messages remain outside the folds. Existing fresh-state/capability checks and command locks remain; controls do not act on missing/stale status or an uncertain command outcome. Cameras, IMU, and preview keep running after recording stops; mutually exclusive sessions can be repeated. CLI/YAML startup recording remains and can be stopped from Web. See [Web Recording Control](non-ros-demo.md#web-recording-control) for operation and access boundaries.

Expanding or collapsing advanced options or recording details does not send stop, reset options or bias, or recreate WebRTC, SSE, or the attitude Worker. Invalid hidden advanced values automatically open the section before browser validation feedback. `Esc` only exits single-camera expansion and is not a recording control. Refresh still resets browser-local options to defaults and clears preview bias without changing device recording state.

Web allows only fixed runtime storage (standard package `/root/demo/bin/recordings`) or `/mnt/sdcard/recordings` on mounted TF. The device allocates session names, with no custom paths or eMMC fallback for absent TF. Start requires at least 64 MiB free, not a guarantee of sufficient space throughout recording. Recording/storage failures report failed/partial and clean up that session rather than masquerading as success; source failures still stop acquisition.

Stop only requests finalization. Wait for device `published_complete`, `data_complete=true`, and `cleanup_complete=true`, then cross-check actual payloads. Web results and `SENSOR_RECORDING_RESULT` are session results and do not require acquisition-process exit. `partial`, `failed`, `aborted`, or incomplete cleanup is not complete data. Collapsing details, closing the browser, and network loss do not stop recording. Query actual state after a timeout; do not blindly retry. Incomplete cleanup blocks a new session.

Dynamic MP4 uses `imu_health_scope=callback_window` to check native samples, sequence continuity, counter differences, and queue writes for that window. It waits for the first valid IDR and boundedly waits for a common encoded group at stop. This does not establish losslessness outside the window or for the whole producer. Final producer health after process shutdown applies only to a still-active startup-auto session. Preview filtering, attitude bias, and telemetry decimation do not alter saved values. There is no authentication: anyone reaching the device can start/stop disk writes. Use only a trusted isolated LAN.

H.264 MP4 saving is recommended first: the four `cameraN.mp4` files play directly and reuse RTSP encoding. ROS1 bag stores JPEG messages for ROS1 tooling or later extraction. Supported frame rates are a parameter range, not a zero-loss guarantee; see section 9 for load boundaries. Startup and acceptance are in sections 5/7 respectively.

Pressure bags may legally end their session at strict drop-policy exhaustion; that is not a sustained-pressure pass. The current composition's `8h` MP4 + FSYNC recording has not started. Normal application-exit finalization retains IMU input until producer shutdown and consumer drain, then closes the writer. Dynamic stop instead ends its callback window without stopping the producer. The historical DDS publication/reception difference still cannot be exactly attributed. Continuous saved sequences do not prove every path retains all head/tail data; see {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

| Mode | Entry | Main output | Complete-save criterion |
|---|---|---|---|
| H.264 MP4 | `--record-mp4-dir` | One session directory | `SENSOR_MP4_RESULT ... outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |
| ROS1 bag | `--record-bag` | One `.bag` file | `SENSOR_BAG_RESULT ... bag_outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |

For startup command-line recording, also check process exit code 0 and an explicitly complete corresponding `SENSOR_*_RESULT`. Dynamic Web sessions use the session final result described above. Partial, `data_complete=no`, or relevant errors are recovery/diagnostic data only.

Here, complete is first the individual recorder's publication result, not universal proof that every hardware sample, exposure observation, or FSYNC association is complete. Default `--imu-sample-drop-policy allow-counted` continues after counted timing rejection when identity remains provable. Bag completeness checks the session and recorder queue/write errors; it does not independently require zero producer timing drops. MP4 additionally requires valid final producer health, published=observed=admitted=written>0, continuous sequences, zero FIFO/timing/invalid-packet drops, and maximum sample uncertainty at most `200µs`. `gpio_event_gap_count` diagnoses missing wake-notification sequence values, not physical-edge/sample loss, and does not independently fail bag/MP4 completeness. For a zero-loss dataset, check final health and actual saved payloads in both modes. `strict` fails on timing/invalid-packet rejection but does not guarantee success under arbitrary load. Repeated host observations and wall-clock rollback are valid; sample sequence defines order.

Images, frame metadata, and IMU CSV/bag payloads preserve producer `CLOCK_REALTIME` capture/sample times (Unix epoch ns). MP4 timestamp CSV stores group-trigger times on the same timeline, quantized by the encoder to microseconds and expressed in ns, not original per-camera nanosecond stamps; with FSYNC enabled, original values are in `fsync.jsonl`. Bag record time independently reads system time at writing, not sampling; backward steps are preserved and bag indexes are time-sorted. MP4 container playback remains relative/nominal. Synchronize the system clock before acquisition. A common domain does not prove camera/IMU sample or exposure alignment; see [Data Contracts](../development/data-contracts.md).

Add `--fsync --sample-rate-hz 1600` for trigger-to-sample association (default off, `800/1600Hz` supported). Bags add `/robobaton/fsync` as `std_msgs/String` JSON; MP4 sessions add `fsync.jsonl`. Cross-check `sample_sequence`, `group_id`, and `frame_ids` against saved data. Only `status=1` is valid. Container completeness does not prove association completeness: inspect missing/ambiguous records, sequence gaps, and final captured/dropped counts. See [Data Contracts](../development/data-contracts.md) for fields and uncertainty boundaries.

Bag `/cameraN/frame_metadata`, tee `camN/frames.jsonl`, and MP4 `exposure.jsonl` save frozen per-frame `exposure`. `status=1` is a latest-ISP observation estimate, not certified applied exposure; `0` is unavailable, without carrying earlier values forward. The MP4 sidecar describes input frames and may outnumber encoded frames; join by camera and microsecond-quantized group-trigger time against timestamp CSV. See [Exposure Observations](../development/data-contracts.md#per-frame-exposure-observations) for fields, join keys, and limits.

## 2. Version and Runtime Package Consistency

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

The device also needs usable `python3` and matching `libstdc++`. Clean-system-image versus runtime-package ownership of these dependencies is not fully resolved. Available tools or passing manifests do not establish runtime-dependency acceptance for every image.

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

## 5. Save an H.264 MP4 Session (Recommended)

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

### 5.2 YAML Start (More Recommended)

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
- IMU final FIFO/mapper/uncertainty-drop/invalid-packet counters are zero and sample sequences are continuous; GPIO notification gaps remain diagnostic, not a completeness veto;
- A matching `publication_receipt.json` exists in the session;
- No `.publication_incomplete` marker exists in the session directory.

Typical complete directory:

```text
run_30fps_mp4/
├── camera0.mp4 ... camera3.mp4
├── camera0_timestamps.csv ... camera3_timestamps.csv
├── imu.csv
├── exposure.jsonl
├── fsync.jsonl
├── camera_params.yaml
├── session_status.json
└── publication_receipt.json
```

The MP4 playback timeline uses the nominal frame rate; `cameraN_timestamps.csv` aligns encoded frames by `frame_index`, providing realtime group-trigger times quantized to microseconds and expressed in ns, not original per-camera nanosecond stamps. With FSYNC enabled, cross-check CSV using group time in `fsync.jsonl` and read original per-camera values from `camera_timestamps_ns`; see [Data Contracts](../development/data-contracts.md).

`exposure.jsonl` always stores input-frame observations, including `status=0`. `fsync.jsonl` is always created, with association records written only when FSYNC is enabled. An unavailable exposure estimate alone neither stops images nor changes complete to partial. If every saved frame must have an estimate, separately check `exposure.status` and input-to-encoded-frame joins rather than infer it from container completeness.

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

## 7. Save a ROS1 Bag

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

### 7.2 YAML Start (More Recommended)

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
- Successful stop yields `IMU_RUNTIME_HEALTH final=yes health_valid=yes` with nonzero generation; compare published, consumer-observed, recorder-admitted/written counts, and actual bag IMU messages;
- A zero-loss requirement additionally needs zero sequence gaps/duplicates/regressions, invalid packets, FIFO overflows, and timing drops, plus actual sample readback. GPIO notification gaps are not sample-loss counts. Windows without corrections should have no sample timestamp duplicates/regressions; host timestamps may repeat within a burst, and corrections may move both realtime stamps backward. Do not fabricate increasing stamps or ignore other health errors;
- The final path comes from `SENSOR_BAG_RESULT path=`, not from guessing the configured path.

A nonzero exit, `published_partial`, `.partial.bag`, or quarantine is not formally complete data, but should be kept for diagnostics — do not auto-overwrite or delete it.

### 7.5 Queue and Storage Diagnostics

`SENSOR_BAG_RESULT` fields `frame_queue_*`, `encoded_queue_*`, and `imu_queue_*` report capacity, peaks, time at capacity, and rejections. `encoded_queue_oldest_evicted_*` counts complete groups evicted to admit newer groups. The default strict policy is `--record-drop-min-interval 10` (YAML: `save_data.drop_min_interval`): scan fully encoded groups not yet claimed by the writer from oldest to newest and select only candidates at least 10 arrival ordinals from every previous drop. Without an eligible old candidate, dropping the incoming group requires the same spacing. If neither is legal, recording explicitly stops, drains accepted data, publishes `*.partial.bag`, records a reason, and exits nonzero rather than relaxing the interval. The guarantee covers recorder drops only, not acquisition-source, hardware, or IMU losses; it does not guarantee sustained target frame rate under pressure. Evictions or rejections preclude complete-data acceptance.

`source_group_order` in each `/cameraN/frame_metadata` is the zero-based recorder frame-set arrival ordinal used to compare retained groups across cameras and calculate drop spacing. Producer `group_id` remains unchanged; its gaps must not inflate the interval. `/robobaton/session_config` records `drop_policy_min_group_interval`; `/robobaton/session_status` records `drop_policy_stopped`, `drop_policy_stop_group_order`, `drop_policy_dropped_groups`, `drop_policy_min_observed_interval` (0 for fewer than two drops), and `error`. On a policy stop, the terminal ordinal is the exclusive upper bound of recorded coverage, not a legal drop.

At image-burst or IMU high-water service points, the writer drains the current IMU backlog snapshot in bounded batches; later arrivals cannot extend that service indefinitely. The reorder bound includes all committed orders, even frames not yet encoded. A group partially claimed by the writer cannot be evicted.

Drops must apply the same decision to the complete four-camera group and report `data_complete=false`. Legal spacing proves policy compliance only; an early stop, partial bag, or readable playback is not sustained-pressure or all-sensor acceptance.

`chunk_*` and `record_*` latencies include the writer/buffered-write path, not just storage-media latency. `dirty_kb`/`writeback_kb` come from system `/proc/meminfo`. `diskstats_*_delta` sums every `/proc/diskstats` row, potentially counting both disks and their partitions; it is not I/O attributable to this recording or one mount device. Do not derive disk busy percentage from aggregate `io_time`. Diagnose using the actual mounted device, final health, and payload readback.


## 8. View and Unpack a ROS1 Bag

The runtime package includes `bin/rosbag_info.py` (a Python standard-library implementation requiring usable `/usr/bin/python3` on-device; clean-image dependency ownership remains unresolved). After saving, view the bag status directly on-device:

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

- H.264 MP4 reuses RTSP-encoded access units. Completeness depends on encoding, storage, and final IMU health; high load or timing drops can produce `published_partial` even when all four MP4s play.
- ROS1 bag uses separate JPEG encoding and queues. CPU, encoder throughput, storage, and RTSP preview load affect losses; no frame-rate threshold guarantees complete saving or only a small loss at higher rates.
- After changing fps, IMU ODR, FSYNC, dimensions, storage, or system scheduling, check sustained four-channel rates, final health, and actual payloads on the target. Exposure `status=1` coverage, unique FSYNC matching, and storage completeness are separate checks.

Short non-ROS `60fps` + `1600Hz` FSYNC CPU/BPU console association does not establish saved-image decoding. Native bag JPEG removes only private JPU APP9, without changing the ROS2 JPEG plugin or closing high-rate H.264 RTSP missing-reference/slice warnings. One encoding/saving path's result does not certify another path.

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
