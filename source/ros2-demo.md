# ROS2 Demo 使用

本页说明 `RoboBaton_4P_ROS2_demo` 的交叉构建、安装包部署、运行和 topic 检查方式。当前 ROS2 路径已完成构建、安装包、板端相机/IMU topic 和 compressed 图像验证；正式 release/tag、产品发布编号和长期支持策略仍待产品确认。

```{important}
ROS2 与 non-ROS RTSP 是两条独立使用路径。ROS2 demo 不提供 RTSP；non-ROS `/root/demo` 运行包和 ROS2 `/root/ros2_demo` install 包不要混用目录、头文件或 `.so`。
```

## 功能边界

ROS2 包名为 `robobaton_4p_ros2_demo`，版本 `0.1.0`。主要产物：

- 节点：`robobaton_sensors_node`
- IMU 频率检查工具：`robobaton_imu_rate_monitor`
- Launch：`launch/robobaton_sensors.launch.py`
- 默认配置：`config/robobaton_sensors.yaml`

已开放能力：

- 四路 raw 图像：`sensor_msgs/msg/Image`，编码 `nv12`。
- 四路 compressed 图像：`sensor_msgs/msg/CompressedImage`，JPEG payload；有 compressed 订阅者时才执行 NV12 -> I420 -> TurboJPEG 压缩。
- 四路 `sensor_msgs/msg/CameraInfo`。
- IMU：`sensor_msgs/msg/Imu`。
- 温度：`sensor_msgs/msg/Temperature`。

当前不提供 RTSP、相机/IMU 硬同步、TF 外参、相机内参或畸变标定。`CameraInfo` 只发布当前帧宽高，标定字段为空；IMU orientation 不可用。

## Topics

| Topic | 消息类型 | 编码/用途 | QoS |
|---|---|---|---|
| `/robobaton/cam0/image_raw` | `sensor_msgs/msg/Image` | cam0 raw NV12 | `SensorDataQoS`，keep last 2 |
| `/robobaton/cam1/image_raw` | `sensor_msgs/msg/Image` | cam1 raw NV12 | `SensorDataQoS`，keep last 2 |
| `/robobaton/cam2/image_raw` | `sensor_msgs/msg/Image` | cam2 raw NV12 | `SensorDataQoS`，keep last 2 |
| `/robobaton/cam3/image_raw` | `sensor_msgs/msg/Image` | cam3 raw NV12 | `SensorDataQoS`，keep last 2 |
| `/robobaton/cam0/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam0 JPEG compressed transport | 跟随 image_transport publisher 的 raw topic QoS |
| `/robobaton/cam1/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam1 JPEG compressed transport | 跟随 image_transport publisher 的 raw topic QoS |
| `/robobaton/cam2/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam2 JPEG compressed transport | 跟随 image_transport publisher 的 raw topic QoS |
| `/robobaton/cam3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | cam3 JPEG compressed transport | 跟随 image_transport publisher 的 raw topic QoS |
| `/robobaton/cam0/camera_info` | `sensor_msgs/msg/CameraInfo` | cam0 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/cam1/camera_info` | `sensor_msgs/msg/CameraInfo` | cam1 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/cam2/camera_info` | `sensor_msgs/msg/CameraInfo` | cam2 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/cam3/camera_info` | `sensor_msgs/msg/CameraInfo` | cam3 宽高信息，标定字段为空 | Reliable + Transient Local，keep last 1 |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42688 gyro/accel | `SensorDataQoS`，keep last 100 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42688 温度 | `SensorDataQoS`，keep last 10 |

## 交叉构建

独立获取 ROS2 demo 仓后，以 `<ros2-demo-root>` 为根执行构建：

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo.git
cd RoboBaton_4P_ROS2_demo

# 将下面路径替换为实际 X5 交叉编译包根目录
export X5_CROSS_ROOT=/absolute/path/to/cross_compile/new
set +u
source /opt/ros/humble/setup.bash
set -u
script/build_x5_ros2.sh --clean --cross-root "$X5_CROSS_ROOT"
```

