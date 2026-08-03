# 数据合同

本页记录用户可以依赖的数据格式、字段和时间语义。未公开的物理方位、坐标系、外参和硬同步能力均明确列为限制，不在文档中伪造。

## 相机图像与 RTSP

| 项目 | 合同 |
|---|---|
| `libsc132.so` / camera callback 原始帧 | 标准方向 NV12 `1280x1088` |
| RTSP 对外流 | H.264 默认；支持 H.265 |
| FOV | 水平 `148.4°`、垂直 `126.6°`、对角 `193.8°` |
| camera FPS | V1 稳定功能配置为 `25/30/40/50fps`，默认 `30fps`；`60fps` 是显式 `stress-only` 压力配置，不是稳定发布 profile |
| RTSP path | `/PRR` |
| 端口映射 | camera 0/1/2/3 -> `554/555/556/557` |

`libsc132.so` 的 callback 暴露 NV12 原始帧；RTSP 客户端接收 H.264/H.265 编码流，RTSP 不直接承载 NV12 原始帧。帧信息包含 `width`、`height`、`stride`、`vstride`、Y/UV 虚拟地址、Y/UV 物理地址和 Y/UV size。NV12 消费端不得假设 buffer 一定紧凑；应使用 `stride`、`vstride` 和 size 字段处理对齐。

## Frame Set 字段

| 字段 | 含义 |
|---|---|
| `camera_count` | 当前帧组内的相机数量，完整四目为 `4`。 |
| `group_id` | 帧组序号。 |
| `group_timestamp_ns` | 帧组时间戳，单位 `ns`。 |
| `max_skew_ns` | 当前帧组实际观测到的最大 timestamp skew，单位 `ns`。 |
| `items[i].camera_id` | 物理 camera ID，范围 `0..3`。 |
| `items[i].frame_id` | 归一化后的帧 ID。 |
| `items[i].timestamp_ns` | 单路帧时间戳，单位 `ns`。 |

`sc132_frame_set_config_t.max_skew_ns` 才是配组放行上限；默认值为 `2000000 ns`。

## Trigger 模式

| 模式 | V1 状态 | 公开合同 |
|---|---|---|
| `software_gpio` | 已验证；V1 唯一稳定模式 | 默认模式，使用 GPIO417 软件触发。 |
| `vin_lpwm` | 实验性 / 未验收 | CLI/配置仍接受该值，但不属于 V1 稳定发布合同。 |
| `none` | 实验性 / 未验收 | CLI/配置仍接受该值，但不属于 V1 稳定发布合同。 |

在 V1 已验证的 `software_gpio` 模式下，demo 对外诊断的 `camera_ts_ns` 和 RTSP PTS 会映射到启动时冻结 offset 对应的 `system_realtime` epoch。显式使用实验性的 `vin_lpwm` 或 `none` 时，时间戳保留 SC132 原生时间域，不声明为 V1 wall/realtime 合同。底层 C API 头文件中的 `timestamp_ns` 不保证与墙上时钟同域；不要把 demo 打印时间和底层原始时间域混写。

## IMU

| 项目 | 合同 |
|---|---|
| 设备路径 | `/dev/spidev2.0` |
| SPI mode/speed | mode `0`，`4 MHz` |
| DRDY | GPIO395 |
| 读取模式 | sensor timestamp FIFO |
| FIFO watermark | `1` |
| ODR | `25/50/100/200/500/1000/2000Hz` |
| 不使用 | GPIO397、FSYNC、`icm42688_pulse_fsync()` |

字段语义：

