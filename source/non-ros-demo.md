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
- `camera.fps` 常用默认 `30`，`cam_demo` 支持 `25/30/40/50/60`；`60` 为显式高帧率档。
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

限制：`--rotate 180` 只支持 `30fps`，不支持 `25/40/50/60fps`。

默认四路 RTSP：

```text
cam0 -> rtsp://<x5-ip>:554/PRR
cam1 -> rtsp://<x5-ip>:555/PRR
cam2 -> rtsp://<x5-ip>:556/PRR
cam3 -> rtsp://<x5-ip>:557/PRR
```

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

IMU 路径使用 GPIO395 DRDY + sensor timestamp FIFO，不使用 GPIO397、FSYNC 或 `icm42688_pulse_fsync()`。

## 6. 串口 Demo

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