构建脚本会加载 `<cross-root>/scripts/setup_x5_cross_env.sh`，也可以通过 `--cross-env <path>` 指定交叉环境脚本。默认产物位于：

```text
1.ros2_build/
├── build/
├── install/
└── log/
```

安装包目录为 `1.ros2_build/install`，使用 merged install 布局，包含 `setup.bash`、`setup.sh`、`share/robobaton_4p_ros2_demo/` 和 `lib/robobaton_4p_ros2_demo/`。构建完成后运行包内 verifier：

```bash
python3 script/verify_install.py 1.ros2_build/install
```

如果构建时报 `ModuleNotFoundError: No module named 'ament_package'`，先确认宿主机已经 source `/opt/ros/humble/setup.bash`，且 `/usr/bin/python3` 能导入 `ament_package`。

## 安全部署

下面命令把 install 包上传到 ROS2 独立运行目录，不改动 non-ROS `/root/demo`：

```bash
cd <ros2-demo-root>
tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner \
  -C 1.ros2_build/install \
  -cf /tmp/robobaton_4p_ros2_install.tar .
(cd /tmp && sha256sum robobaton_4p_ros2_install.tar > robobaton_4p_ros2_install.tar.sha256)
ssh root@<x5-ip> "rm -rf /root/ros2_demo.new && mkdir -p /root/ros2_demo.new"
scp /tmp/robobaton_4p_ros2_install.tar \
  /tmp/robobaton_4p_ros2_install.tar.sha256 \
  root@<x5-ip>:/root/ros2_demo.new/
ssh root@<x5-ip> "\
  set -e; \
  cd /root/ros2_demo.new; \
  if ! sha256sum -c robobaton_4p_ros2_install.tar.sha256; then \
    cd /root; \
    rm -rf /root/ros2_demo.new; \
    exit 1; \
  fi; \
  mkdir -p install; \
  tar -xf robobaton_4p_ros2_install.tar -C install; \
  rm -f robobaton_4p_ros2_install.tar robobaton_4p_ros2_install.tar.sha256; \
  cd install/lib/robobaton_4p_ros2_demo; \
  sha256sum -c abi_manifest.sha256"
```

archive checksum 覆盖完整 install tree 传输内容；checksum 失败时不得解包、不得切换，并删除 `/root/ros2_demo.new` 保留旧 `/root/ros2_demo`。解包后执行的 `abi_manifest.sha256` 只覆盖 runtime 可执行文件、插件和相关动态库，是 runtime ABI 子集校验；校验失败时删除 `/root/ros2_demo.new` 并保留旧 `/root/ros2_demo`。

切换前确认旧 ROS2 节点已退出；保持 `cam-service` 运行，不停止或重配该服务：

```bash
ssh root@<x5-ip> "\
  set -e; \
  if pgrep -af 'robobaton_sensors_node|robobaton_imu_rate_monitor'; then \
    echo 'old ROS2 demo process is still running; exit it before switching'; \
    exit 2; \
  fi; \
  ts=\$(date +%Y%m%d-%H%M%S); \
  if [ -d /root/ros2_demo ]; then mv /root/ros2_demo /root/ros2_demo.bak.\$ts; fi; \
  mv /root/ros2_demo.new /root/ros2_demo"
```

回滚时退出新节点，然后恢复最近一次备份：

```bash
ssh root@<x5-ip> "\
  set -e; \
  latest_bak=\$(ls -dt /root/ros2_demo.bak.* 2>/dev/null | head -n 1); \
  test -n \"\$latest_bak\"; \
  mv /root/ros2_demo /root/ros2_demo.failed.\$(date +%Y%m%d-%H%M%S); \
  mv \"\$latest_bak\" /root/ros2_demo"
```

## 运行

X5 板端先加载 ROS Humble，再加载 ROS2 demo overlay：

