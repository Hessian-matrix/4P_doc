# ROS2 Demo Usage

This page describes ROS2 usage for current V2 source. Before use, topics, compressed images, native IMU rates, and required camera rates still need target-board checks; build or install verification does not replace actual runtime checks.

Accepted parameters do not establish every mode/load/duration or complete DDS delivery; old compositions cannot certify the current IIO composition. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

```{important}
ROS2 and non-ROS RTSP are two independent usage paths. The ROS2 demo does not provide RTSP; do not mix directories, headers, or `.so` between the non-ROS `/root/demo` runtime package and the ROS2 `/root/ros2_demo` install package.
```

## Feature Boundary

The ROS2 package is `robobaton_4p_ros2_demo`; software versions follow packaged `VERSION`/`package.xml` and `--version`, not an automatic increase for V2 hardware or documentation revisions. Main artifacts:

- Node: `robobaton_sensors_node`
- IMU frequency check tool: `robobaton_imu_rate_monitor`
- Launch: `launch/robobaton_sensors.launch.py`
- Default configuration: `config/robobaton_sensors.yaml`
- Install environment script: `robobaton_ros2_env.bash` in the install root, for uniformly loading the ROS2 underlay, this package's overlay, the FastDDS SHM profile, and the log-buffering setting.

Exposed capabilities:

- Four raw images: `sensor_msgs/msg/Image`, encoding `nv12`.
- Four compressed images: `sensor_msgs/msg/CompressedImage`, JPEG payload; only when there is a compressed subscriber are valid NV12 rows copied into the X5 media-codec internal input buffer, and hardware single-frame compression executed with `MEDIA_CODEC_ID_JPEG`.
- Four `sensor_msgs/msg/CameraInfo`.
- IMU: `sensor_msgs/msg/Imu`.
- Temperature: `sensor_msgs/msg/Temperature`.
- Per-frame ISP exposure observations and per-sample native-clock/output-bridge IMU timing JSON.

RTSP, physical sampling/exposure-sync guarantees, TF extrinsics, and camera calibration are unavailable. CameraInfo has current width/height only; IMU orientation is unavailable and no FSYNC association exists.

CAM1..CAM4 map respectively to software cam0..cam3 and `/robobaton/cam0..3`. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#camera-interface).

## Topics

| Topic | Message type | Encoding / purpose | QoS |
|---|---|---|---|
| `/robobaton/cam0/image_raw` | `sensor_msgs/msg/Image` | cam0 raw NV12 | Reliable, keep last 8 |
| `/robobaton/cam1/image_raw` | `sensor_msgs/msg/Image` | cam1 raw NV12 | Reliable, keep last 8 |
| `/robobaton/cam2/image_raw` | `sensor_msgs/msg/Image` | cam2 raw NV12 | Reliable, keep last 8 |
| `/robobaton/cam3/image_raw` | `sensor_msgs/msg/Image` | cam3 raw NV12 | Reliable, keep last 8 |
| `/robobaton/cam0/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam0 JPEG compressed transport | Follows raw QoS, Reliable, keep last 8 |
| `/robobaton/cam1/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam1 JPEG compressed transport | Follows raw QoS, Reliable, keep last 8 |
| `/robobaton/cam2/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam2 JPEG compressed transport | Follows raw QoS, Reliable, keep last 8 |
| `/robobaton/cam3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam3 JPEG compressed transport | Follows raw QoS, Reliable, keep last 8 |
| `/robobaton/cam0/camera_info` | `sensor_msgs/msg/CameraInfo` | cam0 width/height info, empty calibration | Reliable + Transient Local, keep last 1 |
| `/robobaton/cam1/camera_info` | `sensor_msgs/msg/CameraInfo` | cam1 width/height info, empty calibration | Reliable + Transient Local, keep last 1 |
| `/robobaton/cam2/camera_info` | `sensor_msgs/msg/CameraInfo` | cam2 width/height info, empty calibration | Reliable + Transient Local, keep last 1 |
| `/robobaton/cam3/camera_info` | `sensor_msgs/msg/CameraInfo` | cam3 width/height info, empty calibration | Reliable + Transient Local, keep last 1 |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42670-P gyro/accel | `SensorDataQoS`, keep last 100 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42670-P temperature | `SensorDataQoS`, keep last 10 |
| `/robobaton/cam0..3/exposure` | `std_msgs/msg/String` | `robobaton_exposure_v1` per-frame ISP observation JSON | Reliable, keep last 8 |
| `/robobaton/imu/timing` | `std_msgs/msg/String` | Per-sample `robobaton_imu_timing_v3` native-clock/output-bridge JSON | Reliable, keep last256 |

