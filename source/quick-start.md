# 快速开始

本页只负责“最快运行成功”。如果 `/root/demo` 或 `/root/ros2_demo/install` 尚未部署，先按 [部署、升级与回滚](deployment-and-upgrade.md) 完成安全部署；单路诊断、UART、详细参数和排错分别见 [non-ROS Demo 使用](non-ros-demo.md)、[ROS2 Demo 使用](ros2-demo.md)、[硬件连接与安全](hardware-and-safety.md) 和 [故障排查](troubleshooting.md)。

## 1. 选择路径

| 目标 | 使用路径 | 适合场景 |
|---|---|---|
| 四路 RTSP、IMU、UART 示例 | non-ROS `/root/demo` | 不接入 ROS2，最快确认视频流和传感器输出。 |
| ROS2 图像和 IMU topics | ROS2 `/root/ros2_demo/install` | 订阅 raw/compressed 图像、CameraInfo、IMU 和温度。 |

两条路径不要同时占用相机资源；切换前先退出旧相机应用，并保持 `cam-service` 运行。

## 2. non-ROS 最短运行

在 X5 SSH 终端执行：

```bash
cd /root/demo
./sensor_demo
```

`sensor_demo` 默认运行四路 SC132 相机、PRRTSP v2 H.264 RTSP 推流和 ICM-42688 IMU 采集。默认图像为 `1280x1088@30fps`；`25/30/40/50fps` 为稳定配置，`60fps` 仅为 stress-only。

四路 RTSP URL：

```text
CAM1 / cam0 -> rtsp://192.168.1.12:554/PRR
CAM2 / cam1 -> rtsp://192.168.1.12:555/PRR
CAM3 / cam2 -> rtsp://192.168.1.12:556/PRR
CAM4 / cam3 -> rtsp://192.168.1.12:557/PRR
```

其中 CAM1/CAM2/CAM3/CAM4 是物理丝印，cam0/cam1/cam2/cam3 是软件相机 ID。

Windows 上可使用 EasyPlayer 查看四路 RTSP 画面。

```{figure} image/rtsp.png
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

期望 topic list 中出现 `/robobaton/cam0..3/image_raw`、`/robobaton/cam0..3/image_raw/compressed`、`/robobaton/cam0..3/camera_info`、`/robobaton/imu/data` 和 `/robobaton/imu/temperature`。raw/compressed 图像 QoS 为 Reliable + KeepLast(8)；CameraInfo 为 Reliable + Transient Local + KeepLast(1)。ROS2 不提供 RTSP；需要 RTSP 时使用 non-ROS `/root/demo`。

## 4. 停止程序

前台运行的 `sensor_demo`、ROS2 launch 或节点使用 `Ctrl+C` 停止。确认退出：

```bash
pgrep -af 'sensor_demo|cam_demo|robobaton_sensors_node|ros2 launch|ros2 run' || true
```

不要通过停止 `cam-service` 来切换 demo。若命令无输出、topic 无数据或 RTSP 无法拉流，先看 [故障排查](troubleshooting.md)；需要单颗相机、IMU、UART 或 YAML 参数细节时，再进入 [non-ROS Demo 使用](non-ros-demo.md) 或 [ROS2 Demo 使用](ros2-demo.md)。
