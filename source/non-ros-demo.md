# non-ROS Demo 使用

[`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo) 是面向用户的最小 non-ROS 公开交付仓库，提供四目 SC132 RTSP、ICM-42688 IMU 和 UART 示例。底层实现细节和未公开验证资料不属于公开交付内容。

## 1. 目录和运行包

常用入口：

```text
<non-ros-demo-root>/
├── demo/                    # 可直接部署到 X5 /root/demo 的运行包
│   ├── cam_demo
│   ├── sensor_demo
│   ├── imu_reader_demo
│   ├── serial_port_demo
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

部署时完整复制 `demo/` 目录内容。顶层 `cam_demo`、`sensor_demo`、`imu_reader_demo` 和 `serial_port_demo` 是启动脚本，会设置运行所需的 `LD_LIBRARY_PATH`；真实 ELF 位于 `bin/`。

## 2. 运行联合入口 `sensor_demo`

`sensor_demo` 同时运行：

- 四路 SC132 相机；
- PRRTSP v2 H.264/H.265 RTSP 推流；
- ICM-42688 GPIO395 DRDY + sensor timestamp FIFO IMU 采集线程。

```bash
cd /root/demo
./sensor_demo
```

常用覆盖：

```bash
./sensor_demo --sample-rate-hz 2000
./sensor_demo --print-rate-hz 50 --print-metrics
./sensor_demo --diagnostics
```

退出时会输出 IMU 摘要：

```text
SENSOR_IMU_RESULT samples=... invalid=... timestamp_duplicates=... timestamp_regressions=... effective_hz=...
```
`effective_hz`按相对1000Hz目标的ppm误差验收；V1门限为绝对误差`<=12000ppm`，等价稳定窗口约`988.0–1012.0Hz`。

`timestamp_duplicates=0`、`timestamp_regressions=0` 是时间戳单调性的关键观察项。

## 3. YAML 配置

`sensor_demo` 启动时读取 `${DEMO_DIR:-当前目录}/config/sensor_config.yaml`。命令行参数优先于 YAML。

默认配置结构：

```yaml
camera:
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 1000
  print_rate_hz: 10
  print_metrics: false
```

边界：

- `camera.width` / `camera.height` 固定为 `1280` / `1088`，修改会被拒绝。
- 完整四目路径固定为四路；单颗 sensor 诊断使用 `cam_demo --camera-id`。
- `camera.fps` 默认 `30`；`25/30/40/50` 是 V1 稳定功能配置；`60` 是显式 `stress-only` 压力配置，不是稳定发布 profile。
- `rtsp.codec` 支持 `h264` 和 `h265`。
- IMU 采样率支持 `25/50/100/200/500/1000/2000Hz`。

## 4. 单独运行相机 RTSP

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
--trigger-mode <software_gpio|vin_lpwm|none>
--diagnostics
--max-skew-ns <ns>
--frame-timeout-ms <ms>
```

Trigger 模式状态：

| 模式 | 当前状态 |
|---|---|
| `software_gpio` | 默认且唯一已验证的稳定模式。 |
| `vin_lpwm` | 实验性，不属于 V1 稳定配置。 |
| `none` | 实验性，不属于 V1 稳定配置。 |

限制：`--rotate 180` 只支持 `30fps`，不支持 `25/40/50/60fps`。`60fps` 必须显式指定，仅用于压力测试。

默认四路 RTSP：

```text
CAM1 / cam0 -> rtsp://<x5-ip>:554/PRR
CAM2 / cam1 -> rtsp://<x5-ip>:555/PRR
CAM3 / cam2 -> rtsp://<x5-ip>:556/PRR
CAM4 / cam3 -> rtsp://<x5-ip>:557/PRR
```

其中 CAM1/CAM2/CAM3/CAM4 是板上物理丝印，cam0/cam1/cam2/cam3 是软件相机 ID。

单颗 sensor 诊断：

```bash
./cam_demo --camera-id 0 --diagnostics
./cam_demo --camera-id 1 --diagnostics
./cam_demo --camera-id 2 --diagnostics
./cam_demo --camera-id 3 --diagnostics
```

每次只运行一个 `cam_demo`。该模式用于排查单颗 sensor、FPC、供电、I2C 和 MIPI/VIN 链路，不代表 2 路或 3 路组合能力。

`cam-service` 是相机运行依赖，保持其运行。切换 `sensor_demo`、`cam_demo` 或用户自研相机应用前，先正常退出旧相机应用，避免 camera/VIO/编码资源冲突。

## 5. 单独运行 IMU

```bash
cd /root/demo
./imu_reader_demo
./imu_reader_demo --sample-rate-hz 2000 --count 10000
```

默认按 `10Hz` 打印抽样记录；程序仍消费全部 IMU 样本。需要看指标时使用：

```bash
./imu_reader_demo --print-metrics
```

关键字段：

- `ts_ns`：映射到 `system_realtime` epoch 的 IMU sample 时间戳，单位 `ns`。
- `accel_mps2`：加速度，单位 `m/s^2`。
- `gyro_rps`：角速度，单位 `rad/s`。
- `uncertainty_us`、`gpio_gap_count`、`fifo_overflow_count`、`mapper_failure_count`：时间戳映射和采集链路诊断。

`accel_mps2` 按 `[X, Y, Z]` 顺序输出，符号以[硬件连接与安全](hardware-and-safety.md#uart)中的板卡顶视图为参考：设备静止且水平放置时约为 `[0, 0, -9.8] m/s^2`；向图片左侧加速时 X 为负；向图片顶部/产品前方加速时 Y 为负。该参考只用于 IMU 读数理解，不定义 IMU 与相机、base、optical frame 或其他坐标系之间的变换。

IMU 路径使用 GPIO395 DRDY + sensor timestamp FIFO，不使用 GPIO397、FSYNC 或 `icm42688_pulse_fsync()`。

## 6. 串口 Demo

UART1/UART7 3.3V 硬件通信已通过 V1 验收；`serial_port_demo` 是 UART1/UART7 的公开用户示例，不适用于 DEBUG_UART。UART1 是 `/dev/ttyS1`，GH1.25-4P；UART7 是 `/dev/ttyS7`，GH1.25-4P。两者均为用户可编程 `3.3V` UART。

接线时板端 TX 接适配器 RX，板端 RX 接适配器 TX，并始终共地；禁止 5V TTL、RS-232 和 USB-UART 适配器 VCC 反灌。DEBUG_UART 是 `1.8V` 系统控制台/调试口，禁止接入 `3.3V` 或 `5V` 逻辑。UART1/UART7 两个 3.3V 供电脚对外设供电合计额定边界为 `500 mA`，超过时使用独立电源并防止反灌；板卡顶视图接口位置和完整 3V3 供电边界见[硬件连接与安全](hardware-and-safety.md#uart)。

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

## 7. 验证建议

- 相机：用 `ffprobe` 或播放器拉取四路 RTSP，并确认 codec、分辨率和帧率。
- IMU：观察 `SENSOR_IMU_RESULT` 和 `timestamp_duplicates` / `timestamp_regressions`。
- 动态库：始终整包部署，避免混用其他工程或系统目录中的同名 `.so`。
- 进程占用：不要同时运行多个相机应用；切换模式前先退出前一个进程。
