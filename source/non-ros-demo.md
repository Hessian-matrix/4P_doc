# non-ROS Demo 使用

[`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo) 是面向用户的最小 non-ROS 公开交付仓库，提供四目 SC132 RTSP、四路拼接 RTSP、ICM-42688 IMU 和 UART 示例。

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

部署时完整复制 `demo/` 目录内容。顶层 `cam_demo`、`sensor_demo`、`mosaic_rtsp_demo`、`imu_reader_demo` 和 `serial_port_demo` 是启动脚本，会设置运行所需的 `LD_LIBRARY_PATH`；真实 ELF 位于 `bin/`。

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
  # width/height: 1280x1088（默认）、640x480、720x480 或 1280x720，任一轴向
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
- `rtsp.codec` 支持 `h264` 和 `h265`。
- IMU采样率支持`25/50/100/200/500/1000/2000Hz`，默认`1000Hz`。
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

完整 MP4 session 包含 `camera0.mp4` 到 `camera3.mp4`、`camera0_timestamps.csv` 到 `camera3_timestamps.csv`、`imu.csv`、`camera_params.yaml`、`session_status.json` 和 `publication_receipt.json`。MP4 文件使用名义 H.264 frame timing；精确纳秒相机时间戳以同目录 `cameraN_timestamps.csv` 为准。不完整运行会保留为 `.partial` recovery 目录，不能当作 complete 数据源。

离线转换 JPEG 数据集时，在开发机使用公开 demo 仓中的脚本：

```bash
python3 scripts/rosbag_extract.py /root/save_demo/record.bag /data/record_dataset
python3 scripts/mp4_extract.py /root/save_demo/mp4_session /data/mp4_dataset
```

| `imu.sample_rate_hz` | `1000` | `25/50/100/200/500/1000/2000`。 |

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
--trigger-mode <software_gpio|none>
--diagnostics
--max-skew-ns <ns>
--frame-timeout-ms <ms>
```

Trigger 模式状态：

| 模式 | 当前状态 |
|---|---|
| `software_gpio` | 默认且唯一已验证的稳定模式。 |
| `none` | 实验性，不属于 V1 稳定配置。 |

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
- `--fps` 支持 `25|30|40|50|60`，默认 `30`；`25/30/40/50` 是稳定功能档，`60` 是显式 stress-only 压力档，不属于稳定发布 profile。

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

## 8. 串口 Demo


UART1/UART7 普通 3.3V 硬件通信已通过 V1 验收；`serial_port_demo` 是普通 UART 模式下的公开用户示例，不适用于 DEBUG_UART。PPS 模式下 UART7 RX 切换为 `/dev/pps2`，UART7 TX 释放为 GPIO/IO；该模式下不要运行 `serial_port_demo`。DEBUG_UART 为 `1.8V`；UART1 是 `/dev/ttyS1`、UART7 是 `/dev/ttyS7`，两者均为 `3.3V` 用户 UART，接口为 GH1.25-4P。UART1/UART7 的 `3V3` 脚支持输入/输出并可为外设供电，两个接口共享合计 `500 mA` 限制并支持热插拔。

接线时板端 TX 接对端 RX，板端 RX 接对端 TX，并始终共地；禁止 5V TTL、RS-232 和 USB-UART 适配器 VCC 反灌。DEBUG_UART 只能接 `1.8V` 逻辑；UART1/UART7 使用 `3.3V` 逻辑。UART1/UART7 的 `3V3` 脚支持输入/输出并可为外设供电，两个接口共享合计 `500 mA` 限制并支持热插拔；板卡顶视图接口位置和完整供电边界见[硬件连接与安全](hardware-and-safety.md#uart)。

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
