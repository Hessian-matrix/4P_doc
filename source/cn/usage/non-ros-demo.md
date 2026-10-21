# non-ROS Demo 使用

[`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo) 是面向用户的 V2 non-ROS 公开源码仓库，提供四目 SC132 RTSP、四路拼接 RTSP、ICM-42670-P IMU、UART 和 SocketCAN CAN 示例。旧 V1 下载包的硬件/API 不适用于 V2。

## 1. 目录和运行包

常用入口：

```text
<non-ros-demo-root>/
├── demo/                    # 可直接部署到 X5 /root/demo 的运行包
│   ├── cam_demo
│   ├── sensor_demo
│   ├── mosaic_rtsp_demo
│   ├── imu_reader_demo
│   ├── serial_port_demo
│   ├── can_demo
│   ├── start_sensor_demo.sh     # sensor_demo 开机自启动管理脚本
│   ├── env.sh
│   ├── config/sensor_config.yaml
│   ├── bin/
│   └── lib/
├── config/sensor_config.yaml
├── include/
├── lib/
├── scripts/
└── src/
```

部署时完整复制 `demo/` 目录内容。顶层 `cam_demo`、`sensor_demo`、`mosaic_rtsp_demo`、`imu_reader_demo`、`serial_port_demo` 和 `can_demo` 是启动脚本，会设置运行所需的 `LD_LIBRARY_PATH`；真实 ELF 位于 `bin/`。

## 2. 运行联合入口 `sensor_demo`

`sensor_demo` 同时运行：

- 四路 SC132 相机；
- PRRTSP v2 H.264/H.265 RTSP 推流；
- ICM-42670-P INT1（`34120000.gpio` offset `8`）+ sensor timestamp FIFO IMU 采集线程。

```bash
cd /root/demo
./sensor_demo
```

常用覆盖：

```bash
./sensor_demo --sample-rate-hz 1600
./sensor_demo --print-rate-hz 50 --print-metrics
./sensor_demo --diagnostics
```

退出时会输出 IMU 摘要：

```text
SENSOR_IMU_RESULT samples=... invalid=... timestamp_duplicates=... timestamp_regressions=... effective_hz=...
```
未发生系统校时的窗口应检查 `timestamp_duplicates=0`、`timestamp_regressions=0`；对外 realtime stamp 允许随系统校时回拨，不能把跨校时窗口的回退单独当作硬件时序错误。还须检查序号、timing drop、最终健康计数和实际载荷。

`--imu-sample-drop-policy allow-counted` 为默认策略：身份可证明但 timing 预算不满足的样本计数丢弃，继续采集；`strict` 遇 timing/无效包拒绝即失败。身份无法唯一证明、时钟证书失效或硬件错误在两种策略下都停止。`--imu-start-order camera-first|imu-first` 控制启动顺序，默认 `camera-first`，不改变时间戳或关联合同。

(non-ros-yaml)=
## 3. YAML 配置

`sensor_demo` 启动时读取 `${DEMO_DIR:-当前目录}/config/sensor_config.yaml`。命令行参数优先于 YAML。

默认配置结构：

```yaml
camera:
  # width/height: 1280x1088（默认）、640x480、720x480 或 1280x720，任一轴向
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
  test_exposure_midpoint: false
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 800
  print_rate_hz: 10
  print_metrics: false
  fsync_enabled: false
save_data:
  save: false
  format: mp4
  save_path: /root/demo/save_mp4/
  skip: false
```

边界：

- `camera.width` / `camera.height` 支持 `1280x1088`（默认）、`640x480`、`720x480`、`1280x720`，两种轴向写法均合法，其余值在启动相机前拒绝。
- 完整四目路径固定为四路；单颗 sensor 诊断使用 `cam_demo --camera-id`。
- non-ROS公开帧率集合为25/30/40/50/60fps；默认`30`，其他值在启动相机前拒绝。
- `camera.test_exposure_midpoint` 默认 `false`；改为 `true` 并重启 `sensor_demo`，图像时间戳使用“触发时间＋半曝光时长”的估算曝光中点。显式 YAML 值优先于 `SC132_TEST_EXPOSURE_MIDPOINT`；旧配置省略此字段时沿用环境变量（未设置则关闭）。需要同时重建应用和支持该开关的 `libsc132.so`；不影响 IMU 时间戳或 bag record time。ROS1 bag 对齐读取图像 `header.stamp`，不要再加半曝光。曝光不可用时停止采集，不宣称已校准的真实曝光中点，详见 {ref}`数据合同 <test-exposure-midpoint>`。
- `rtsp.codec` 支持 `h264` 和 `h265`。
- IMU 原生采样率支持 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；旧 `500/1000/2000Hz` 明确拒绝，不会重采样。
- `save_data.format` 默认是 `mp4`，同时支持 `rosbag`；保存路径必须是绝对路径。

(non-ros-save)=

## 4. 保存四路图像与 IMU

完整的整包校验、ROS1 bag/MP4互斥配置、优雅退出、结果验收、离线转换和恢复流程见 [保存数据](save-data-guide.md)。

ROS bag 保存适合保留 JPEG 图像帧、相机参数和 IMU 数据：

```bash
cd /root/demo
./sensor_demo --record-bag /root/save_demo/record.bag
```

MP4 保存复用 RTSP 已编码的 H.264 访问单元，适合长时间保存四路视频和 IMU CSV：

```bash
cd /root/demo
./sensor_demo --record-mp4-dir /root/save_demo/mp4_session
```

MP4 模式要求 `rtsp.codec: h264`、完整四路 camera mask `0x0f`，且不能同时启用 `--record-bag` 或 `record-frame-skip`。配置的 final 输出目录不得以 `.partial` 结尾；如果目标目录或同名 `.partial` 已存在，程序会自动写入同级 `<目录名>-YYYYMMDDTHHMMSSZ[-NNNN]`，退出摘要 `SENSOR_MP4_RESULT path=` 给出真实目录。

当前 MP4 session 包含 `camera0.mp4`～`camera3.mp4`、四路 `cameraN_timestamps.csv`、`imu.csv`、`exposure.jsonl`、`fsync.jsonl`、`camera_params.yaml`、`session_status.json` 和 `publication_receipt.json`。`fsync.jsonl` 始终创建，仅启用 FSYNC 后写入关联记录。MP4 使用名义 H.264 帧时间；timestamp CSV 保存微秒量化、以 ns 表示的 realtime 组触发时间，逐路原始值可见输入曝光 sidecar，开启 FSYNC 后也在关联记录中。曝光 `status=1` 是估计，不能当实际生效曝光；输入 sidecar 可能多于已编码帧。关联方式见[数据合同](../development/data-contracts.md)。`.partial` 仅用于恢复，不能当完整数据源。

离线转换 JPEG 数据集时，在开发机使用公开 demo 仓中的脚本：

```bash
python3 scripts/rosbag_extract.py /root/save_demo/record.bag /data/record_dataset
python3 scripts/mp4_extract.py /root/save_demo/mp4_session /data/mp4_dataset
```

| `imu.sample_rate_hz` | `800` | `25/50/100/200/400/800/1600`；旧档位拒绝。 |

## 5. 单独运行相机 RTSP

```bash
cd /root/demo
pgrep -a cam-service
./cam_demo
```

默认行为：四路、`1280x1088`、`30fps`、H.264、RTSP path `/PRR`。

常用参数：

```text
--fps <25|30|40|50|60>
--codec <h264|h265>
--rotate <0|90|180|270>
--bps <kbps>
--url <path>
--trigger-mode vin_lpwm
--diagnostics
--max-skew-ns <ns>
--frame-timeout-ms <ms>
```

Trigger 模式状态：

| 模式 | 当前状态 |
|---|---|
| `vin_lpwm` | 唯一支持的模式，VIN LPWM 硬件触发；其他值拒绝。 |

限制：`--width/--height` 接受 `1280x1088`（默认）、`640x480`、`720x480`、`1280x720`，两种轴向写法均合法，其余组合拒绝；缩放由 `libsc132` VSE 硬件整幅拉伸完成，不改变 FOV。`--rotate 180`只支持`30fps`，不支持`25fps`、`40fps`、`50fps`和`60fps`。对外 NV12/RTSP 画布在旋转 `0/180` 时宽高不变（如 `1280x1088`、`640x480`），旋转 `90/270` 时宽高交换（如 `1088x1280`、`480x640`）。相机、RTSP、ROS1 bag和H.264 MP4使用同一`25/30/40/50/60fps`公开帧率集合。

默认四路 RTSP：

```text
CAM1 / cam0 -> rtsp://192.168.1.12:554/PRR
CAM2 / cam1 -> rtsp://192.168.1.12:555/PRR
CAM3 / cam2 -> rtsp://192.168.1.12:556/PRR
CAM4 / cam3 -> rtsp://192.168.1.12:557/PRR
```

其中 CAM1/CAM2/CAM3/CAM4 是板上物理丝印，cam0/cam1/cam2/cam3 是软件相机 ID。
以上使用出厂默认 IP；板卡地址已修改时替换 URL 中的地址。

单颗 sensor 诊断：

```bash
./cam_demo --camera-id 0 --diagnostics
./cam_demo --camera-id 1 --diagnostics
./cam_demo --camera-id 2 --diagnostics
./cam_demo --camera-id 3 --diagnostics
```

每次只运行一个 `cam_demo`。该模式用于排查单颗 sensor、FPC、供电、I2C 和 MIPI/VIN 链路，不代表 2 路或 3 路组合能力。

`cam-service` 是相机运行依赖，保持其运行。切换 `sensor_demo`、`cam_demo` 或用户自研相机应用前，先正常退出旧相机应用，避免 camera/VIO/编码资源冲突。

(non-ros-mosaic)=

## 6. 四路拼接 RTSP（mosaic_rtsp_demo）

`mosaic_rtsp_demo` 把四路 SC132 `1280x1088` NV12 frame-set 在 CPU 内合成为一张 `2560x2176` 的 hbmem NV12 DMA 输出缓冲，并通过 `libprrtsp.so` 的 external NV12 输入输出固定 H.264 RTSP，避免 PRRTSP 再复制整帧。

```bash
cd /root/demo
./mosaic_rtsp_demo
./mosaic_rtsp_demo --fps 40
./mosaic_rtsp_demo --fps 50
```

固定 RTSP 地址：

```text
rtsp://<x5-ip>:558/PRR
```

该程序为固定形态，不提供相机分辨率、码率、编码或 RTSP 端口/路径配置：

- 固定四路、H.264、8000kbps、正装方向，输出 `2560x2176`，RTSP 端口 `558`、path `/PRR`。
- `--fps` 支持 `25|30|40|50|60`，默认 `30`。

退出时输出运行统计：

```text
queue_full_drop=... invalid_group=... copy_failure=... send_failure=...
retain_release_balance=... copy_duration_avg_ms=... send_duration_avg_ms=...
```

- `retain_release_balance=0` 表示跨线程保留的 SC132 frame 已全部归还，无帧泄漏。
- `queue_full_drop`、`invalid_group`、`copy_failure`、`send_failure` 为 `0` 表示运行期间无队列丢弃、无无效帧组、无合成或发送失败。
- `copy_duration_avg_ms`、`send_duration_avg_ms` 为合成与 RTSP 发送的帧耗时均值，用于判断档位余量。

与 `cam_demo`/`sensor_demo` 一样，`mosaic_rtsp_demo` 独占四路相机资源，运行前先退出其他相机应用，并保持 `cam-service` 运行。

## 7. 单独运行 IMU


```bash
cd /root/demo
./imu_reader_demo
./imu_reader_demo --sample-rate-hz 1600 --count 10000
```

默认按 `10Hz` 打印抽样记录；程序仍消费全部 IMU 样本。需要看指标时使用：

```bash
./imu_reader_demo --print-metrics
```

关键字段：

- `ts_ns`：`CLOCK_REALTIME` 域的 IMU sample 时间戳，单位 `ns`，由 producer 的 FIFO TMST→RAW→realtime 映射提供；`host_ts_ns` 为同域 INT1 边沿。`TIME_BASE domain=realtime realtime_start_ns=...` 仅声明启动时系统参考，不会冻结 offset；运行中校时可使后续时间戳回拨。
- `accel_mps2`：加速度，单位 `m/s^2`。
- `gyro_rps`：角速度，单位 `rad/s`。
- `uncertainty_us`、`gpio_gap_count`、`fifo_overflow_count`、`mapper_failure_count`：时间戳映射和采集链路诊断。

V2 `accel_mps2` 按 `[X, Y, Z]` 输出；PCB 安装方向和符号尚待实板六面/旋转验证，不以 V1 顶视图推断正负轴或相机坐标变换。

IMU INT1 使用 `34120000.gpio` offset `8`，FIFO TMST 为逐样本时间；相机使用 LPWM，输出时间来自 VIN 随帧传播的触发捕获，不是到帧时间。相机和 IMU FSYNC 共用同一物理 IO；这不自动提供 FIFO 样本与曝光的一一对应。

显式关联使用 `sensor_demo --fsync --sample-rate-hz 1600` 或 YAML `imu.fsync_enabled: true`（默认关闭，仅支持 `800/1600Hz`）。不保存时 stdout 输出 `robobaton_fsync_v1` JSON；保存时进入 bag `/robobaton/fsync` 或 MP4 `fsync.jsonl`。仅 `status=1` 表示唯一匹配；检查 timing drop、序号缺口和 `SENSOR_FSYNC_RESULT`，不把样本对应误称为曝光同步，详见[数据合同](../development/data-contracts.md)。

运行需要实时调度权限：相机捕获 `SCHED_FIFO/60`、IMU owner `SCHED_FIFO/20`、INT1 observer `SCHED_FIFO/30`，联合应用 IMU consumer `SCHED_RR/3`；两个 observer 继承允许 CPU 集合，每轮休眠 `50µs`。调度设置失败拒绝启动。应用不自动修改 IRQ/debug 或实时配额，高负载可能显式丢样或失败；保存及关联验收还须读取成功 stop 后的 `IMU_RUNTIME_HEALTH final=yes health_valid=yes`，不只观察仍有终端输出。

## 8. 串口 Demo


UART1/UART7 逻辑电平保持 `3.3V`，设备节点为 `/dev/ttyS1`、`/dev/ttyS7`；DEBUG_UART 为 `1.8V`，不适用于 `serial_port_demo`。V2 CN2/CN3 为 5pin；CN3 的独立 IO 默认作为 PPS 输入，无需切换 UART7 RX/TX。完整线序和供电脚额定值以正式 V2 资料为准，断电接线，不继承 V1 `500 mA` 或热插拔承诺；见[硬件连接与安全](../getting-started/hardware-and-safety.md#uart)。

```bash
cd /root/demo
./serial_port_demo
```

默认配置是 `/dev/ttyS1`、`115200`、`txrx`。常用示例：

```bash
./serial_port_demo --port /dev/ttyS1 --mode tx --baud 115200 --text "hello-x5"
./serial_port_demo --port /dev/ttyS7 --mode rx --baud 115200
./serial_port_demo --port /dev/ttyS1 --mode txrx --baud 115200 --count 10 --text "ping"
./serial_port_demo --port /dev/ttyS7 --mode echo --baud 115200
```

## 9. 验证建议


- 相机：用 `ffprobe` 或播放器拉取四路 RTSP，并确认 codec、分辨率和帧率。
- IMU：观察 `SENSOR_IMU_RESULT` 和 `timestamp_duplicates` / `timestamp_regressions`。
- 动态库：始终整包部署，避免混用其他工程或系统目录中的同名 `.so`。
- 进程占用：不要同时运行多个相机应用；切换模式前先退出前一个进程。

(non-ros-autostart)=

## 10. 开机自启动

`sensor_demo` 的开机自启动由运行包顶层脚本 `start_sensor_demo.sh` 管理：

```bash
cd /root/demo
./start_sensor_demo.sh            # 前台启动 sensor_demo（等效 ./sensor_demo）
./start_sensor_demo.sh enable     # 安装开机自启动（需要 root）
./start_sensor_demo.sh disable    # 取消开机自启动（需要 root）
./start_sensor_demo.sh status     # 查看自启动与运行状态
```

开机自启动通过板端 `/userdata/startup.sh` 实现：系统 `S99auto_startup` 在 `/userdata` 挂载后执行该文件。脚本只追加/删除自己带 `SENSOR_DEMO_AUTOSTART_MANAGED` 标记的块，不会覆盖其它脚本（如 `wifi_setup.sh`）写入的内容；取消自启动时若文件只剩余注释/空行残留会整体删除。开机自启动使用运行包内默认配置，直接修改 `config/sensor_config.yaml` 即可调整，无需重新执行 `enable`。`enable`/`disable` 需要 root 权限。

(non-ros-can)=

## 11. CAN Demo

`can_demo` 使用 Linux SocketCAN `CAN_RAW` 接口操作 TCAN4550 驱动注册的网络设备。默认使用经典 CAN（载荷 `0..8` 字节）；`--fd` 显式开启 CAN FD 发送（最长 `64` 字节）或经典/FD 混合接收。两种格式均支持 11-bit 标准和 29-bit 扩展 ID；经典 CAN 可接收远程帧，FD 没有远程帧。不支持错误帧订阅或自动回包。程序不直接访问 SPI、不修改设备树、GPIO、bitrate 或接口状态，也不依赖相机/IMU 运行库或 `cam-service`。

### 前置条件与接口配置

- BSP 已启用 CAN、CAN_RAW、M_CAN/TCAN4550 驱动，并正确配置 SPI、IRQ、时钟、供电与 pinmux。没有 `can0` 时先修复 BSP，不靠应用自动创建接口。
- 按正式 V2 标识断电连接 CAN_H、CAN_L 与参考地；不要按 UART/TTL 接线。总线两端按规范配置 `120Ω` 终端，确认既有终端后再接入，不猜测连接器针序或板载终端状态。
- 对端必须使用相同 bitrate，并处于可接收/ACK 的工作状态。下面的 `500000` 仅为示例，不是板卡固定默认值。接口名以现场枚举为准。

以下配置需 root 或网络管理权限，且会中断该 CAN 接口；先确认没有其他 CAN 应用或控制业务正在使用，再手动执行：

```bash
ip -details -statistics link show can0
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 fd off
ip link set dev can0 up
ip -details -statistics link show can0
```

使用 CAN FD 时，两端均须支持 FD，并匹配仲裁段和数据段速率、ISO/non-ISO 模式；下面 `500000` / `2000000` 只是示例。确认接口没有其他业务使用后，手动将其配置为 FD，再运行带 `--fd` 的 demo：

```bash
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 dbitrate 2000000 fd on
ip link set dev can0 up
ip -details -statistics link show can0
```

FD 接口的 MTU 应为 `72`；`--fd` 遇到经典接口 MTU `16` 会失败，不自动重配置。`--brs` 决定发送帧是否在数据段切换速率，对端需能接收对应帧。经典 CAN 默认模式也可以在 FD 接口上发送/接收经典帧，但不会接收 FD 帧。

若命令不支持 CAN 参数，需安装支持 CAN 的 iproute2；若驱动探测失败、接口未注册或处于 BUS-OFF，先检查 BSP、接线、终端、对端和 bitrate，不停止或重配 `cam-service`。程序遇到接口不存在、非 CAN 设备或未 UP 会明确失败。

### 收发示例

终端 A 接收；默认持续等待，按 Ctrl-C 正常退出：

```bash
cd /root/demo
./can_demo --interface can0 --mode rx
# 有限接收：10 帧，每次等待的空闲超时为 5 秒
./can_demo --interface can0 --mode rx --count 10 --timeout-ms 5000
```

发送示例（外部节点先准备好接收）：

```bash
cd /root/demo
./can_demo --interface can0 --mode tx --id 123 --data 0102030405060708 --count 10 --interval-ms 100
./can_demo --interface can0 --mode tx --extended --id 1ABCDE --data AABB
./can_demo --interface can0 --mode tx --id 123 --data ''
```

CAN FD 示例（先完成 FD 接口配置，外部节点先准备好接收）：

```bash
# 混合接收经典数据/远程帧与 FD 数据帧；不是只接收 FD 的过滤器
./can_demo --interface can0 --mode rx --fd --count 10 --timeout-ms 5000
# 12 字节 FD，不切换数据段速率
./can_demo --interface can0 --mode tx --fd --id 123 --data 000102030405060708090A0B
# 16 字节扩展 ID FD，开启 BRS
./can_demo --interface can0 --mode tx --fd --brs --extended --id 1ABCDE --data 000102030405060708090A0B0C0D0E0F
```

| 参数 | 语义 |
|---|---|
| `--interface <name>` | 默认 `can0`；仅操作已注册且 UP 的 CAN 设备 |
| `--mode <rx\|tx>` | 默认 `rx`；不会默认发帧 |
| `--id <hex>` | TX ID，默认 `123`；可带 `0x`，标准范围 `0..7FF`，扩展范围 `0..1FFFFFFF` |
| `--extended` | 显式选择 TX 29-bit ID；数值大小不会自动切换格式 |
| `--fd` | TX 使用 FD 帧；RX 接收经典与 FD 混合帧；要求接口启用 FD、MTU `72` |
| `--brs` | TX 数据段速率切换，必须同时使用 `--mode tx --fd`；不是 RX 过滤器 |
| `--data <hexbytes>` | TX 默认 `0102030405060708`；经典 `0..8` 字节；FD 接受 `0..8,12,16,20,24,32,48,64` 字节，其他长度拒绝且不隐式补零；偶数个 hex 字符，无分隔符，空字符串表示零载荷 |
| `--count <n>` | RX 默认 `0`（持续）；TX 默认 `1`；显式 `0` 持续运行至 Ctrl-C |
| `--interval-ms <n>` | TX 帧间等待，默认 `1000`，范围 `1..3600000` ms；不是实时发送周期保证 |
| `--timeout-ms <n>` | RX 每次等待的空闲超时，默认 `0`（无限），范围 `0..3600000` ms；不是整个会话超时 |
| `--help` / `--version` | 单独使用，不打开 CAN 硬件 |

发送专用参数要求 `--mode tx`；`--fd` 可用于收发，`--brs` 还要求 `--fd`。非法参数退出 `2`，接口/I/O/接收超时失败退出 `1`，计数完成或 SIGINT/SIGTERM 正常中断退出 `0`。经典输出不变，形如 `rx 123#0102030405060708`，扩展 ID 固定 8 位，远程帧如 `rx 123#R8`。FD 输出为 `ID##<flags><data>`，flags 是一个十六进制数字，bit 0 为 BRS、bit 1 为 ESI；例如 `rx 123##1000102030405060708090A0B` 表示 BRS 置位的 12 字节 FD 帧。ESI 由发送控制器报告，demo 不提供设置 ESI 的参数；`--extended` 只改变 ID 格式，不开启 FD。

### 验证与限制

`tx_queued=N` 只表示 N 帧被内核接受，不表示对端收到或每帧已在总线上完成。默认 SocketCAN 本地回环可能让同机另一个接收进程看到发帧；这不能证明外部接线、收发器或 ACK 正常。外部验收须在第二个物理节点核对 ID、格式、载荷和计数，再反向发帧确认本板接收，同时检查 `ip -details -statistics link show can0` 的错误、丢帧和 BUS-OFF 状态。host 数据报逻辑测试、vcan 或 `--help` 不代替这一步。

应用支持 FD 不等于当前 BSP 已通过实板完整性验收。受影响 BSP 的长 FD 载荷可能损坏，不能仅凭收齐帧数、没有总线错误或短帧通过认定可靠；须先修复底层问题，并在第二个物理节点逐字节核对长载荷、FD/BRS 标志及双向计数。

单独编译使用 `scripts/build_can_demo.sh`，完整打包使用 `scripts/package_runtime.sh`，详见[公开 Demo 源码编译](../development/open-source-build.md)。
