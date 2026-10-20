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

H.264 MP4 saving is recommended first: the four `cameraN.mp4` files play directly and reuse RTSP encoding. ROS1 bag stores JPEG messages for ROS1 tooling or later extraction. Supported frame rates are a parameter range, not a zero-loss guarantee; see section 9 for load boundaries. Startup and acceptance are in sections 5/7 respectively.

| Mode | Entry | Main output | Complete-save criterion |
|---|---|---|---|
| H.264 MP4 | `--record-mp4-dir` | One session directory | `SENSOR_MP4_RESULT ... outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |
| ROS1 bag | `--record-bag` | One `.bag` file | `SENSOR_BAG_RESULT ... bag_outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |

Only when the process exit code is 0 and the corresponding `SENSOR_*_RESULT` explicitly reports completeness can the data be used as formally complete data. `.partial`, a nonzero exit code, or `data_complete=no` can only be used as recovery or diagnostic data.

Here, complete is first the individual recorder's publication result, not a universal proof that every hardware sample, exposure observation, or FSYNC association is complete. Default `--imu-sample-drop-policy allow-counted` continues after counted timing rejection when identity remains provable. Bag completeness checks the session and recorder queue/write errors; it does not independently require zero producer timing drops. MP4 completeness additionally requires valid final producer health, published=observed=admitted=written>0, continuous sequences, zero GPIO/FIFO/timing/invalid-packet drops, and maximum sample uncertainty at most `200µs`. For a zero-loss dataset, check final health and actual saved payloads in both modes. `strict` fails immediately on timing/invalid-packet rejection, but does not guarantee success under arbitrary load.

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

The `v1.3.0` release uses the same set of AArch64 ELFs, `runtime-provenance.json`, and `manifest.sha256`; in use, follow the actual `VERSION` inside the deployment package, not the version inferred from the document title.

## 3. Pre-Run On-Device Checks

### 3.1 Hardware and Processes

The current stable path requires:

- All four cameras connected;
- ICM-42670-P INT1 acquisition link available;
- `cam-service` running normally;
- No other `cam_demo` or `sensor_demo` occupying the cameras at the same time;
- The default stable trigger mode is `vin_lpwm`.

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
- IMU final GPIO/FIFO/mapper/uncertainty-drop are zero;
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

The following uses the default `30fps` as the complete-save example; to use `25/40/50/60fps`, replace `--fps` and check completeness per the corresponding target-board acceptance matrix:

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
  --record-frame-skip 1
```

`record-frame-skip=1` saves one group and skips one group in units of complete `group_id`, with all four cameras sharing the same decision; it does not change the RTSP output frame rate.

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
- A zero-loss requirement additionally needs zero sequence gaps/duplicates/regressions, invalid packets, GPIO gaps, FIFO overflows, and timing drops. Windows without clock corrections should have no timestamp duplicates/regressions; system corrections may move realtime backward. Do not fabricate increasing stamps or ignore other health errors;
- The final path comes from `SENSOR_BAG_RESULT path=`, not from guessing the configured path.

A nonzero exit, `published_partial`, `.partial.bag`, or quarantine is not formally complete data, but should be kept for diagnostics — do not auto-overwrite or delete it.

## 8. View and Unpack a ROS1 Bag

The runtime package includes `bin/rosbag_info.py` (a Python standard-library implementation; the device ships `/usr/bin/python3`). After saving, view the bag status directly on-device:

```bash
DEMO_DIR=/root/demo  # change to the actual full runtime package directory
cd ${DEMO_DIR}
python3 bin/rosbag_info.py /root/data/robobaton/run_30fps.bag
python3 bin/rosbag_info.py --yaml --freq /root/data/robobaton/run_30fps.bag
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
