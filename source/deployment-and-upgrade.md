# 部署、升级与回滚

本页给出 non-ROS 运行包和 ROS2 install 包的安全部署流程。目标是在新包完整上传并通过 manifest 校验后再切换目标目录，避免先删除旧运行包导致无法回滚。

```{important}
保持 `cam-service` 运行。更新前只退出旧的 `sensor_demo`、`cam_demo` 或其他相机应用，不停止 `cam-service`。
```

## 1. non-ROS 预检

开发机准备：

```bash
cd <non-ros-demo-root>
test -f demo/manifest.sha256
test -x demo/cam_demo
test -x demo/sensor_demo
```

确认网络和 SSH：

```bash
ssh root@<x5-ip> "hostname && test -d /root && pgrep -a cam-service"
```

如果 `cam-service` 不存在或状态异常，先按产品支持流程处理；不要把停止服务作为常规部署步骤。

## 2. non-ROS 上传到临时目录

```bash
ssh root@<x5-ip> "rm -rf /root/demo.new && mkdir -p /root/demo.new"
tar -C demo -cf - . | ssh root@<x5-ip> "tar -xf - -C /root/demo.new"
ssh root@<x5-ip> "cd /root/demo.new && sha256sum -c manifest.sha256"
```

`sha256sum -c manifest.sha256` 必须全部通过。失败时直接删除 `/root/demo.new`，保留旧 `/root/demo`：

```bash
ssh root@<x5-ip> "rm -rf /root/demo.new"
```

## 3. non-ROS 备份旧包并切换

确认没有旧相机应用仍在运行。下面命令只查找 demo 进程，实际现场如有用户自研相机应用，也必须先退出。发现旧进程时命令会退出，不会切换目录：

```bash
ssh root@<x5-ip> "\
  set -e; \
  if pgrep -af 'sensor_demo|cam_demo|imu_reader_demo|serial_port_demo'; then \
    echo 'old non-ROS demo process is still running; exit it before switching'; \
    exit 2; \
  fi; \
  ts=\$(date +%Y%m%d-%H%M%S); \
  if [ -d /root/demo ]; then mv /root/demo /root/demo.bak.\$ts; fi; \
  mv /root/demo.new /root/demo; \
  chmod +x /root/demo/cam_demo /root/demo/sensor_demo /root/demo/imu_reader_demo /root/demo/serial_port_demo /root/demo/bin/*"
```

## 4. non-ROS 最小验证

```bash
ssh root@<x5-ip> "cd /root/demo && ./cam_demo --help >/tmp/cam_demo.help"
ssh root@<x5-ip> "cd /root/demo && ./imu_reader_demo --help >/tmp/imu_reader_demo.help"
ssh root@<x5-ip> "cd /root/demo && ./serial_port_demo --help >/tmp/serial_port_demo.help"
ssh root@<x5-ip> "cd /root/demo && ./sensor_demo --help >/tmp/sensor_demo.help"
```

相机验证时只启动一个相机入口。

终端 A：SSH 到 X5 板端并运行 `sensor_demo`：

```bash
ssh root@<x5-ip> "cd /root/demo && ./sensor_demo"
```

终端 B：在开发机运行 `ffprobe` 拉一路 RTSP：

```bash
ffprobe -v error -rtsp_transport tcp \
  -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate \
  -of default=noprint_wrappers=1 \
  rtsp://<x5-ip>:554/PRR
```

期望看到 codec、`width=1280`、`height=1088` 和目标帧率。完成验证后在终端 A 用 `Ctrl+C` 正常退出 demo。

## 5. non-ROS 回滚

如果切换后最小验证失败，先退出新 demo，再恢复最近一次备份：

```bash
ssh root@<x5-ip> "\
  set -e; \
  latest_bak=\$(ls -dt /root/demo.bak.* 2>/dev/null | head -n 1); \
  test -n \"\$latest_bak\"; \
  mv /root/demo /root/demo.failed.\$(date +%Y%m%d-%H%M%S); \
  mv \"\$latest_bak\" /root/demo"
```

回滚后重新执行 `./sensor_demo --help`、`./imu_reader_demo --help` 和一路 RTSP 拉流验证。

## 6. ROS2 install 预检

ROS2 使用独立目录 `/root/ros2_demo`，不要和 non-ROS `/root/demo` 混用。

开发机准备：