| 字段 | 单位/语义 |
|---|---|
| `sample_sequence` / demo `sample_seq` | IMU 样本序号。 |
| `temperature_c` / demo `temp_c` | 摄氏度。 |
| `accel_mps2` | `m/s^2`。 |
| `gyro_rps` | `rad/s`。 |
| `host_timestamp_ns` | GPIO395 DRDY 边沿锚点；底层为 `CLOCK_MONOTONIC_RAW` 域。 |
| `sample_timestamp_ns` | FIFO TMST 映射得到的逐 sample 时间戳；底层为 `CLOCK_MONOTONIC_RAW` 域。 |
| demo `ts_ns` | 由冻结 `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset 映射到 `system_realtime` epoch 的 sample 时间戳。 |

IMU 是独立连续采样路径。当前公开交付不提供相机/IMU 硬同步、公开 TF 外参或公开标定。

## ROS2 topics

| Topic | 消息类型 | 合同 |
|---|---|---|
| `/robobaton/cam0..3/image_raw` | `sensor_msgs/msg/Image` | 四路 raw NV12 图像，`encoding="nv12"`。 |
| `/robobaton/cam0..3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | 标准 compressed transport JPEG；当前插件使用 TurboJPEG。 |
| `/robobaton/cam0..3/camera_info` | `sensor_msgs/msg/CameraInfo` | 只包含当前帧宽高；标定字段为空。 |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42688 gyro/accel；orientation 不可用。 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42688 温度，复用 IMU sample stamp。 |

ROS2 QoS：

| 数据 | QoS |
|---|---|
| raw Image | `SensorDataQoS`，keep last 2 |
| compressed Image | 跟随 image_transport publisher 的 raw topic QoS |
| CameraInfo | Reliable + Transient Local，keep last 1 |
| IMU | `SensorDataQoS`，keep last 100 |
| Temperature | `SensorDataQoS`，keep last 10 |

ROS2 raw `Image.step` 使用底层 DMA buffer 的 stride；`data.size()` 使用底层 Y/UV buffer size，可能大于紧凑 `width * height * 3 / 2`。订阅端不得按紧凑 NV12 假设直接索引 UV 平面。

ROS2 `header.stamp` 不是发布时刻。在 V1 已验证的 `software_gpio` 模式下，节点启动时冻结 `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset，并把相机 SC132 raw timestamp 映射到 system realtime/ROS stamp。实验性的 `vin_lpwm` 和 `none` 保留底层 SC132 时间域，不声明为 V1 wall/realtime 合同。IMU `sample_timestamp_ns` 会通过同一个冻结 offset 映射到 system realtime/ROS 时间戳；IMU 不使用 `host_timestamp_ns` 作为消息时间。

ROS2 当前不发布 RTSP、TF 外参或标定；相机/IMU 硬同步仍不提供。需要通用可视化时优先订阅 `/image_raw/compressed`，不要假设 raw NV12 可被普通 RGB/BGR 工具直接显示。

## UART

| 项目 | 合同 |
|---|---|
| 默认设备 | `/dev/ttyS1` |
| 可示例切换 | `/dev/ttyS7` 或其他现场设备 |
| 默认波特率 | `115200` |
| 数据格式 | 8N1、raw、无 flow control |
| demo 模式 | `tx`、`rx`、`txrx`、`echo` |
| TX/RX 信号逻辑电平 | `3.3V` |
| V1 交付边界 | 只交付 `serial_port_demo` 软件示例；UART 硬件通信不属于 V1 已验收功能 |

现有公开板卡顶视图中，接口位于板卡上边缘；按图从左到右，`DEBUG_UART` 为 `GND/RX/TX`，`UART7` 和 `UART1` 均为 `3V3/RX/TX/GND`。图片没有标出 Pin 1；从线缆端或连接器插接面观察时不得直接照抄左右顺序。三组接口的 TX/RX 均使用 `3.3V` 逻辑电平，必须共地，禁止接入 5V TTL 或 RS-232。

`3V3` 引脚标签不代表 V1 承诺对外供电能力。3V3 方向、允许电流和热插拔能力仍待产品确认；连接 USB-UART 时只连接匹配的 3.3V TX/RX/GND 信号，不连接适配器 VCC。

## 待确认坐标/外参

| 项目 | 状态 |
|---|---|
| Camera 0/1/2/3 物理安装方向 | 待产品确认 |
| 相机坐标系轴向和手性 | 待产品确认 |
| IMU 坐标系轴向和手性 | 待产品确认 |
| `T_cam_imu` / 多相机外参 | 待产品确认 |
| 相机内参/畸变 | 待产品确认 |
