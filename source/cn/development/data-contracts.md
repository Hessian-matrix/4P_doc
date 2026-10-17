# 数据合同

本页记录用户可以依赖的数据格式、字段和时间语义。未公开的物理方位、坐标系、外参和硬同步能力均明确列为限制，不在文档中伪造。

## 相机图像与 RTSP

| 项目 | 合同 |
|---|---|
| `libsc132.so` / camera callback 原始帧 | NV12；native `1280x1088` 或 VSE 缩放 `640x480`/`720x480`/`1280x720`；旋转 `0/180` 宽高不变，`90/270` 宽高交换 |
| RTSP 对外流 | H.264 默认；支持 H.265 |
| FOV | 相机 A/B 保持水平 `148.4°`/`115.6°`、垂直 `126.6°`/`96.8°`、对角 `193.8°`/`157.2°`。 |
| camera FPS | 默认`30fps`，支持`25fps`、`30fps`、`40fps`、`50fps`和`60fps`；其他值在启动副作用前拒绝 |
| RTSP path | `/PRR` |
| 端口映射 | CAM1..CAM4 依次对应软件 cam0..cam3 与 `554/555/556/557`，物理映射与 V1 不变。 |

`libsc132.so` callback 暴露 NV12 原始帧，RTSP 客户端接收 H.264/H.265 编码流。帧信息包含 `width`、`height`、`stride`、`vstride`、Y/UV 虚拟/物理地址及 size。旋转 `90/270` 会交换宽高；消费端须依每帧元数据与 stride/size 处理对齐，不要假设紧凑 `1280x1088`。

## Frame Set 字段

| 字段 | 含义 |
|---|---|
| `camera_count` | 当前帧组内的相机数量，完整四目为 `4`。 |
| `group_id` | 帧组序号。 |
| `group_timestamp_ns` | 帧组时间戳，单位 `ns`。 |
| `max_skew_ns` | 当前帧组实际观测到的最大 timestamp skew，单位 `ns`。 |
| `items[i].camera_id` | 软件 ID `0..3`，依次对应物理 CAM1..CAM4，与 V1 不变。 |
| `items[i].frame_id` | 归一化后的帧 ID。 |
| `items[i].timestamp_ns` | 单路帧时间戳，单位 `ns`。 |

`sc132_frame_set_config_t.max_skew_ns` 才是配组放行上限；默认值为 `10000000 ns（10ms）`，限制触发捕获值差异，不代表曝光对齐精度。

## Trigger 模式

| 模式 | 当前状态 | 公开合同 |
|---|---|---|
| `vin_lpwm` | 所有相机应用及底层库唯一支持的 VIN 硬件触发 | 相机与 IMU FSYNC 共用 LPWM IO；相机 `timestamp_ns` 来自随帧传播的 `trig_tv` 硬件捕获，缺失则停止采集，不回退到到帧时间。 |

LPWM `timestamp_ns` 是 SIF 硬件计数器时间，`trig_tv` 微秒值换算为 ns；不是 `CLOCK_MONOTONIC_RAW`、UTC 或曝光中心时刻。帧组时间取各路捕获值的最小值，各路保留独立捕获值；`max_skew_ns` 表示捕获值差异，不代表曝光或相机/IMU 对齐精度。non-ROS 相机诊断、RTSP PTS、保存图像时间和 ROS2 图像 `header.stamp` 保留该原生时间域。IMU FIFO TMST 映射至 RAW 后由 consumer 原样保留，不再转换至 realtime。相机 SIF→RAW 映射尚未实现，不能直接与 IMU 时间戳相减；共线 FSYNC 尚无公开样本关联接口。

## IMU