```bash
cd <ros2-demo-root>
test -d 1.ros2_build/install
test -x 1.ros2_build/install/robobaton_ros2_env.bash
python3 script/verify_install.py 1.ros2_build/install
test -f 1.ros2_build/install/lib/robobaton_4p_ros2_demo/abi_manifest.sha256
```

确认板端 ROS2 和相机服务：

```bash
ssh root@<x5-ip> "test -f /opt/ros/humble/setup.bash && pgrep -a cam-service"
```

保持 `cam-service` 运行；部署前只退出旧的 `robobaton_sensors_node` 或其他相机应用。

## 7. ROS2 上传、校验与切换

在开发机把完整 install tree 制作成确定性 archive，并上传 archive 与 checksum 到临时目录：

```bash
tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner \
  -C 1.ros2_build/install \
  -cf /tmp/robobaton_4p_ros2_install.tar .
(cd /tmp && sha256sum robobaton_4p_ros2_install.tar > robobaton_4p_ros2_install.tar.sha256)
ssh root@<x5-ip> "rm -rf /root/ros2_demo.new && mkdir -p /root/ros2_demo.new"
scp /tmp/robobaton_4p_ros2_install.tar \
  /tmp/robobaton_4p_ros2_install.tar.sha256 \
  root@<x5-ip>:/root/ros2_demo.new/
ssh root@<x5-ip> "\
  set -e; \
  cd /root/ros2_demo.new; \
  if ! sha256sum -c robobaton_4p_ros2_install.tar.sha256; then \
    cd /root; \
    rm -rf /root/ros2_demo.new; \
    exit 1; \
  fi; \
  mkdir -p install; \
  tar -xf robobaton_4p_ros2_install.tar -C install; \
  rm -f robobaton_4p_ros2_install.tar robobaton_4p_ros2_install.tar.sha256; \
  cd install/lib/robobaton_4p_ros2_demo; \
  sha256sum -c abi_manifest.sha256"
```

archive checksum 覆盖完整 install tree 传输内容；checksum 失败时不得解包、不得切换，并删除 `/root/ros2_demo.new` 保留旧 `/root/ros2_demo`。包内 verifier 和 `abi_manifest.sha256` 的边界是 runtime 可执行文件、image_transport 插件、相关动态库、RUNPATH、runtime 环境脚本、relocatable Bash setup 和 ABI 子集；它们不替代板端 topic、NV12 布局或 IMU 频率检查。

校验失败时删除临时目录并保留旧包：

```bash
ssh root@<x5-ip> "rm -rf /root/ros2_demo.new"
```

切换前确认旧 ROS2 节点已退出。发现旧进程时命令会退出，不会切换目录：

```bash
ssh root@<x5-ip> "\
  set -e; \
  if pgrep -af 'robobaton_sensors_node|robobaton_imu_rate_monitor|ros2 launch|ros2 run'; then \
    echo 'old ROS2 demo process is still running; exit it before switching'; \
    exit 2; \
  fi; \
  ts=\$(date +%Y%m%d-%H%M%S); \
  if [ -d /root/ros2_demo ]; then mv /root/ros2_demo /root/ros2_demo.bak.\$ts; fi; \
  mv /root/ros2_demo.new /root/ros2_demo"

```

## 8. ROS2 最小验证

终端 A：SSH 到 X5 并运行 ROS2 节点：

```bash
ssh root@<x5-ip>
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

终端 B：加载同一环境后检查 topic：

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 topic list --no-daemon --include-hidden-topics
ros2 topic hz /robobaton/cam0/image_raw
ros2 topic hz /robobaton/cam0/image_raw/compressed
ros2 topic echo /robobaton/cam0/camera_info --once
ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

完成验证后在终端 A 用 `Ctrl+C` 正常退出节点。

## 9. ROS2 回滚

如果切换后最小验证失败，先退出新 ROS2 节点，再恢复最近一次备份：

```bash
ssh root@<x5-ip> "\
  set -e; \
  latest_bak=\$(ls -dt /root/ros2_demo.bak.* 2>/dev/null | head -n 1); \
  test -n \"\$latest_bak\"; \
  mv /root/ros2_demo /root/ros2_demo.failed.\$(date +%Y%m%d-%H%M%S); \
  mv \"\$latest_bak\" /root/ros2_demo"
```

回滚后重新执行 `source /root/ros2_demo/install/robobaton_ros2_env.bash`、launch 和 topic 检查。
