# ROS2 Demo 使用

本页说明 `RoboBaton_4P_ROS2_demo` 运行和 topic 检查方式。当前 ROS2 路径已完成构建、安装包、板端相机/IMU topic 和 compressed 图像验证。

```{important}
ROS2 与 non-ROS RTSP 是两条独立使用路径。ROS2 demo 不提供 RTSP；non-ROS `/root/demo` 运行包和 ROS2 `/root/ros2_demo` install 包不要混用目录、头文件或 `.so`。
```

## 功能边界

ROS2 包名为 `robobaton_4p_ros2_demo`，版本 `1.0.0`。主要产物：

- 节点：`robobaton_sensors_node`
- IMU 频率检查工具：`robobaton_imu_rate_monitor`
- Launch：`launch/robobaton_sensors.launch.py`
- 默认配置：`config/robobaton_sensors.yaml`
- 安装环境脚本：install 根目录的 `robobaton_ros2_env.bash`，用于统一加载 ROS2 underlay、本包 overlay、FastDDS SHM profile 和日志缓冲设置。

已开放能力：

- 四路 raw 图像：`sensor_msgs/msg/Image`，编码 `nv12`。
- 四路 compressed 图像：`sensor_msgs/msg/CompressedImage`，JPEG payload；有 compressed 订阅者时才把有效 NV12 行复制到 X5 media-codec 内部输入 buffer，并以 `MEDIA_CODEC_ID_JPEG` 执行硬件单帧压缩。
- 四路 `sensor_msgs/msg/CameraInfo`。
- IMU：`sensor_msgs/msg/Imu`。
- 温度：`sensor_msgs/msg/Temperature`。

当前不提供 RTSP、相机/IMU 硬同步、TF 外参、相机内参或畸变标定。`CameraInfo` 只发布当前帧宽高，标定字段为空；IMU orientation 不可用。

