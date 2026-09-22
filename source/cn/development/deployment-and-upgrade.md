# 部署、升级与回滚

本页给出 non-ROS 运行包和 ROS2 install 包的安全部署流程。目标是在新包完整上传并通过 manifest 校验后再切换目标目录，避免先删除旧运行包导致无法回滚。

```{important}
保持 `cam-service` 运行。更新前只退出旧的 `sensor_demo`、`cam_demo` 或其他相机应用，不停止 `cam-service`。
```

## 1. non-ROS 预检

开发机准备：

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # 改成实际仓库目录
cd "$NON_ROS_ROOT"
test -f demo/manifest.sha256
test -x demo/cam_demo
test -x demo/sensor_demo
```

确认网络和 SSH：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh "root@${X5_IP}" "hostname && test -d /root && pgrep -a cam-service"
```

如果 `cam-service` 不存在或状态异常，先按产品支持流程处理；不要把停止服务作为常规部署步骤。

## 2. non-ROS 上传、校验、切换与 smoke

下面是一条完整的安全入口：上传到唯一临时目录，完成 manifest 校验，确认旧应用退出后备份旧目录并原子切换，最后执行 help/smoke。

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
REMOTE_NEW="/root/demo.new.${RUN_ID}"
REMOTE_BACKUP="/root/demo.bak.${RUN_ID}"

ssh "root@${X5_IP}" "umask 077; mkdir -m 700 '${REMOTE_NEW}'"
if ! tar -C demo -cf - . | ssh "root@${X5_IP}" "tar -xf - -C '${REMOTE_NEW}'"; then
  ssh "root@${X5_IP}" "rm -rf '${REMOTE_NEW}'"
  exit 1
fi
if ! ssh "root@${X5_IP}" "cd '${REMOTE_NEW}' && sha256sum -c manifest.sha256"; then
  ssh "root@${X5_IP}" "rm -rf '${REMOTE_NEW}'"
  exit 1
fi

if ! ssh "root@${X5_IP}" "set -e; \
  non_ros_demo_running() { \
    for proc in /proc/[0-9]*; do \
      [ -r \"\$proc/cmdline\" ] || continue; \
      command_path=\$(tr '\\0' '\\n' < \"\$proc/cmdline\" | sed -n '1p'); \
      command_name=\${command_path##*/}; \
      case \"\$command_name\" in \
        sensor_demo|cam_demo|imu_reader_demo|serial_port_demo) return 0 ;; \
      esac; \
    done; \
    return 1; \
  }; \
  if non_ros_demo_running; then \
    echo 'old non-ROS demo process is still running; exit it before switching'; exit 2; \
  fi; \
  if [ -d /root/demo ]; then mv /root/demo '${REMOTE_BACKUP}'; fi; \
  mv '${REMOTE_NEW}' /root/demo; \
  chmod +x /root/demo/cam_demo /root/demo/sensor_demo /root/demo/imu_reader_demo /root/demo/serial_port_demo /root/demo/bin/*"; then
  ssh "root@${X5_IP}" "rm -rf '${REMOTE_NEW}'"
  exit 1
fi

if ! ssh "root@${X5_IP}" "cd /root/demo && ./cam_demo --help >/tmp/cam_demo.help && ./sensor_demo --help >/tmp/sensor_demo.help"; then
  ssh "root@${X5_IP}" "set -e; \
    if [ -d /root/demo ]; then mv /root/demo /root/demo.failed.${RUN_ID}; fi; \
    if [ -d '${REMOTE_BACKUP}' ]; then mv '${REMOTE_BACKUP}' /root/demo; fi"
  exit 1
fi
```

manifest 校验、旧应用退出检查或 help/smoke 失败时，不得把临时目录当作正式包使用。切换前备份目录为 `${REMOTE_BACKUP}`；后续运行验证失败时，先退出新 demo，再恢复该备份。

## 3. non-ROS 最小验证

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh "root@${X5_IP}" "cd /root/demo && ./cam_demo --help >/tmp/cam_demo.help"
ssh "root@${X5_IP}" "cd /root/demo && ./imu_reader_demo --help >/tmp/imu_reader_demo.help"
ssh "root@${X5_IP}" "cd /root/demo && ./serial_port_demo --help >/tmp/serial_port_demo.help"
ssh "root@${X5_IP}" "cd /root/demo && ./sensor_demo --help >/tmp/sensor_demo.help"
```

