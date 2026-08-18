# 数据合同

本页记录用户可以依赖的数据格式、字段和时间语义。未公开的物理方位、坐标系、外参和硬同步能力均明确列为限制，不在文档中伪造。

## 相机图像与 RTSP

| 项目 | 合同 |
|---|---|
| `libsc132.so` / camera callback 原始帧 | 标准方向 NV12 `1280x1088` |
| RTSP 对外流 | H.264 默认；支持 H.265 |
| FOV | 水平 `148.4°`、垂直 `126.6°`、对角 `193.8°` |
| camera FPS | 默认`30fps`，`25/30/40/50/60fps`均为受支持配置；60fps的stress-only标签仅属于ROS1 bag全量JPEG保存，H.264 MP4为稳定发布矩阵 |
| RTSP path | `/PRR` |
| 端口映射 | CAM1/CAM2/CAM3/CAM4 -> cam0/cam1/cam2/cam3 -> `554/555/556/557` |

`libsc132.so` 的 callback 暴露 NV12 原始帧；RTSP 客户端接收 H.264/H.265 编码流，RTSP 不直接承载 NV12 原始帧。帧信息包含 `width`、`height`、`stride`、`vstride`、Y/UV 虚拟地址、Y/UV 物理地址和 Y/UV size。NV12 消费端不得假设 buffer 一定紧凑；应使用 `stride`、`vstride` 和 size 字段处理对齐。

## Frame Set 字段

| 字段 | 含义 |
|---|---|
| `camera_count` | 当前帧组内的相机数量，完整四目为 `4`。 |
| `group_id` | 帧组序号。 |
| `group_timestamp_ns` | 帧组时间戳，单位 `ns`。 |
| `max_skew_ns` | 当前帧组实际观测到的最大 timestamp skew，单位 `ns`。 |
| `items[i].camera_id` | 软件 camera ID，范围 `0..3`；物理丝印映射为 CAM1 -> cam0、CAM2 -> cam1、CAM3 -> cam2、CAM4 -> cam3。 |
| `items[i].frame_id` | 归一化后的帧 ID。 |
| `items[i].timestamp_ns` | 单路帧时间戳，单位 `ns`。 |

`sc132_frame_set_config_t.max_skew_ns` 才是配组放行上限；默认值为 `2000000 ns`。

## Trigger 模式

| 模式 | V1 状态 | 公开合同 |
|---|---|---|
| `software_gpio` | 已验证；V1 唯一稳定模式 | 默认模式，使用 GPIO417 软件触发。 |
| `vin_lpwm` | 实验性，不属于 V1 稳定配置。 | CLI/配置仍接受该值，但不属于 V1 稳定发布合同。 |
| `none` | 实验性，不属于 V1 稳定配置。 | CLI/配置仍接受该值，但不属于 V1 稳定发布合同。 |

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

IMU 加速度 `accel_mps2` 按 `[X, Y, Z]` 顺序输出，符号以 [硬件连接与安全](hardware-and-safety.md#uart) 中当前板卡顶视图为物理参考：设备静止且水平放置时，`accel_mps2` 约为 `[0, 0, -9.8] m/s^2`；向图片左侧加速时 X 为负；向图片顶部/产品前方加速时 Y 为负。该说明不定义 IMU 到相机、base、optical frame 或其他坐标系的关系，也不提供 TF 或外参。

## non-ROS 保存输出

| 输出 | 合同 |
|---|---|
| ROS bag | `sensor_demo --record-bag <absolute .bag>` 保存四路 JPEG 图像、相机参数和 IMU 数据；不完整压力/异常运行使用显式 `.partial.bag` recovery 文件。 |
| MP4 session | `sensor_demo --record-mp4-dir <absolute directory>` 保存四路 H.264 MP4、四路 timestamp CSV、`imu.csv`、`camera_params.yaml`、`session_status.json` 和 `publication_receipt.json`。 |
| MP4 路径冲突 | 配置的 final 目录或同名 `.partial` 已存在时，实际输出自动切到同级 `<name>-YYYYMMDDTHHMMSSZ[-NNNN]`；以 `SENSOR_MP4_RESULT path=` 为准。 |
| `.partial` | 保留 recovery namespace；`.partial` MP4 session 可提取排查，但不声明为 complete。 |

MP4 模式只支持 H.264 和完整四路 camera mask `0x0f`，不能与 bag 保存或 frame-skip 同时启用。MP4 文件的帧时序是容器名义 timing；精确纳秒相机时间戳以同 session 的 `cameraN_timestamps.csv` 为准，按 `frame_index` 与 MP4 metadata 对齐。`published_complete` 源必须带有匹配的 `publication_receipt.json`，并且四路 MP4/index inventory 完整。

## ROS2 topics

| Topic | 消息类型 | 合同 |
|---|---|---|
| `/robobaton/cam0..3/image_raw` | `sensor_msgs/msg/Image` | 四路 raw NV12 图像，`encoding="nv12"`。 |
| `/robobaton/cam0..3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | 标准 compressed transport JPEG；当前插件使用 X5 media codec 硬件 JPEG 编码。 |
| `/robobaton/cam0..3/camera_info` | `sensor_msgs/msg/CameraInfo` | 只包含当前帧宽高；标定字段为空。 |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42688 gyro/accel；orientation 不可用。 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42688 温度，复用 IMU sample stamp。 |

ROS2 QoS：

| 数据 | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | 跟随 raw publisher，同为 Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
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
| UART1/UART7 TX/RX 信号逻辑电平 | `3.3V` |
| UART1/UART7 3.3V 供电脚 | 两个供电脚共享 `VCC3V3_SYS`；V1 对外设供电额定边界为合计 `500 mA` |
| V1 交付边界 | UART1/UART7 3.3V 硬件通信已通过 V1 验收；`serial_port_demo` 是公开用户示例 |

UART1/UART7 为 `3.3V` 用户可编程 UART，分别对应 `/dev/ttyS1` 和 `/dev/ttyS7`，连接器为 GH1.25-4P；`serial_port_demo` 只适用于 UART1/UART7。DEBUG_UART 是 `1.8V` 系统调试 UART，连接器为 GH1.25-3P，不支持 `serial_port_demo`。接口位置、电平和供电边界见 [硬件连接与安全](hardware-and-safety.md#uart)。

连接时板端 TX 接适配器 RX，板端 RX 接适配器 TX，并始终共地。禁止把 `3.3V` 或 `5V` 逻辑接到 DEBUG_UART。连接通用 USB-UART 到 UART1/UART7 时，默认只连接匹配的 `3.3V` TX/RX/GND 信号，并断开适配器 VCC。若 UART1/UART7 外设总电流超过合计 `500 mA`，必须使用独立电源；独立电源需与板端共地，且不得反向灌入板端 3.3V 电源轨。