物理相机丝印到 ROS2 prefix 的映射为 CAM1 -> `/robobaton/cam0`、CAM2 -> `/robobaton/cam1`、CAM3 -> `/robobaton/cam2`、CAM4 -> `/robobaton/cam3`；完整 RTSP 端口映射见 [硬件连接与安全](hardware-and-safety.md#相机接口)。

## Topics

| Topic | 消息类型 | 编码/用途 | QoS |
|---|---|---|---|
| `/robobaton/cam0/image_raw` | `sensor_msgs/msg/Image` | cam0 raw NV12 | Reliable，keep last 8 |
| `/robobaton/cam1/image_raw` | `sensor_msgs/msg/Image` | cam1 raw NV12 | Reliable，keep last 8 |
| `/robobaton/cam2/image_raw` | `sensor_msgs/msg/Image` | cam2 raw NV12 | Reliable，keep last 8 |
| `/robobaton/cam3/image_raw` | `sensor_msgs/msg/Image` | cam3 raw NV12 | Reliable，keep last 8 |
| `/robobaton/cam0/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam0 JPEG compressed transport | 跟随 raw QoS，Reliable，keep last 8 |
| `/robobaton/cam1/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam1 JPEG compressed transport | 跟随 raw QoS，Reliable，keep last 8 |
| `/robobaton/cam2/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam2 JPEG compressed transport | 跟随 raw QoS，Reliable，keep last 8 |
| `/robobaton/cam3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam3 JPEG compressed transport | 跟随 raw QoS，Reliable，keep last 8 |
| `/robobaton/cam0/camera_info` | `sensor_msgs/msg/CameraInfo` | cam0 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/cam1/camera_info` | `sensor_msgs/msg/CameraInfo` | cam1 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/cam2/camera_info` | `sensor_msgs/msg/CameraInfo` | cam2 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/cam3/camera_info` | `sensor_msgs/msg/CameraInfo` | cam3 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42688 gyro/accel | `SensorDataQoS`，keep last 100 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42688 温度 | `SensorDataQoS`，keep last 10 |

## 安全部署

ROS2 install 包部署到 `/root/ros2_demo/install`，不改动 non-ROS `/root/demo`。部署必须使用完整 archive checksum 校验传输内容，解包后再用 runtime `abi_manifest.sha256` 校验可执行文件、插件和相关动态库。checksum 或 `abi_manifest.sha256` 失败时不得切换，保留旧 `/root/ros2_demo`。

切换前确认旧 ROS2 节点已退出，保持 `cam-service` 运行；切换时备份旧 `/root/ros2_demo`，失败时按最近备份回滚。完整上传、校验、切换和回滚命令见 [部署、升级与回滚](deployment-and-upgrade.md)。

## 运行

X5 板端推荐加载 install 根目录环境脚本。脚本默认加载 `/opt/ros/humble/setup.bash`，再加载本包 overlay，并设置 FastDDS SHM profile 和 `RCUTILS_LOGGING_BUFFERED_STREAM=0`：

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

只想运行一次命令时，可以直接执行脚本作为 wrapper：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic list --no-daemon --include-hidden-topics
```

板端 ROS2 underlay 路径不同时，先设置 `ROBOBATON_ROS_UNDERLAY=/path/to/setup.bash`。确需 POSIX `sh` 时，必须显式提供 install 前缀：

```sh
. /opt/ros/humble/setup.sh
COLCON_CURRENT_PREFIX=/root/ros2_demo/install \
  . /root/ros2_demo/install/setup.sh
```

IMU-only：

```bash
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args \
  -p enable_camera:=false -p enable_imu:=true
```

单颗相机 smoke：

```bash
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args \
  -p enable_camera:=true -p enable_imu:=false -p camera.camera_mask:=1
```

默认联合运行：

```bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

## 快速检查

查看 graph 时优先绕过可能过期的 daemon：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic list --no-daemon --include-hidden-topics
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 node list --no-daemon
```

如果必须使用普通 `ros2 topic list`，先在已加载环境下重启 daemon：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --restart-daemon
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic list --include-hidden-topics
```

IMU 1000Hz 频率优先用包内 C++ monitor：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

默认订阅 `/robobaton/imu/data`，每秒输出 `ROB2_IMU_RATE ... hz=...`。启动后的第一行可能包含 DDS 匹配和半个统计窗口，判断稳定频率时看后续连续多行。

常用覆盖参数：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor --ros-args \
  -p topic:=/robobaton/imu/data -p report_period_ms:=1000 -p qos_depth:=100
```

raw、compressed 和 CameraInfo 检查：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic hz /robobaton/cam0/image_raw
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic hz /robobaton/cam0/image_raw/compressed
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic echo /robobaton/cam0/camera_info --once
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic echo /robobaton/imu/temperature --once
```

FastDDS SHM 和环境变量检查：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --check
```

只有在已停止 launch、`ros2 daemon stop` 且确认没有 `robobaton_sensors_node`、`ros2 launch`、`ros2 run` 进程时，才允许清理遗留 FastDDS SHM 文件：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --clean-shm
```

`ros2 topic hz` 可用于低频 topic 快速诊断；在 X5 Cortex-A55 上，它可能因 Python 消息构造、回调和统计开销低估 1000Hz IMU topic，不作为本包 IMU 1000Hz 发布率门禁。

## YAML 参数

| 参数 | 默认值 | 边界/语义 |
|---|---:|---|
| `enable_camera` | `true` | 是否启动相机 publisher。 |
| `enable_imu` | `true` | 是否启动 IMU publisher。 |
| `camera.camera_mask` | `15` | bit0..bit3 对应软件 cam0..cam3，即物理 CAM1..CAM4；只支持单颗或完整四路，不支持 2/3 路。 |
| `camera.fps` | `30` | `25/30/40/50fps` 为 V1 稳定功能配置；`60fps` 是显式 `stress-only` 压力配置，不是稳定发布 profile。 |
| `camera.rotate_degrees` | `0` | 支持 `0/90/180/270`；`180` 只允许 `30fps`，`25/40/50/60fps`均拒绝。 |
| `camera.frame_set_max_skew_ns` | `2000000` | 帧组放行上限，单位 ns。 |
| `camera.frame_set_timeout_ms` | `100` | 帧组等待超时，单位 ms。 |
| `camera.queue_capacity` | `4` | 每路 ROS 发布队列容量，必须大于 0。 |
| `camera.queue_policy` | `block` | 支持 `block`、`drop_newest`；`drop_newest` 不保证完整四帧组。 |
| `camera.publish_camera_info` | `true` | 是否发布 CameraInfo。 |
| `camera.image_encoding` | `nv12` | 当前只支持 `nv12`。 |
| `camera.publish_compressed_image` | `true` | 是否注册 raw 与 compressed image_transport 发布插件。 |
| `camera.compressed_jpeg_quality` | `80` | JPEG quality，范围 `1..100`。 |
| `camera.frame_id_prefix` | `robobaton_cam` | 生成 `robobaton_cam0_optical_frame` 等 frame_id。 |
| `camera.trigger_mode` | `software_gpio` | 只有 `software_gpio` 是 V1 已验证模式；`vin_lpwm`、`none` 为实验性 / 未验收参数。 |
| `imu.sample_rate_hz` | `1000` | ICM-42688 sample rate，建议使用公开支持档位。 |
| `imu.read_mode` | `sensor_timestamp_fifo` | 当前只支持该模式。 |
| `imu.fifo_watermark_samples` | `1` | 当前固定为 `1`。 |
| `imu.frame_id` | `robobaton_imu_link` | IMU frame_id；完整加速度符号约定见[数据合同](data-contracts.md#imu)。 |
| `imu.publish_temperature` | `true` | 是否发布 `/robobaton/imu/temperature`。 |

## 数据语义

raw `Image` 使用 NV12。`Image.step` 保留底层 DMA buffer 的 stride；`data.size()` 使用底层 Y/UV buffer size，可能大于紧凑 `width * height * 3 / 2`。订阅端必须按 `step` 和 `data.size()` 处理对齐，不要假设紧凑布局。

compressed topic 是标准 `CompressedImage` JPEG payload。插件只在有 `/image_raw/compressed` 订阅者时执行压缩：它按 `Image.step` 和 `data.size()` 校验 NV12 布局，把有效 Y/UV 行复制到 X5 media-codec 输入 buffer，并通过 `MEDIA_CODEC_ID_JPEG` 生成 JPEG，保留原始消息的 `header`。


`header.stamp` 不是发布时刻。在 V1 已验证的 `software_gpio` 模式下，节点启动时冻结 `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset，并把相机 SC132 raw timestamp 映射到 system realtime/ROS stamp。实验性的 `vin_lpwm` 和 `none` 保留底层 SC132 时间域，不声明为 V1 wall/realtime 合同。IMU `sample_timestamp_ns` 会通过同一个冻结 offset 映射到 system realtime/ROS 时间戳；IMU 不使用 `host_timestamp_ns` 作为消息时间。

`CameraInfo` 只带当前帧宽高，畸变模型和标定矩阵为空。IMU orientation 不可用，消息设置 `orientation_covariance[0] = -1.0`；gyro/accel 协方差当前不伪造。`robobaton_imu_link` 只标识 IMU 消息来源；它不建立到相机、base、optical frame 或其他坐标系的变换，也不声明 TF 或外参。