相机验证时只启动一个相机入口。

终端 A：SSH 到 X5 板端并运行 `sensor_demo`：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh "root@${X5_IP}" "cd /root/demo && ./sensor_demo"
```

终端 B：在开发机运行 `ffprobe` 拉一路 RTSP：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ffprobe -v error -rtsp_transport tcp \
  -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate \
  -of default=noprint_wrappers=1 \
  "rtsp://${X5_IP}:554/PRR"
```

期望看到 codec、`width=1280`、`height=1088` 和目标帧率。完成验证后在终端 A 用 `Ctrl+C` 正常退出 demo。

## 4. non-ROS 回滚

如果切换后最小验证失败，先退出新 demo，再恢复最近一次备份：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh "root@${X5_IP}" "\
  set -e; \
  latest_bak=\$(ls -dt /root/demo.bak.* 2>/dev/null | head -n 1); \
  test -n \"\$latest_bak\"; \
  mv /root/demo /root/demo.failed.\$(date +%Y%m%d-%H%M%S); \
  mv \"\$latest_bak\" /root/demo"
```

回滚后重新执行 `./sensor_demo --help`、`./imu_reader_demo --help` 和一路 RTSP 拉流验证。

## 5. ROS2 install 预检

ROS2 使用独立目录 `/root/ros2_demo`，不要和 non-ROS `/root/demo` 混用。

开发机准备：

```bash
ROS2_ROOT="$HOME/RoboBaton_4P_ROS2_demo"  # 改成实际仓库目录
cd "$ROS2_ROOT"
test -d 1.ros2_build/install
test -x 1.ros2_build/install/robobaton_ros2_env.bash
python3 script/verify_install.py 1.ros2_build/install
test -f 1.ros2_build/install/lib/robobaton_4p_ros2_demo/abi_manifest.sha256
```

确认板端 ROS2 和相机服务：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh "root@${X5_IP}" "test -f /opt/ros/humble/setup.bash && pgrep -a cam-service"
```

保持 `cam-service` 运行；部署前只退出旧的 `robobaton_sensors_node` 或其他相机应用。

## 6. ROS2 上传、校验、切换与 smoke

ROS2 使用与 non-ROS 相同的顺序：唯一临时目录、完整 archive checksum、解包后 runtime manifest、检查旧应用、备份旧目录、原子切换、help/smoke，失败时恢复最近备份。

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
REMOTE_NEW="/root/ros2_demo.new.${RUN_ID}"
REMOTE_BACKUP="/root/ros2_demo.bak.${RUN_ID}"
ARCHIVE="/tmp/robobaton_4p_ros2_install.${RUN_ID}.tar"

# 在开发机生成完整 install tree 的确定性 archive 和 checksum。
tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner \
  -C 1.ros2_build/install -cf "${ARCHIVE}" .
(cd "$(dirname "${ARCHIVE}")" && sha256sum "$(basename "${ARCHIVE}")") \
  > "${ARCHIVE}.sha256"

ssh "root@${X5_IP}" "umask 077; mkdir -m 700 '${REMOTE_NEW}'"
scp "${ARCHIVE}" "${ARCHIVE}.sha256" "root@${X5_IP}:${REMOTE_NEW}/"
if ! ssh "root@${X5_IP}" "set -e; \
  cd '${REMOTE_NEW}'; \
  sha256sum -c '$(basename "${ARCHIVE}").sha256'; \
  mkdir -p install; \
  tar -xf '$(basename "${ARCHIVE}")' -C install; \
  rm -f '$(basename "${ARCHIVE}")' '$(basename "${ARCHIVE}").sha256'; \
  test -f install/lib/robobaton_4p_ros2_demo/abi_manifest.sha256"; then
  ssh "root@${X5_IP}" "rm -rf '${REMOTE_NEW}'"
  rm -f "${ARCHIVE}" "${ARCHIVE}.sha256"
  exit 1
