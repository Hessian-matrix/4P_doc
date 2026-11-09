# 快速开始

本页只负责“最快运行成功”。如果 `/root/demo` 或 `/root/ros2_demo/install` 尚未部署，先按 [部署、升级与回滚](development/deployment-and-upgrade.md) 完成安全部署；单路诊断、UART、详细参数和排错分别见 [non-ROS Demo 使用](usage/non-ros-demo.md)、[ROS2 Demo 使用](usage/ros2-demo.md)、[硬件连接与安全](getting-started/hardware-and-safety.md) 和 [故障排查](troubleshooting.md)。

使用随板预烧录的发布版系统时，开机已自动启动 `sensor_demo`。只需在同一可信局域网浏览器打开 `http://192.168.1.12/`（按实际板卡地址修改），即可查看四路相机、IMU 和控制录包，无需执行下文的手动启动命令；图示与步骤见{ref}`首次上电：网页使用 <first-boot-web>`。

## 1. 选择路径

| 目标 | 使用路径 | 适合场景 |
|---|---|---|
| 网页预览与录包 | 开机自启的 `sensor_demo` | 无需 SSH，直接在浏览器查看传感器并开始/停止录制。 |
| 四路 RTSP、IMU、UART 示例 | non-ROS `/root/demo` | 不接入 ROS2，最快确认视频流和传感器输出。 |
| ROS2 图像和 IMU topics | ROS2 `/root/ros2_demo/install` | 订阅 raw/compressed 图像、CameraInfo、曝光观测、IMU、温度与IMU 时钟元数据。 |

两条路径不要同时占用相机资源。执行下文手动启动或 ROS2 命令前，先按[首次上电：停止应用](getting-started/first-boot.md#7-停止应用)停止开机自启实例，并确认正常退出；保持 `cam-service` 运行。网页“停止录制”不等于退出应用。

## 2. non-ROS 最短运行

仅在需要手动运行且旧相机应用已退出后，在 X5 SSH 终端执行；本节显式开启 RTSP，供后续播放器检查：

```bash
cd /root/demo
./sensor_demo --rtsp
```

`sensor_demo` 默认运行四路 SC132 相机、H.264 网页预览和 ICM-42670-P IMU（原生默认 `800Hz`）采集；RTSP 默认关闭，本节命令用 `--rtsp` 显式开启 PRRTSP v2 推流。默认图像为 `1280x1088@30fps`，支持 `25/30/40/50/60fps`；输出画布支持 `1280x1088`/`640x480`/`720x480`/`1280x720`。这是实现的参数集合，不保证所有保存/ROS2 路径持续达到目标帧率或零丢失；当前已验证范围与未闭环问题见{ref}`能力与验证边界 <capability-verification-boundary>`。

默认不保存。bag/MP4、曝光估计及四组合启动 YAML/CLI 示例见 [non-ROS 使用](usage/non-ros-demo.md) 与[数据保存](usage/save-data-guide.md)。默认 `camera_timestamp_path: observer`、`imu_timestamp_mode: host`；停止/重启后切换 official 和/或 tmst，仍使用相同二进制/IIO 路径。所有 IMU 模式均要求匹配的内核 IIO V4 capture 模块，V2/V3 不兼容。独立 CLI 保留 MONOTONIC，tmst 另报告 RAW sample；保存/ROS2 将所选原生时钟桥接到 realtime。observer 需 `/dev/mem` 只读权限并保留 `500µs` admission；official 不启动 observer，物理误差未知。TMST `200µs` admission 是计算边界而非物理精度，提供独立FSYNC诊断，无触发关联／spidev／回退。当前 non-ROS HO 短窗证据及未验收范围见{ref}`能力与验证边界 <capability-verification-boundary>`。

四路 RTSP URL：

```text
CAM1 / cam0 -> rtsp://192.168.1.12:554/PRR
CAM2 / cam1 -> rtsp://192.168.1.12:555/PRR
CAM3 / cam2 -> rtsp://192.168.1.12:556/PRR
CAM4 / cam3 -> rtsp://192.168.1.12:557/PRR
```

CAM1/CAM2/CAM3/CAM4 依次对应软件 cam0/cam1/cam2/cam3。出厂地址为 `192.168.1.12/24`；如已修改地址，使用设备实际地址。

Windows 上可使用 EasyPlayer 查看四路 RTSP 画面。

```{figure} ../image/rtsp.png
:alt: EasyPlayer 显示 RoboBaton 4P 默认四路 RTSP 画面

EasyPlayer 基本上电播放示例：默认 RTSP 端口为 `554`、`555`、`556`、`557`，path 为 `/PRR`。
```

开发机检查一路：

```bash
ffprobe -v error -rtsp_transport tcp \
  -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate \
  -of default=noprint_wrappers=1 \
  rtsp://192.168.1.12:554/PRR
```

期望看到 `codec_name=h264`、`width=1280`、`height=1088` 和接近目标的帧率。使用 H.265 配置时，codec 期望为 `hevc`。

需要保存四路图像与 IMU 时，继续阅读 {ref}`non-ROS Demo 使用：保存四路图像与 IMU <non-ros-save>`。MP4 保存示例为 `./sensor_demo --record-mp4-dir /data/robobaton/mp4_session`，实际输出目录以 `SENSOR_MP4_RESULT path=` 为准。

## 3. ROS2 最短运行

在 X5 SSH 终端执行：

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

另开一个 X5 终端，加载同一环境后检查：

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 topic list --no-daemon --include-hidden-topics
ros2 topic hz /robobaton/cam0/image_raw
ros2 topic hz /robobaton/cam0/image_raw/compressed
ros2 topic echo /robobaton/cam0/camera_info --once
ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

期望 topic list 包含四路 image_raw/compressed、camera_info、exposure，以及 `/robobaton/imu/data`、`/robobaton/imu/temperature`、`/robobaton/imu/timing`。图像/exposure 为 Reliable KeepLast(8)，CameraInfo 为 Reliable Transient Local KeepLast(1)，IMU timing 为 Reliable KeepLast(256)。曝光仅为估计，timing 保留主机估计和输出桥证据而非物理精度；详见 [ROS2 Demo 使用](usage/ros2-demo.md)。

## 4. 停止程序

前台运行的 `sensor_demo`、ROS2 launch 或节点使用 `Ctrl+C` 停止。确认退出：

开机自启的后台程序使用 `/root/demo/start_sensor_demo.sh stop` 正常停止，等待命令成功返回；不要重复启动或强杀。网页“停止录制”只停止保存，不退出采集程序。

```bash
pgrep -af 'sensor_demo|cam_demo|robobaton_sensors_node|ros2 launch|ros2 run' || true
```

不要通过停止 `cam-service` 来切换 demo。若命令无输出、topic 无数据或 RTSP 无法拉流，先看 [故障排查](troubleshooting.md)；需要单颗相机、IMU、UART 或 YAML 参数细节时，再进入 [non-ROS Demo 使用](usage/non-ros-demo.md) 或 [ROS2 Demo 使用](usage/ros2-demo.md)。

## 具体使用

```{toctree}
:maxdepth: 1

usage/non-ros-demo
usage/save-data-guide
usage/ros2-demo
usage/usb-gadget-switch
```