| 项目 | 合同 |
|---|---|
| 设备路径 | `/dev/spidev2.0` |
| SPI mode/speed | mode `0`，`4 MHz` |
| INT1 DRDY | `34120000.gpio` offset `8`；不用旧 GPIO395 |
| 读取模式 | sensor timestamp FIFO |
| FIFO watermark | `1` |
| 原生 ODR | `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；旧 `500/1000/2000Hz` 配置明确拒绝，不重采样 |
| FSYNC | V2 输入与相机公共触发网相连；IMU 不驱动该网，不声明样本/曝光对齐。 |

字段语义：

| 字段 | 单位/语义 |
|---|---|
| `sample_sequence` / demo `sample_seq` | IMU 样本序号。 |
| `temperature_c` / demo `temp_c` | 摄氏度。 |
| `accel_mps2` | `m/s^2`。 |
| `gyro_rps` | `rad/s`。 |
| `host_timestamp_ns` | 配对 INT1 边沿的主机 `CLOCK_MONOTONIC_RAW` 纳秒时间戳；不是样本时间戳。 |
| `sample_timestamp_ns` | FIFO TMST 映射得到的逐 sample 时间戳；底层为 `CLOCK_MONOTONIC_RAW` 域。 |
| demo `ts_ns` | 直接保留 `CLOCK_MONOTONIC_RAW` 域的 sample 时间戳，单位 ns；不加 realtime offset。`host_ts_ns` 同样保留 RAW 域。 |
| `reserved0` | 当前会话观测到的 FIFO timestamp 低 16 位回绕次数；不表示 V1 20 位 SPI 快照回绕。 |
| `timestamp_uncertainty_us` | 逐样本时间映射的不确定度，单位 us。 |
| `gpio_event_gap_count` / `fifo_overflow_count` / `mapper_failure_count` | 当前会话的边沿缺口、FIFO 溢出与时间映射失败累计计数。 |

IMU 独立连续采样；V2 FSYNC 输入虽与相机触发共网，但当前公开接口不提供相机/IMU 同步样本对应关系、曝光时刻、TF 外参或标定。逐样本时间域以公开头文件为准，不能把主机 INT1 时间或 FSYNC delta 冒充样本时间。

`accel_mps2` 按 `[X, Y, Z]` 输出；V2 PCB 的安装方向与加速度符号尚待实板六面/旋转验证，不沿用 V1 顶视图的 `[0, 0, -9.8]` 和左右前后轴向结论。

## non-ROS 保存输出

| 输出 | 合同 |
|---|---|
| ROS bag | `sensor_demo --record-bag <absolute .bag>` 保存四路 JPEG 图像、相机参数和 IMU 数据；不完整压力/异常运行使用显式 `.partial.bag` recovery 文件。 |
| MP4 session | `sensor_demo --record-mp4-dir <absolute directory>` 保存四路 H.264 MP4、四路 timestamp CSV、`imu.csv`、`camera_params.yaml`、`session_status.json` 和 `publication_receipt.json`。 |
| MP4 路径冲突 | 配置的 final 目录或同名 `.partial` 已存在时，实际输出自动切到同级 `<name>-YYYYMMDDTHHMMSSZ[-NNNN]`；以 `SENSOR_MP4_RESULT path=` 为准。 |
| `.partial` | 保留 recovery namespace；`.partial` MP4 session 可提取排查，但不声明为 complete。 |

MP4 模式只支持 H.264 和完整四路 camera mask `0x0f`，不能与 bag 保存或 frame-skip 同时启用。MP4 文件的帧时序是容器名义 timing；精确纳秒相机时间戳以同 session 的 `cameraN_timestamps.csv` 为准，按 `frame_index` 与 MP4 metadata 对齐。`published_complete` 源必须带有匹配的 `publication_receipt.json`，并且四路 MP4/index inventory 完整。

bag 消息的 payload 与记录时刻分开：图像及首帧 CameraInfo 的 `header.stamp` 保留相机捕获值；IMU payload 保留 RAW sample stamp。bag record time 来自独立的 `CLOCK_MONOTONIC_RAW` 到达/写入时钟，按写入次序不递减，不把两个传感器 epoch 做数值比较。session config 声明 `camera_timestamp_domain="sc132_native"`、`imu_timestamp_domain="monotonic_raw"`、`record_timestamp_domain="monotonic_raw"`。

## ROS2 topics

| Topic | 消息类型 | 合同 |
|---|---|---|
| `/robobaton/cam0..3/image_raw` | `sensor_msgs/msg/Image` | 四路 raw NV12 图像，`encoding="nv12"`。 |
| `/robobaton/cam0..3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | 标准 compressed transport JPEG；当前插件使用 X5 media codec 硬件 JPEG 编码。 |
| `/robobaton/cam0..3/camera_info` | `sensor_msgs/msg/CameraInfo` | 只包含当前帧宽高；标定字段为空。 |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42670-P gyro/accel；orientation 不可用。 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42670-P 温度，复用 IMU sample stamp。 |

ROS2 QoS：

| 数据 | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | 跟随 raw publisher，同为 Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
| IMU | `SensorDataQoS`，keep last 100 |
| Temperature | `SensorDataQoS`，keep last 10 |

ROS2 raw `Image.step` 使用底层 DMA buffer 的 stride；`data.size()` 使用底层 Y/UV buffer size，可能大于紧凑 `width * height * 3 / 2`。订阅端不得按紧凑 NV12 假设直接索引 UV 平面。

ROS2 `header.stamp` 不是发布时刻：LPWM 相机保留 SIF 触发捕获时间域；IMU 直接保留 RAW 域的 `sample_timestamp_ns`，不以 `host_timestamp_ns` 为消息时间。两者尚不同域，不能直接做 ROS 时间同步配对；也不能与节点 `now()`、Unix 时间或仿真 `/clock` 相减。RAW 是本机本次启动的时钟，不是跨设备或跨重启 epoch。PTP 不会自动转换 SIF/RAW 计数器或建立 FSYNC 样本关联。

ROS2 当前不发布 RTSP、TF 外参或标定；相机/IMU 硬同步仍不提供。需要通用可视化时优先订阅 `/image_raw/compressed`，不要假设 raw NV12 可被普通 RGB/BGR 工具直接显示。

## UART

| 项目 | 合同 |
|---|---|
| 默认设备 | `/dev/ttyS1` |
| 可示例切换 | `/dev/ttyS7` 或其他现场设备 |
| 波特率 | `serial_port_demo` 默认 `115200`；DEBUG_UART `921600`。 |
| serial_port_demo 数据格式 | 8N1、raw、无 flow control |
| demo 模式 | `tx`、`rx`、`txrx`、`echo` |
| UART1/UART7 TX/RX 信号逻辑电平 | 保持 `3.3V`；DEBUG_UART 为 `1.8V`。 |
| UART1/UART7 供电脚 | V2 CN2/CN3 的供电用途、电平、额定负载和热插拔边界待确认，勿引用 V1 合计 `500 mA` 限制。 |
| V1 历史边界 | UART1/UART7 在 V1 板上曾验收；不构成 V2 电气或线束兼容证明。 |

V2 UART1/UART7 对应 CN2/CN3 5pin 接口与 `/dev/ttyS1`、`/dev/ttyS7`。CN3 有独立 IO 默认作为 PPS 输入，不需要复用或切换 RX/TX；PPS 设备节点按系统枚举识别。完整线序及供电脚用途以正式 V2 标识为准。DEBUG_UART 非用户串口；默认断电接线，核实 TX/RX/GND、对端电平及共地，不接适配器 VCC，不反灌。见[硬件连接与安全](../getting-started/hardware-and-safety.md#uart)。
