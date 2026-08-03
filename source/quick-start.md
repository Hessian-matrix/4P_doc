# 快速开始

本页给用户一条从选择 non-ROS 或 ROS2 路径到板端冒烟验证的最短路径。需要更完整的升级/回滚流程时，见 [部署、升级与回滚](deployment-and-upgrade.md)；需要接口和数据语义时，见 [数据合同](data-contracts.md) 与 [API 参考](api-reference.md)。

## 1. 选择使用路径

| 目标 | 推荐入口 | 适合场景 |
|---|---|---|
| 直接在 X5 上验证四目 RTSP、IMU、串口 | [RoboBaton_4p_demo](https://github.com/Hessian-matrix/RoboBaton_4p_demo) 的 `demo/` | 不改源码，最快验证硬件和运行包。 |
| 二次开发 non-ROS 示例 | [RoboBaton_4p_demo](https://github.com/Hessian-matrix/RoboBaton_4p_demo) | 修改 `cam_demo`、`sensor_demo`、`imu_reader_demo` 或串口示例。 |
| 接入 ROS2 图像和 IMU topics | [ROS2 Demo 使用](ros2-demo.md) | 使用 ROS2 Humble 订阅四路 raw/compressed 图像、CameraInfo、IMU 和温度。 |

## 2. 获取 non-ROS 仓库

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
```

`<non-ros-demo-root>/demo/` 是可直接部署到 X5 的运行包。复制的是 `demo/` 目录里的内容，不是把外层 `demo/` 目录复制成 `/root/demo/demo/`。

## 3. 安全部署运行包

先上传到临时目录并校验 manifest：

```bash
cd <non-ros-demo-root>
ssh root@<x5-ip> "rm -rf /root/demo.new && mkdir -p /root/demo.new"
tar -C demo -cf - . | ssh root@<x5-ip> "tar -xf - -C /root/demo.new"
ssh root@<x5-ip> "cd /root/demo.new && sha256sum -c manifest.sha256"
```

校验通过后再备份旧包并切换：

```bash
ssh root@<x5-ip> "\
  set -e; \
  ts=\$(date +%Y%m%d-%H%M%S); \
  if [ -d /root/demo ]; then mv /root/demo /root/demo.bak.\$ts; fi; \
  mv /root/demo.new /root/demo; \
  chmod +x /root/demo/cam_demo /root/demo/sensor_demo /root/demo/imu_reader_demo /root/demo/serial_port_demo /root/demo/bin/*"
```

如果 manifest 校验失败，删除 `/root/demo.new` 并保留旧 `/root/demo`。不要把 `rm -rf /root/demo` 作为更新第一步。

## 4. non-ROS 最短运行

保持 `cam-service` 运行；只确保旧的相机 demo 或用户自研相机应用已经退出。

```bash
ssh root@<x5-ip>
# 以下命令在 X5 板端 SSH 终端中执行。
cd /root/demo
./sensor_demo
```

`sensor_demo` 联合运行：

- 四路 SC132 相机；
- PRRTSP v2 H.264/H.265 RTSP 推流；
- ICM-42688 GPIO395 DRDY + sensor timestamp FIFO IMU 采集。

默认四路 RTSP 地址：

```text
rtsp://<x5-ip>:554/PRR
rtsp://<x5-ip>:555/PRR
rtsp://<x5-ip>:556/PRR
rtsp://<x5-ip>:557/PRR
```

开发机可用 `ffprobe` 检查其中一路：

```bash
ffprobe -v error -rtsp_transport tcp \
  -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate \
  -of default=noprint_wrappers=1 \
  rtsp://<x5-ip>:554/PRR
```

期望看到 `codec_name=h264`、`width=1280`、`height=1088` 和目标帧率。使用 `./cam_demo --codec h265` 时，codec 期望为 `hevc`。

## 5. 单项冒烟

相机单路诊断：

```bash
cd /root/demo
./cam_demo --camera-id 0 --diagnostics
./cam_demo --camera-id 1 --diagnostics
./cam_demo --camera-id 2 --diagnostics
./cam_demo --camera-id 3 --diagnostics
```

每次只运行一个 `cam_demo`。该模式用于排查单颗 sensor、FPC、供电、I2C 和 MIPI/VIN 链路，不代表 2 路或 3 路组合能力。

IMU：

```bash
cd /root/demo
./imu_reader_demo --sample-rate-hz 1000 --print-metrics
```

UART：

V1 只交付串口软件调用示例；下面的命令不代表 UART 硬件通信已经完成 V1 验收。

```bash
cd /root/demo
./serial_port_demo --port /dev/ttyS1 --mode txrx --baud 115200
```

UART TX/RX 使用 `3.3V` 逻辑电平并要求共地。按板卡顶视图，`DEBUG_UART` 从左到右为 `GND/RX/TX`，`UART7` 和 `UART1` 为 `3V3/RX/TX/GND`；图片没有标出 Pin 1。3V3 供电方向/电流和热插拔能力待产品确认，不要接入 USB-UART VCC、5V TTL 或 RS-232。完整边界见[硬件连接与安全](hardware-and-safety.md#uart-pinout-与-v1-边界)。

## 6. ROS2 最短运行

如果板端已经部署 `/root/ros2_demo/install`，最短运行命令如下。详细构建、上传、manifest 校验和回滚流程见 [ROS2 Demo 使用](ros2-demo.md) 与 [部署、升级与回滚](deployment-and-upgrade.md)。

```bash
ssh root@<x5-ip>
# 以下命令在 X5 板端 SSH 终端中执行。
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

另开一个终端加载同一环境后做快速检查；查看 topic graph 时优先绕过可能过期的 daemon：

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 topic list --no-daemon --include-hidden-topics
ros2 topic hz /robobaton/cam0/image_raw
ros2 topic hz /robobaton/cam0/image_raw/compressed
ros2 topic echo /robobaton/cam0/camera_info --once
ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

ROS2 不提供 RTSP；需要 RTSP 时使用 non-ROS `/root/demo` 路径。

## 7. 常见第一步排查

- 找不到动态库：确认运行的是顶层脚本 `/root/demo/sensor_demo` 或已执行 `. ./env.sh`，并完整复制了 `/root/demo/lib/`。
- RTSP 无法拉流：确认板端 demo 仍在运行、端口为 `554/555/556/557`、path 为 `/PRR`，并优先用 `ffprobe -rtsp_transport tcp` 区分网络和播放器问题。
- 单路无图：先用 `./cam_demo --camera-id <0|1|2|3> --diagnostics` 单独检查对应 FPC、供电、I2C、MIPI/VIN 链路。
- IMU 无数据：确认 `/dev/spidev2.0` 存在，采样率使用 `25/50/100/200/500/1000/2000Hz` 之一。
- ROS2 topic 无数据：确认已经 `source /root/ros2_demo/install/robobaton_ros2_env.bash`，优先用 `ros2 topic list --no-daemon --include-hidden-topics` 排除过期 daemon，且没有其他相机应用占用 camera/VIO 资源。
