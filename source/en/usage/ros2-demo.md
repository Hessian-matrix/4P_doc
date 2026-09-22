# ROS2 Demo Usage

The current `v1.3.0` ROS2 package has completed build and install-package verification; after deploying to the target board, you must still actually check topics, compressed images, and the required frame rate — do not infer runtime results from the install verifier alone.

```{important}
ROS2 and non-ROS RTSP are two independent usage paths. The ROS2 demo does not provide RTSP; do not mix directories, headers, or `.so` between the non-ROS `/root/demo` runtime package and the ROS2 `/root/ros2_demo` install package.
```

## Feature Boundary

The ROS2 package is named `robobaton_4p_ros2_demo`, version `1.3.0`. Main artifacts:

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

RTSP, camera/IMU hardware sync, TF extrinsics, camera intrinsics, and distortion calibration are currently not provided. `CameraInfo` only publishes the current frame width/height, with empty calibration fields; IMU orientation is unavailable.

The physical silkscreen-to-ROS2-prefix mapping is CAM1 -> `/robobaton/cam0`, CAM2 -> `/robobaton/cam1`, CAM3 -> `/robobaton/cam2`, CAM4 -> `/robobaton/cam3`; for the full RTSP port mapping see [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#camera-interface).

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
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42688 gyro/accel | `SensorDataQoS`, keep last 100 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42688 temperature | `SensorDataQoS`, keep last 10 |

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
```

FastDDS SHM and environment variable checks:

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --check
```

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
| `camera.camera_mask` | `15` | bit0..bit3 correspond to software cam0..cam3, i.e. physical CAM1..CAM4; only single or full four-channel is supported, not 2/3 channels. |
| `camera.fps` | `30` | Supports `25/30/40/50/60fps`; other values are rejected before the camera starts. |
| `camera.rotate_degrees` | `0` | Supports `0/90/180/270`; `180` only allows `30fps`, `25/40/50/60fps` rejected; `0/180` output `1280x1088`, `90/270` output `1088x1280`. |
| `camera.frame_set_max_skew_ns` | `10000000` | Frame-set admission upper bound in ns; by default covers the four-channel 10 ms exposure bound. |
| `camera.frame_set_timeout_ms` | `100` | Frame-set wait timeout in ms. |
| `camera.queue_capacity` | `4` | Per-channel ROS publish queue capacity, must be greater than 0. |
| `camera.queue_policy` | `block` | Supports `block`, `drop_newest`; `drop_newest` does not guarantee complete four-frame groups. |
| `camera.publish_camera_info` | `true` | Whether to publish CameraInfo. |
| `camera.image_encoding` | `nv12` | Currently only supports `nv12`. |
| `camera.publish_compressed_image` | `true` | Whether to register raw and compressed image_transport publish plugins. |
| `camera.compressed_jpeg_quality` | `80` | JPEG quality, range `1..100`. |
| `camera.frame_id_prefix` | `robobaton_cam` | Generates frame_ids such as `robobaton_cam0_optical_frame`. |
| `camera.trigger_mode` | `software_gpio` | Only `software_gpio` is a V1-verified mode; `none` is only for explicit free-run diagnostics. |
| `imu.sample_rate_hz` | `1000` | Only accepts `25/50/100/200/500/1000/2000`. |
| `imu.read_mode` | `sensor_timestamp_fifo` | Currently only this mode is supported. |
| `imu.fifo_watermark_samples` | `1` | Currently fixed to `1`. |
| `imu.frame_id` | `robobaton_imu_link` | IMU frame_id; for the full acceleration sign convention see [Data Contracts](../development/data-contracts.md#imu). |
| `imu.publish_temperature` | `true` | Whether to publish `/robobaton/imu/temperature`. |

## Data Semantics

raw `Image` uses NV12. `Image.step` keeps the underlying DMA buffer's stride; `data.size()` uses the underlying Y/UV buffer size, which may be larger than the compact `width * height * 3 / 2`. Subscribers must handle alignment per `step` and `data.size()` and must not assume a compact layout.

The compressed topic is a standard `CompressedImage` JPEG payload. The plugin only performs compression when there is an `/image_raw/compressed` subscriber: it validates the NV12 layout per `Image.step` and `data.size()`, copies valid Y/UV rows into the X5 media-codec input buffer, and generates JPEG via `MEDIA_CODEC_ID_JPEG`, preserving the original message `header`.


`header.stamp` is not the publish moment. In the V1-verified `software_gpio` mode, the node freezes the `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset at startup and maps the camera SC132 raw timestamp to system realtime/ROS stamp. The explicit `none` diagnostic mode keeps the underlying SC132 time domain and is not declared as a V1 wall/realtime contract. IMU `sample_timestamp_ns` is mapped to system realtime/ROS timestamps through the same frozen offset; IMU does not use `host_timestamp_ns` as the message time.

`CameraInfo` only carries the current frame width/height, with the distortion model and calibration matrices empty. IMU orientation is unavailable, and messages set `orientation_covariance[0] = -1.0`; gyro/accel covariance is currently not fabricated. `robobaton_imu_link` only identifies the source of the IMU message; it does not establish a transform to the camera, base, optical frame, or other coordinate systems, nor declare TF or extrinsics.
