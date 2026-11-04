# Quick Start

This page only covers "get it running as fast as possible". If `/root/demo` or `/root/ros2_demo/install` is not yet deployed, complete the safe deployment per [Deployment, Upgrade, and Rollback](development/deployment-and-upgrade.md) first; for single-sensor diagnostics, UART, detailed parameters, and error isolation see [non-ROS Demo Usage](usage/non-ros-demo.md), [ROS2 Demo Usage](usage/ros2-demo.md), [Hardware Connection and Safety](getting-started/hardware-and-safety.md), and [Troubleshooting](troubleshooting.md) respectively.

## 1. Choose a Path

| Goal | Usage path | Suitable scenario |
|---|---|---|
| Four-channel RTSP, IMU, UART examples | non-ROS `/root/demo` | Not using ROS2; fastest way to confirm video streams and sensor output. |
| ROS2 image and IMU topics | ROS2 `/root/ros2_demo/install` | Subscribe to raw/compressed images, CameraInfo, exposure observations, IMU, temperature, and IMU timing metadata. |

Do not let the two paths occupy camera resources at the same time; before switching, exit the old camera application and keep `cam-service` running.

## 2. Shortest non-ROS Run

In the X5 SSH terminal:

```bash
cd /root/demo
./sensor_demo
```

`sensor_demo` runs four SC132 cameras, PRRTSP v2 H.264 RTSP, and IIO IMU capture. Library/standalone defaults are800Hz; the checked-in sensor_config.yaml explicitly selects1600Hz, so follow the actual configuration. Images default to1280x1088@30fps with25/30/40/50/60fps and discrete canvases. Accepted parameters do not guarantee sustained saving/ROS2 throughput; see {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

Saving defaults off. See [non-ROS Demo Usage](usage/non-ros-demo.md) and [Saving Data](usage/save-data-guide.md) for bag/MP4, exposure estimates, and four-way startup YAML/CLI examples. Defaults are `camera_timestamp_path: observer` and `imu_timestamp_mode: host`; stop/restart to change to official and/or tmst, in the same binary/IIO path. Every IMU mode requires the matched kernel IIO V3 capture module; V2 is incompatible. Standalone CLI preserves MONOTONIC and tmst additionally reports RAW sample time; saving/ROS2 bridge the selected native clock to realtime. Observer requires read-only `/dev/mem` and retains `500µs` admission; official never starts it and has unknown physical error. TMST `200µs` admission is computational, not physical accuracy; no FSYNC/spidev/fallback. This update performs no board testing or deployment.

Four-channel RTSP URLs:

```text
CAM1 / cam0 -> rtsp://192.168.1.12:554/PRR
CAM2 / cam1 -> rtsp://192.168.1.12:555/PRR
CAM3 / cam2 -> rtsp://192.168.1.12:556/PRR
CAM4 / cam3 -> rtsp://192.168.1.12:557/PRR
```

CAM1/CAM2/CAM3/CAM4 map to software cam0/cam1/cam2/cam3 respectively. The factory address is `192.168.1.12/24`; use the actual device address if it has been changed.

On Windows you can use EasyPlayer to view the four RTSP streams.

```{figure} ../image/rtsp.png
:alt: EasyPlayer showing the RoboBaton 4P default four-channel RTSP streams

EasyPlayer basic playback example: default RTSP ports are `554`, `555`, `556`, `557`, path `/PRR`.
```

Check one stream from the host:

```bash
ffprobe -v error -rtsp_transport tcp \
  -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate \
  -of default=noprint_wrappers=1 \
  rtsp://192.168.1.12:554/PRR
```

Expect `codec_name=h264`, `width=1280`, `height=1088`, and a frame rate close to the target. With H.265 configuration, the codec is expected to be `hevc`.

To save four-channel images and IMU, continue reading {ref}`non-ROS Demo Usage: Saving Four-Channel Images and IMU <non-ros-save>`. The MP4 save example is `./sensor_demo --record-mp4-dir /data/robobaton/mp4_session`; the actual output directory is given by `SENSOR_MP4_RESULT path=`.

## 3. Shortest ROS2 Run

In the X5 SSH terminal:

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

Open another X5 terminal, load the same environment, then check:

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 topic list --no-daemon --include-hidden-topics
ros2 topic hz /robobaton/cam0/image_raw
ros2 topic hz /robobaton/cam0/image_raw/compressed
ros2 topic echo /robobaton/cam0/camera_info --once
ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

Expect four image_raw/compressed, camera_info, and exposure topics plus `/robobaton/imu/data`, `/robobaton/imu/temperature`, and `/robobaton/imu/timing`. Images/exposure use Reliable KeepLast(8), CameraInfo Reliable Transient Local KeepLast(1), timing Reliable KeepLast(256). Exposure is estimated; timing retains host estimates/output bridges, not physical precision. See [ROS2 Demo Usage](usage/ros2-demo.md).

## 4. Stop the Program

Foreground `sensor_demo`, ROS2 launch, or nodes stop with `Ctrl+C`. Confirm exit:

```bash
pgrep -af 'sensor_demo|cam_demo|robobaton_sensors_node|ros2 launch|ros2 run' || true
```

Do not stop `cam-service` to switch demos. If a command produces no output, a topic has no data, or RTSP cannot be pulled, see [Troubleshooting](troubleshooting.md) first; for single-camera, IMU, UART, or YAML parameter details, enter [non-ROS Demo Usage](usage/non-ros-demo.md) or [ROS2 Demo Usage](usage/ros2-demo.md).

## Detailed Usage

```{toctree}
:maxdepth: 1

usage/non-ros-demo
usage/save-data-guide
usage/ros2-demo
usage/usb-gadget-switch
```