Exposure `timestamp_ns` equals that camera's Image stamp, a trigger-edge time by default. `exposure.status=1` is a fixed one-hardware-frame association estimate: a getter obtained while acquiring raw hardware frame N estimates adjacent N+1 only, allowing uint32 wrap, never matched by normalized group IDs or SDK source frame IDs. ROS2 forwards it unchanged and must not shift another frame. No predecessor, hardware gaps, or invalid predecessor queries yield `0`/all zero, without stretching values across gaps. Query failure at N affects N+1; a valid predecessor can still estimate N. Source frame ID/opaque source time and RAW query-completion time retain the older getter's original values, never rewritten to the target image. This certifies neither applied exposure nor a measured physical-error bound. Worker state is zero-initialized per session and primed during warmup without extra image buffering or delivery delay. For the opt-in {ref}`Exposure-Midpoint Test Switch <test-exposure-midpoint>`, set `SC132_TEST_EXPOSURE_MIDPOINT=1` before starting the node/launch: Image/CameraInfo/exposure use trigger time plus half the matched estimate; do not add half exposure again. Set `0` or unset it and restart to restore the original mode. No trigger-delay compensation or certified exposure midpoint; unavailable exposure still stops acquisition. Only newly rebuilt libraries support the switch. See [Exposure Observations](../development/data-contracts.md#per-frame-exposure-observations).

Fixed N→N+1 is only an estimated-association rule. Real AE can have a different effective lag; there is no per-frame applied-exposure guarantee or AE acceptance claim.

## Safe Deployment

The ROS2 install package deploys to `/root/ros2_demo/install`, without touching the non-ROS `/root/demo`. Deployment must verify the transferred content with the full archive checksum, and after unpacking verify the executables, plugins, and related dynamic libraries with the runtime `abi_manifest.sha256`. If the checksum or `abi_manifest.sha256` fails, do not switch, and keep the old `/root/ros2_demo`.

Before switching, confirm the old ROS2 node has exited and keep `cam-service` running; when switching, back up the old `/root/ros2_demo` and roll back to the most recent backup on failure. See [Deployment, Upgrade, and Rollback](../development/deployment-and-upgrade.md) for the full upload, verification, switch, and rollback commands.

## Running

On the X5 device, loading the install-root environment script is recommended. The script loads `/opt/ros/humble/setup.bash` by default, then loads this package's overlay, and sets the FastDDS SHM profile and `RCUTILS_LOGGING_BUFFERED_STREAM=0`:

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

To run a single command once, execute the script directly as a wrapper:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic list --no-daemon --include-hidden-topics
```

When the on-device ROS2 underlay path differs, set `ROBOBATON_ROS_UNDERLAY=/path/to/setup.bash` first. When POSIX `sh` is genuinely required, you must provide the install prefix explicitly:

```sh
. /opt/ros/humble/setup.sh
COLCON_CURRENT_PREFIX=/root/ros2_demo/install \
  . /root/ros2_demo/install/setup.sh
```

IMU-only:

```bash
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args \
  -p enable_camera:=false -p enable_imu:=true
```

Single-camera smoke:

```bash
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args \
  -p enable_camera:=true -p enable_imu:=false -p camera.camera_mask:=1
```

Default combined run:

```bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

### Startup Timestamp Selectors

Set the two keys at the top level of `ros__parameters`, not inside `camera` or `imu`:

```yaml
robobaton_sensors_node:
  ros__parameters:
    camera_timestamp_path: observer
    imu_timestamp_mode: host
```

`camera_timestamp_path` accepts `observer` (default) or `official`; `imu_timestamp_mode` accepts `host` (default) or `tmst`. Edit these independent keys in the installed `config/robobaton_sensors.yaml` used by launch, or use direct-node overrides. All four pairs use the same binary and the same kernel IIO reads/owner; run one at a time:

```bash
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=observer -p imu_timestamp_mode:=host
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=observer -p imu_timestamp_mode:=tmst
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=official -p imu_timestamp_mode:=host
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=official -p imu_timestamp_mode:=tmst
```

Both parameters are read-only after declaration: stop and restart the node to change them, not `ros2 param set`. Invalid values fail before hardware startup even when that sensor is disabled. Consumers explicitly set `SC132_TIMESTAMP_PATH`. Observer retains its `500µs` SIF admission; official uses same-frame RAW IRQ `timestamps − (tv − trig_tv) × 1000`, never starts the SIF observer, and has validity `0`/uncertainty `UINT32_MAX` (unknown physical error). Host preserves MONOTONIC without a physical bound; tmst maps kernel-owned FIFO/UI transition evidence through userspace unwrapping/bounded affine fitting to RAW, with `200µs` computational admission rather than physical accuracy. Neither path falls back or provides FSYNC association/spidev.

Every pair requires a matching **kernel IIO V4 capture module** already bound; the existing V2/V3 module is incompatible even for host. Application deployment does not update the kernel module. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for the current non-ROS HO short smoke and unverified scope. See [Data Contracts](../development/data-contracts.md).

## Quick Check

When viewing the graph, prefer bypassing the possibly-stale daemon:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic list --no-daemon --include-hidden-topics
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 node list --no-daemon
```

If plain `ros2 topic list` must be used, first restart the daemon under the loaded environment:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --restart-daemon
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic list --include-hidden-topics
```

For IMU frequency, prefer the in-package C++ monitor:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

It subscribes to `/robobaton/imu/data` by default and outputs `ROB2_IMU_RATE ... hz=...` every second. The first line after startup may include DDS matching and half a statistics window; judge the stable frequency from the subsequent consecutive lines.

Common override parameters:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor --ros-args \
  -p topic:=/robobaton/imu/data -p report_period_ms:=1000 -p qos_depth:=100
```

raw, compressed, and CameraInfo checks:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic hz /robobaton/cam0/image_raw
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic hz /robobaton/cam0/image_raw/compressed
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic echo /robobaton/cam0/camera_info --once
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic echo /robobaton/imu/temperature --once
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic echo /robobaton/cam0/exposure --once
```

FastDDS SHM and environment variable checks:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --check
```

The current-source profile reserves `256 MiB` per participant; the node, monitor, and each separate subscriber process own a segment each. Three participants require at least `768 MiB` plus DDS metadata and port resources. Check `/dev/shm` and available RAM before starting, leaving headroom for other processes. This budget does not guarantee arbitrary participant counts or loads; other processes must load the same SHM profile. Budget hardening does not establish that every historical initialization error is resolved.

The historical SHM initialization root cause remains unresolved and specialized investigation is paused. Larger segments, stale-file cleanup, or one successful start do not establish a root-cause repair.

Only when the launch has been stopped, `ros2 daemon stop` has run, and you have confirmed there are no `robobaton_sensors_node`, `ros2 launch`, or `ros2 run` processes, may you clean up leftover FastDDS SHM files:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --clean-shm
```

`ros2 topic hz` can be used for interactive diagnosis; formal evidence uniformly uses the in-package C++ monitor to avoid statistics drift between different client implementations.

## YAML Parameters

| Parameter | Default | Boundary / semantics |
|---|---:|---|
| `enable_camera` | `true` | Whether to start the camera publishers. |
| `enable_imu` | `true` | Whether to start the IMU publisher. |
| `camera_timestamp_path` | `observer` | Top-level startup-only/read-only: `observer` or `official`; stop/restart to change. |
| `imu_timestamp_mode` | `host` | Top-level startup-only/read-only: `host` or `tmst`; same IIO capture in both modes. |
| `camera.camera_mask` | `15` | bit0..bit3 map respectively to CAM1..CAM4 / software cam0..cam3; only single or full four-channel is supported, not 2/3 channels. |
| `camera.fps` | `30` | Supports `25/30/40/50/60fps`; other values are rejected before the camera starts. |
| `camera.rotate_degrees` | `0` | Supports `0/90/180/270`; `180` only allows `30fps`, `25/40/50/60fps` rejected; `0/180` output `1280x1088`, `90/270` output `1088x1280`. |
| `camera.frame_set_max_skew_ns` | `10000000` | Group admission bound on trigger-capture differences in ns, not exposure duration or synchronization accuracy. |
| `camera.frame_set_timeout_ms` | `100` | Frame-set wait timeout in ms. |
| `camera.queue_capacity` | `4` | Per-channel ROS publish queue capacity, must be greater than 0. |
| `camera.queue_policy` | `block` | Supports `block`, `drop_newest`; `drop_newest` does not guarantee complete four-frame groups. |
| `camera.publish_camera_info` | `true` | Whether to publish CameraInfo. |
| `camera.image_encoding` | `nv12` | Currently only supports `nv12`. |
| `camera.publish_compressed_image` | `true` | Whether to register raw and compressed image_transport publish plugins. |
| `camera.compressed_jpeg_quality` | `80` | JPEG quality, range `1..100`. |
| `camera.frame_id_prefix` | `robobaton_cam` | Generates frame_ids such as `robobaton_cam0_optical_frame`. |
| `camera.trigger_mode` | `vin_lpwm` | Only VIN LPWM hardware triggering is supported; other values are rejected. |
| `imu.sample_rate_hz` | `800` | Only native `25/50/100/200/400/800/1600`; other values are explicitly rejected. |
| `imu.fsync_diagnostics` | `true` | Startup-only/read-only boolean; false disables independent FSYNC diagnostics without changing normal time or sample delivery. |
| `imu.buffer_capacity` | `4096` | Power of two in256..8192; IIO scan buffer capacity. |
| `imu.fifo_watermark_samples` | `1` | Currently fixed to `1`. |
| `imu.sample_drop_policy` | `allow_counted` | Invalid six-axis payload policy: `allow_counted` or `strict`, not timestamp precision. |
| `imu.frame_id` | `robobaton_imu_link` | Message-source identifier; V2 physical axes pending confirmation, see [Data Contracts](../development/data-contracts.md#imu). |
| `imu.publish_temperature` | `true` | Whether to publish `/robobaton/imu/temperature`. |

Default stable monitor windows should approach configured800Hz; camera and IMU rates are independent. Discover the unique IIO device by name, not a fixed number. Old `imu.read_mode` and `imu.fsync_enabled` association parameters are unsupported; independent diagnostics use `imu.fsync_diagnostics`.

The node requires camera `observer` FIFO/60 (not started in `official`), IMU owner FIFO/20, and publication RR/3 scheduling permission. Failure rejects startup without automatic system changes. STOP retains callback admission and drains consumers before finalization. Final health includes failed-stop diagnostics, scans, records/ACK, fatal/tail status. Topic presence or send counts do not prove DDS delivery.

`diagnostics.rate_metrics_enabled` defaults to false: final `IMU_RUNTIME_HEALTH` reports `imu_published_samples=unavailable imu_publish_count_valid=no`, rather than treating an unmeasured count as zero. When enabled, the field counts successful IMU `publish()` calls and `imu_publish_count_valid=yes`; it is not a DDS delivery acknowledgment. `published_samples` is the separate producer health count, not a substitute for sink or subscriber counts. Disabled diagnostics add no clock reads or metrics updates.

Normal SIGINT/SIGTERM only requests owner-thread exit: stop the producer while keeping admission open until acquisition is quiescent, drain IMU publication, destroy the node, then shut down the ROS context. This order avoids counting a normal `publish()` return on an already-shut-down context as a valid send during normal finalization; it does not guarantee best-effort DDS delivery. Fatal errors may still close the context early and must be judged by failure status and actual received payloads, not the normal-drain contract.

## Data Semantics

raw `Image` uses NV12. `Image.step` keeps the underlying DMA buffer's stride; `data.size()` uses the underlying Y/UV buffer size, which may be larger than the compact `width * height * 3 / 2`. Subscribers must handle alignment per `step` and `data.size()` and must not assume a compact layout.

The compressed topic is a standard `CompressedImage` JPEG payload. The plugin only performs compression when there is an `/image_raw/compressed` subscriber: it validates the NV12 layout per `Image.step` and `data.size()`, copies valid Y/UV rows into the X5 media-codec input buffer, and generates JPEG via `MEDIA_CODEC_ID_JPEG`, preserving the original message `header`.


`header.stamp` is not publication time. Cameras use the selected realtime trigger estimate or opt-in exposure-midpoint estimate. IMU/Temperature use the output adapter's per-burst MONOTONIC→REALTIME bridge in host mode or RAW→REALTIME bridge in tmst mode. `/robobaton/imu/timing` uses `robobaton_imu_timing_v3`, retaining the original MONOTONIC host estimate even in tmst, independent RAW burst time, mode/FIFO TMST/RAW sample/uncertainty, identity, and correctly labeled bridge bases/half-width. The bridge bound and tmst `200µs` computational admission are not physical precision. Backward wall-clock steps remain visible without monotonic clamping or simulation `/clock` conversion. See [Data Contracts](../development/data-contracts.md#imu) for fields/lossless parsing. The six independent FSYNC diagnostic fields match bag/CSV, without nearest-neighbor matching to camera frames or groups. Disable explicitly with `--ros-args -p imu.fsync_diagnostics:=false`, effective after stop/restart.

`CameraInfo` only carries the current frame width/height, with the distortion model and calibration matrices empty. IMU orientation is unavailable, and messages set `orientation_covariance[0] = -1.0`; gyro/accel covariance is currently not fabricated. `robobaton_imu_link` only identifies the source of the IMU message; it does not establish a transform to the camera, base, optical frame, or other coordinate systems, nor declare TF or extrinsics.