fi

if ! ssh "root@${X5_IP}" "set -e; \
  cd '${REMOTE_NEW}/install/lib/robobaton_4p_ros2_demo'; \
  sha256sum -c abi_manifest.sha256; \
  cd '${REMOTE_NEW}/install'; \
  ros2_demo_running() { \
    for proc in /proc/[0-9]*; do \
      [ -r \"\$proc/cmdline\" ] || continue; \
      command_path=\$(tr '\\0' '\\n' < \"\$proc/cmdline\" | sed -n '1p'); \
      command_name=\${command_path##*/}; \
      arg1=\$(tr '\\0' '\\n' < \"\$proc/cmdline\" | sed -n '2p'); \
      arg2=\$(tr '\\0' '\\n' < \"\$proc/cmdline\" | sed -n '3p'); \
      case \"\$command_name\" in \
        robobaton_sensors_node|robobaton_imu_rate_monitor) return 0 ;; \
        ros2) case \"\$arg1\" in launch|run) return 0 ;; esac ;; \
        python|python3) \
          [ \"\${arg1##*/}\" = ros2 ] && { case \"\$arg2\" in launch|run) return 0 ;; esac; }; \
          ;; \
      esac; \
    done; \
    return 1; \
  }; \
  if ros2_demo_running; then \
    echo 'old ROS2 demo process is still running; exit it before switching'; exit 2; \
  fi; \
  if [ -d /root/ros2_demo ]; then mv /root/ros2_demo '${REMOTE_BACKUP}'; fi; \
  mv '${REMOTE_NEW}' /root/ros2_demo"; then
  ssh "root@${X5_IP}" "rm -rf '${REMOTE_NEW}'"
  rm -f "${ARCHIVE}" "${ARCHIVE}.sha256"
  exit 1
fi

if ! ssh "root@${X5_IP}" "set -e; \
  . /root/ros2_demo/install/robobaton_ros2_env.bash; \
  /root/ros2_demo/install/robobaton_ros2_env.bash ros2 topic list --no-daemon --include-hidden-topics >/tmp/ros2_topics; \
  /root/ros2_demo/install/robobaton_ros2_env.bash ros2 run robobaton_4p_ros2_demo robobaton_sensors_node --version >/tmp/ros2_version"; then
  ssh "root@${X5_IP}" "set -e; \
    if [ -d /root/ros2_demo ]; then mv /root/ros2_demo /root/ros2_demo.failed.${RUN_ID}; fi; \
    if [ -d '${REMOTE_BACKUP}' ]; then mv '${REMOTE_BACKUP}' /root/ros2_demo; fi"
  rm -f "${ARCHIVE}" "${ARCHIVE}.sha256"
  exit 1
fi
rm -f "${ARCHIVE}" "${ARCHIVE}.sha256"
```

archive checksum 覆盖完整 install tree 的传输内容；runtime `abi_manifest.sha256` 覆盖包内声明的 runtime/ABI 子集。两者都必须通过。切换前的旧包备份为 `${REMOTE_BACKUP}`，ROS2 topic smoke 或后续运行验证失败时，先退出新节点，再恢复该备份。

## 7. ROS2 最小验证

终端 A：SSH 到 X5 并运行 ROS2 节点：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh "root@${X5_IP}"
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
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh "root@${X5_IP}" "\
  set -e; \
  latest_bak=\$(ls -dt /root/ros2_demo.bak.* 2>/dev/null | head -n 1); \
  test -n \"\$latest_bak\"; \
  mv /root/ros2_demo /root/ros2_demo.failed.\$(date +%Y%m%d-%H%M%S); \
  mv \"\$latest_bak\" /root/ros2_demo"
```

回滚后重新执行 `source /root/ros2_demo/install/robobaton_ros2_env.bash`、launch 和 topic 检查。