```bash
source /opt/ros/humble/setup.bash
source /root/ros2_demo/install/setup.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

已搬迁 install 推荐使用 Bash `setup.bash`，它可以自定位当前前缀。确需 POSIX `sh` 时，必须显式提供 install 前缀：

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

IMU 1000Hz 频率优先用包内 C++ monitor：

```bash
ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

默认订阅 `/robobaton/imu/data`，每秒输出 `ROB2_IMU_RATE ... hz=...`。启动后的第一行可能包含 DDS 匹配和半个统计窗口，判断稳定频率时看后续连续多行。

常用覆盖参数：

```bash
ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor --ros-args \
  -p topic:=/robobaton/imu/data -p report_period_ms:=1000 -p qos_depth:=100
```

raw、compressed 和 CameraInfo 检查：

```bash
ros2 topic hz /robobaton/cam0/image_raw
ros2 topic hz /robobaton/cam0/image_raw/compressed
ros2 topic echo /robobaton/cam0/camera_info --once
ros2 topic echo /robobaton/imu/temperature --once
```

`ros2 topic hz` 可用于低频 topic 快速诊断；在 X5 Cortex-A55 上，它可能因 Python 消息构造、回调和统计开销低估 1000Hz IMU topic，不作为本包 IMU 1000Hz 发布率门禁。

## YAML 参数

| 参数 | 默认值 | 边界/语义 |
|---|---:|---|
| `enable_camera` | `true` | 是否启动相机 publisher。 |
| `enable_imu` | `true` | 是否启动 IMU publisher。 |
| `diagnostics.rate_metrics_enabled` | `false` | 默认不输出内部频率指标。 |
| `diagnostics.rate_log_period_ms` | `1000` | 启用 rate metrics 时必须大于 0。 |
| `diagnostics.rate_run_id` | `""` | 仅接受安全 ASCII 标识字符；公开文档不要求使用内部 run ID。 |
| `camera.camera_mask` | `15` | bit0..bit3 对应 cam0..cam3；只支持单颗或完整四路，不支持 2/3 路。 |
| `camera.fps` | `30` | 支持 `25/30/40/50/60fps`；`60fps` 为显式高帧率档。 |
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
| `camera.trigger_mode` | `software_gpio` | 请只使用已验证的 `software_gpio`、`vin_lpwm` 或 `none`。 |
| `imu.sample_rate_hz` | `1000` | ICM-42688 sample rate，建议使用公开支持档位。 |
| `imu.read_mode` | `sensor_timestamp_fifo` | 当前只支持该模式。 |
| `imu.fifo_watermark_samples` | `1` | 当前固定为 `1`。 |
| `imu.frame_id` | `robobaton_imu_link` | IMU frame_id；坐标轴方向待产品确认。 |
| `imu.publish_temperature` | `true` | 是否发布 `/robobaton/imu/temperature`。 |

## 数据语义

raw `Image` 使用 NV12。`Image.step` 保留底层 DMA buffer 的 stride；`data.size()` 使用底层 Y/UV buffer size，可能大于紧凑 `width * height * 3 / 2`。订阅端必须按 `step` 和 `data.size()` 处理对齐，不要假设紧凑布局。

compressed topic 是标准 `CompressedImage` JPEG payload，当前压缩插件使用 TurboJPEG。插件只在有 `/image_raw/compressed` 订阅者时执行 NV12 -> I420 -> JPEG 压缩，保留原始消息的 `header`。

`header.stamp` 不是发布时刻。`software_gpio`/`gpio` 触发模式下，节点启动时冻结 `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset，并把相机 SC132 raw timestamp 映射到 system realtime/ROS stamp；其他 trigger mode 保留底层 SC132 时间域，不声明为 wall/realtime。IMU `sample_timestamp_ns` 会通过同一个冻结 offset 映射到 system realtime/ROS 时间戳；IMU 不使用 `host_timestamp_ns` 作为消息时间。

`CameraInfo` 只带当前帧宽高，畸变模型和标定矩阵为空。IMU orientation 不可用，消息设置 `orientation_covariance[0] = -1.0`；gyro/accel 协方差当前不伪造。
