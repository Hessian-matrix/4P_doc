# 数据合同

本页记录用户可以依赖的数据格式、字段和时间语义。未公开的物理方位、坐标系、外参和硬同步能力均明确列为限制，不在文档中伪造。

## 相机图像与 RTSP

| 项目 | 合同 |
|---|---|
| `libsc132.so` / camera callback 原始帧 | NV12；native `1280x1088` 或 VSE 缩放 `640x480`/`720x480`/`1280x720`；旋转 `0/180` 宽高不变，`90/270` 宽高交换 |
| RTSP 对外流 | H.264 默认；支持 H.265 |
| FOV | V1 A/B 相机曾标称水平 `148.4°`/`115.6°`、垂直 `126.6°`/`96.8°`、对角 `193.8°`/`157.2°`；V2 镜头/子板及 FOV 待核实。 |
| camera FPS | 默认`30fps`，支持`25fps`、`30fps`、`40fps`、`50fps`和`60fps`；其他值在启动副作用前拒绝 |
| RTSP path | `/PRR` |
| 端口映射 | 软件 cam0/cam1/cam2/cam3 -> `554/555/556/557`；V2 物理接口对应关系待核实。 |

`libsc132.so` callback 暴露 NV12 原始帧，RTSP 客户端接收 H.264/H.265 编码流。帧信息包含 `width`、`height`、`stride`、`vstride`、Y/UV 虚拟/物理地址及 size。旋转 `90/270` 会交换宽高；消费端须依每帧元数据与 stride/size 处理对齐，不要假设紧凑 `1280x1088`。V1 A/B FOV 不可直接套用 V2 子板。

## Frame Set 字段

| 字段 | 含义 |
|---|---|
| `camera_count` | 当前帧组内的相机数量，完整四目为 `4`。 |
| `group_id` | 帧组序号。 |
| `group_timestamp_ns` | 帧组时间戳，单位 `ns`。 |
| `max_skew_ns` | 当前帧组实际观测到的最大 timestamp skew，单位 `ns`。 |
| `items[i].camera_id` | 软件 camera ID，范围 `0..3`；V2 物理接口到软件 ID 的对应关系待实板核对，不沿用 V1 丝印映射。 |
| `items[i].frame_id` | 归一化后的帧 ID。 |
| `items[i].timestamp_ns` | 单路帧时间戳，单位 `ns`。 |

`sc132_frame_set_config_t.max_skew_ns` 才是配组放行上限；默认值为 `10000000 ns（10ms）`，用于覆盖四路曝光时间差。

## Trigger 模式

| 模式 | 当前状态 | 公开合同 |
|---|---|---|
| `vin_lpwm` | 默认 VIN 硬件触发 | 走 VIN 硬件 `lpwm_attr` 输出，绕开 FSYNC 软件 GPIO 路径。 |
| `none` | 显式 free-run 诊断 | 不保证四路硬触发。 |

`software_gpio`（仅主仓内部调试，不对外公开）模式下，demo 对外诊断的 `camera_ts_ns` 和 RTSP PTS 经启动时冻结的 offset 映射至 `system_realtime` epoch；`none` 诊断模式保留 SC132 原生时间域。底层 C API 的 `timestamp_ns` 不保证与墙上时钟同域。V1 对此时间语义的验收不能代替 V2 实板验收。

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
| demo `ts_ns` | 由冻结 `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset 映射到 `system_realtime` epoch 的 sample 时间戳。 |
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

ROS2 `header.stamp` 不是发布时刻。节点在 `software_gpio` 模式冻结 `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset，把相机 SC132 raw timestamp 与 IMU `sample_timestamp_ns` 映射到 system realtime/ROS stamp；显式 `none` 诊断模式保留 SC132 原生时间域。IMU 不以 `host_timestamp_ns` 为消息时间；V1 时间验收不能证明 V2 相机与 IMU 对齐。

ROS2 当前不发布 RTSP、TF 外参或标定；相机/IMU 硬同步仍不提供。需要通用可视化时优先订阅 `/image_raw/compressed`，不要假设 raw NV12 可被普通 RGB/BGR 工具直接显示。

## UART

| 项目 | 合同 |
|---|---|
| 默认设备 | `/dev/ttyS1` |
| 可示例切换 | `/dev/ttyS7` 或其他现场设备 |
| 波特率 | `serial_port_demo` 默认 `115200`；V2 DEBUG_UART 控制台参数待确认。 |
| serial_port_demo 数据格式 | 8N1、raw、无 flow control |
| demo 模式 | `tx`、`rx`、`txrx`、`echo` |
| UART1/UART7 TX/RX 信号逻辑电平 | V2 实际 GPIO_VREF/BOM 和接口电平待确认；不得沿用 V1 `3.3V` 作为接线依据。 |
| UART1/UART7 供电脚 | V2 CN2/CN3 的供电用途、电平、额定负载和热插拔边界待确认，勿引用 V1 合计 `500 mA` 限制。 |
| V1 历史边界 | UART1/UART7 在 V1 板上曾验收；不构成 V2 电气或线束兼容证明。 |

V2 UART1/UART7 对应 CN2/CN3 5P 接口；新增信号不能当作 RTS/CTS 或 PPS 接线。`serial_port_demo` 的软件默认设备是 `/dev/ttyS1`，可示例切换 `/dev/ttyS7`，但 V2 物理线序、tty 映射、TX/RX 电平和供电方向仍待现场确认。PPS 脚本的 V1 `/dev/pps2` 复用说明不构成 V2 已支持 PPS 的承诺。DEBUG_UART 非用户 UART；在核实 V2 电平前不接入外部适配器。默认断电接线，先确认板端 TX/RX/GND 和对端电平，禁止误接或反灌。参见[硬件连接与安全](../getting-started/hardware-and-safety.md#uart)。
