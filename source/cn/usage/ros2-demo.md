# ROS2 Demo 使用

本页说明 V2 当前源码的 ROS2 使用方式。目标板使用前仍须检查 topic、compressed 图像、IMU 原生速率和所需帧率；构建或 install 校验不替代实际运行检查。

参数支持不代表所有模式/负载/时长或 DDS 全部送达；旧组成不能认证当前 IIO 组成。见{ref}`能力与验证边界 <capability-verification-boundary>`。

```{important}
ROS2 与 non-ROS RTSP 是两条独立使用路径。ROS2 demo 不提供 RTSP；non-ROS `/root/demo` 运行包和 ROS2 `/root/ros2_demo` install 包不要混用目录、头文件或 `.so`。
```

## 功能边界

ROS2 包名为 `robobaton_4p_ros2_demo`；软件版本以包内 `VERSION`/`package.xml` 和 `--version` 为准，不因 V2 硬件或文档修订自动改变。主要产物：

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
- 逐帧 ISP 曝光观测，以及逐样本 IMU 原生时钟/输出桥 timing JSON。

不提供 RTSP、物理采样/曝光同步保证、TF 外参或相机标定。CameraInfo 仅当前宽高，IMU orientation 不可用；没有 FSYNC 关联。

CAM1..CAM4 依次对应软件 cam0..cam3 与 `/robobaton/cam0..3`；见[硬件连接与安全](../getting-started/hardware-and-safety.md#相机接口)。

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
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42670-P gyro/accel | `SensorDataQoS`，keep last 100 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42670-P 温度 | `SensorDataQoS`，keep last 10 |
| `/robobaton/cam0..3/exposure` | `std_msgs/msg/String` | `robobaton_exposure_v1` 逐帧 ISP 观测 JSON | Reliable，keep last 8 |
| `/robobaton/imu/timing` | `std_msgs/msg/String` | 每样本 `robobaton_imu_timing_v3` 原生时钟/输出桥 JSON | Reliable，keep last256 |

曝光消息中的 `timestamp_ns` 与该路 Image stamp 一致，默认是触发沿时间。`exposure.status=1` 是固定单硬件帧关联估计：采集原始硬件帧 N 时取得的 getter 只估计相邻 N+1（允许 uint32 回绕），不按归一化组号或 SDK 源帧号匹配；ROS2 原样转发，不能再移一帧。无前驱、硬件缺口或无效前驱查询时 `0` 且全零，不跨缺口延用；N 查询失败影响 N+1，有效前驱仍可估计 N。源帧号/opaque 源时间和 RAW 查询完成时间保留更早 getter 原值，不改写为目标图像；没有实际生效曝光证明或已测物理误差上界。各 worker 会话状态清零并在 warmup 中预热，无额外图像缓冲或交付延迟。显式 {ref}`曝光中点测试开关 <test-exposure-midpoint>` 需在节点/launch 启动前设置 `SC132_TEST_EXPOSURE_MIDPOINT=1`，Image/CameraInfo/exposure 使用触发时间加匹配估计半时长；不要再次加半曝光。设 `0` 或取消变量后重启恢复。该模式不补偿触发延迟、不提供真实曝光中点，曝光不可用时仍停止采集；仅新重建的库支持。详见[逐帧曝光观测](../development/data-contracts.md#逐帧曝光观测)。

固定 N→N+1 只是估计关联规则；真实 AE 的有效滞后可能不同，不保证任何一帧实际应用的曝光，也不构成 AE 验收。

## 安全部署

ROS2 install 包部署到 `/root/ros2_demo/install`，不改动 non-ROS `/root/demo`。部署必须使用完整 archive checksum 校验传输内容，解包后再用 runtime `abi_manifest.sha256` 校验可执行文件、插件和相关动态库。checksum 或 `abi_manifest.sha256` 失败时不得切换，保留旧 `/root/ros2_demo`。

切换前确认旧 ROS2 节点已退出，保持 `cam-service` 运行；切换时备份旧 `/root/ros2_demo`，失败时按最近备份回滚。完整上传、校验、切换和回滚命令见 [部署、升级与回滚](../development/deployment-and-upgrade.md)。

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

### 启动时间戳 selector

两个键放在 `ros__parameters` 顶层，不在 `camera` 或 `imu` 下：

```yaml
robobaton_sensors_node:
  ros__parameters:
    camera_timestamp_path: observer
    imu_timestamp_mode: host
```

`camera_timestamp_path` 接受 `observer`（默认）或 `official`；`imu_timestamp_mode` 接受 `host`（默认）或 `tmst`。可修改 launch 使用的已安装 `config/robobaton_sensors.yaml` 中这两个独立键，或直接运行节点并覆盖参数。四种组合共用同一二进制与同一内核 IIO 读取/owner，每次只运行一个：

```bash
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=observer -p imu_timestamp_mode:=host
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=observer -p imu_timestamp_mode:=tmst
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=official -p imu_timestamp_mode:=host
ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --ros-args -p camera_timestamp_path:=official -p imu_timestamp_mode:=tmst
```

两参数声明后只读，切换须停止并重启节点，不能用 `ros2 param set` 热切换。即使禁用该传感器，非法值也在硬件启动前拒绝。consumer 显式设置 `SC132_TIMESTAMP_PATH`。observer 保留 `500µs` SIF admission；official 使用同帧 RAW IRQ `timestamps − (tv − trig_tv) × 1000`，绝不启动 SIF observer，validity 为 `0`、uncertainty 为 `UINT32_MAX`（物理误差未知）。host 保留 MONOTONIC，无物理上界；tmst 依据内核拥有的 FIFO/UI 跳变证据，由用户态解绕/有界仿射拟合到 RAW，`200µs` 是计算 admission 而非物理精度。均不回退，也不提供 FSYNC 关联或 spidev。

每种组合均要求设备已绑定匹配的 **内核 IIO V4 capture 模块**；现有 V2/V3 模块即使 host 模式也不兼容。应用部署不更新内核模块。当前 non-ROS HO 短窗证据及未验收范围见{ref}`能力与验证边界 <capability-verification-boundary>`。不声明四组合实板验收通过。见[数据合同](../development/data-contracts.md)。

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

IMU频率优先用包内 C++ monitor：

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
/root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic echo /robobaton/cam0/exposure --once
```

FastDDS SHM 和环境变量检查：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --check
```

当前源码 profile 为每个 participant 预留 `256 MiB`；节点、monitor 和每个独立订阅进程分别占一份。三个 participant 至少需要 `768 MiB` 加 DDS 元数据和端口资源；启动前检查 `/dev/shm` 与可用 RAM，并为其他进程保留余量。该预算不保证任意 participant 数或负载可用；其他进程也须加载相同 SHM profile，不要把容量加固当成所有历史初始化错误已解决。

历史 SHM 初始化问题的根因仍未解决，专项定位已暂停；增大 segment、清理遗留文件或单次启动成功都不证明根因已修复。

只有在已停止 launch、`ros2 daemon stop` 且确认没有 `robobaton_sensors_node`、`ros2 launch`、`ros2 run` 进程时，才允许清理遗留 FastDDS SHM 文件：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash --clean-shm
```

`ros2 topic hz`可用于交互诊断；正式证据统一使用包内C++ monitor，避免不同客户端实现造成统计口径漂移。

## YAML 参数

| 参数 | 默认值 | 边界/语义 |
|---|---:|---|
| `enable_camera` | `true` | 是否启动相机 publisher。 |
| `enable_imu` | `true` | 是否启动 IMU publisher。 |
| `camera_timestamp_path` | `observer` | 顶层启动只读：`observer` 或 `official`；停止/重启后切换。 |
| `imu_timestamp_mode` | `host` | 顶层启动只读：`host` 或 `tmst`；两模式使用相同 IIO 采集。 |
| `camera.camera_mask` | `15` | bit0..bit3 依次对应 CAM1..CAM4 / 软件 cam0..cam3；只支持单颗或完整四路，不支持 2/3 路。 |
| `camera.fps` | `30` | 支持`25/30/40/50/60fps`；其他值在启动相机前拒绝。 |
| `camera.rotate_degrees` | `0` | 支持 `0/90/180/270`；`180` 只允许 `30fps`，`25/40/50/60fps`拒绝；`0/180` 输出 `1280x1088`，`90/270` 输出 `1088x1280`。 |
| `camera.frame_set_max_skew_ns` | `10000000` | 组内触发捕获差异的放行上限，单位 ns；不表示曝光时长或同步精度。 |
| `camera.frame_set_timeout_ms` | `100` | 帧组等待超时，单位 ms。 |
| `camera.queue_capacity` | `4` | 每路 ROS 发布队列容量，必须大于 0。 |
| `camera.queue_policy` | `block` | 支持 `block`、`drop_newest`；`drop_newest` 不保证完整四帧组。 |
| `camera.publish_camera_info` | `true` | 是否发布 CameraInfo。 |
| `camera.image_encoding` | `nv12` | 当前只支持 `nv12`。 |
| `camera.publish_compressed_image` | `true` | 是否注册 raw 与 compressed image_transport 发布插件。 |
| `camera.compressed_jpeg_quality` | `80` | JPEG quality，范围 `1..100`。 |
| `camera.frame_id_prefix` | `robobaton_cam` | 生成 `robobaton_cam0_optical_frame` 等 frame_id。 |
| `camera.trigger_mode` | `vin_lpwm` | 仅支持 VIN LPWM 硬件触发；其他值拒绝。 |
| `imu.sample_rate_hz` | `800` | 只接受原生 `25/50/100/200/400/800/1600`；其他值明确拒绝。 |
| `imu.fsync_diagnostics` | `true` | 启动只读boolean；false关闭独立FSYNC诊断，不改变正常时间或样本交付。 |
| `imu.buffer_capacity` | `4096` | 256..8192的2次幂；IIO scan 缓冲容量。 |
| `imu.fifo_watermark_samples` | `1` | 当前固定为 `1`。 |
| `imu.sample_drop_policy` | `allow_counted` | 无效六轴 payload 策略：`allow_counted` 或 `strict`，不是时间精度策略。 |
| `imu.frame_id` | `robobaton_imu_link` | 消息来源标识；V2 物理轴向尚待确认，见[数据合同](../development/data-contracts.md#imu)。 |
| `imu.publish_temperature` | `true` | 是否发布 `/robobaton/imu/temperature`。 |

默认 monitor 稳定窗口应接近配置800Hz，相机和 IMU 速率独立。库按唯一 IIO name 发现设备，不假定编号；旧 `imu.read_mode` 与 `imu.fsync_enabled` 关联参数不再支持；独立诊断使用 `imu.fsync_diagnostics`。

节点需要相机 `observer` FIFO/60（`official` 不启动该线程）、IMU owner FIFO/20、发布 RR/3 的实时调度权限，失败拒绝启动，不自动修改系统设置。STOP 保持 callback 接纳、排空 consumer 后终结；最终 health 含失败 stop 诊断、scan、record/ACK、fatal/尾部，不能由 topic 存在或发送计数证明 DDS 到达。

`diagnostics.rate_metrics_enabled` 默认关闭：最终 `IMU_RUNTIME_HEALTH` 显示 `imu_published_samples=unavailable imu_publish_count_valid=no`，不把未采集的发布计数当作零。开启时该字段为实际 IMU `publish()` 成功次数，`imu_publish_count_valid=yes`；它不是 DDS 接收确认。`published_samples` 是独立的 producer 健康计数，不能替代 sink 或订阅端计数；关闭诊断不额外读取时钟或更新 metrics。

正常 SIGINT/SIGTERM 只请求 owner 退出：先停止 producer，保持接纳直到采集静止，排空 IMU 发布队列并析构节点，最后关闭 ROS context。此顺序防止正常收尾在已关闭 context 上把 `publish()` 正常返回误算为有效发送；不保证 best-effort DDS 送达。致命错误仍可提前关闭 context，必须按失败及真实接收载荷判读，不能套用正常排空保证。

## 数据语义

raw `Image` 使用 NV12。`Image.step` 保留底层 DMA buffer 的 stride；`data.size()` 使用底层 Y/UV buffer size，可能大于紧凑 `width * height * 3 / 2`。订阅端必须按 `step` 和 `data.size()` 处理对齐，不要假设紧凑布局。

compressed topic 是标准 `CompressedImage` JPEG payload。插件只在有 `/image_raw/compressed` 订阅者时执行压缩：它按 `Image.step` 和 `data.size()` 校验 NV12 布局，把有效 Y/UV 行复制到 X5 media-codec 输入 buffer，并通过 `MEDIA_CODEC_ID_JPEG` 生成 JPEG，保留原始消息的 `header`。


`header.stamp` 不是发布时刻。相机使用所选 realtime 触发估计或显式曝光中点估计。IMU/Temperature 使用输出适配层每 burst 桥值：host 为 MONOTONIC→REALTIME，tmst 为 RAW→REALTIME。`/robobaton/imu/timing` 使用 `robobaton_imu_timing_v3`，tmst 下仍保留原始 MONOTONIC 主机估计、独立 RAW burst、模式/FIFO TMST/RAW sample/不确定度、身份及正确标注的桥基点/半宽。桥边界与 tmst `200µs` 计算 admission 均不是物理精度。照实保留墙钟回拨，不强制递增、不转换仿真 `/clock`；字段和无损整数解析见[数据合同](../development/data-contracts.md#imu)。 六个独立FSYNC诊断字段与bag／CSV一致，不对相机帧或group最近邻匹配；显式关闭使用`--ros-args -p imu.fsync_diagnostics:=false`，停止/重启生效。

`CameraInfo` 只带当前帧宽高，畸变模型和标定矩阵为空。IMU orientation 不可用，消息设置 `orientation_covariance[0] = -1.0`；gyro/accel 协方差当前不伪造。`robobaton_imu_link` 只标识 IMU 消息来源；它不建立到相机、base、optical frame 或其他坐标系的变换，也不声明 TF 或外参。
