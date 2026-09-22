# Deployment, Upgrade, and Rollback

This page gives the safe deployment flow for the non-ROS runtime package and the ROS2 install package. The goal is to switch the target directory only after the new package is fully uploaded and passes manifest verification, to avoid deleting the old runtime package first and losing the ability to roll back.

```{important}
Keep `cam-service` running. Before updating, only exit the old `sensor_demo`, `cam_demo`, or other camera applications; do not stop `cam-service`.
```

## 1. non-ROS Pre-Check

Host preparation:

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # change to the actual repository directory
cd "$NON_ROS_ROOT"
test -f demo/manifest.sha256
test -x demo/cam_demo
test -x demo/sensor_demo
```

Confirm network and SSH:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh "root@${X5_IP}" "hostname && test -d /root && pgrep -a cam-service"
```

If `cam-service` does not exist or is abnormal, handle it per the product-support flow first; do not treat stopping the service as a routine deployment step.

## 2. non-ROS Upload, Verify, Switch, and Smoke

The following is one complete safe entry: upload to a unique temporary directory, complete manifest verification, confirm the old application exited, back up the old directory and atomically switch, then run help/smoke.

```bash
X5_IP=192.168.1.12  # change to the actual board address
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

If manifest verification, the old-application-exit check, or help/smoke fails, the temporary directory must not be used as a formal package. The pre-switch backup directory is `${REMOTE_BACKUP}`; if later runtime verification fails, first exit the new demo, then restore that backup.

## 3. non-ROS Minimal Verification

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh "root@${X5_IP}" "cd /root/demo && ./cam_demo --help >/tmp/cam_demo.help"
ssh "root@${X5_IP}" "cd /root/demo && ./imu_reader_demo --help >/tmp/imu_reader_demo.help"
ssh "root@${X5_IP}" "cd /root/demo && ./serial_port_demo --help >/tmp/serial_port_demo.help"
ssh "root@${X5_IP}" "cd /root/demo && ./sensor_demo --help >/tmp/sensor_demo.help"
```

When verifying the camera, start only one camera entry.

Terminal A: SSH into the X5 and run `sensor_demo`:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh "root@${X5_IP}" "cd /root/demo && ./sensor_demo"
```

Terminal B: on the host run `ffprobe` to pull one RTSP stream:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ffprobe -v error -rtsp_transport tcp \
  -select_streams v:0 \
  -show_entries stream=codec_name,width,height,avg_frame_rate \
  -of default=noprint_wrappers=1 \
  "rtsp://${X5_IP}:554/PRR"
```

Expect to see codec, `width=1280`, `height=1088`, and the target frame rate. After verification, exit the demo normally with `Ctrl+C` in terminal A.

## 4. non-ROS Rollback

If minimal verification fails after switching, first exit the new demo, then restore the most recent backup:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh "root@${X5_IP}" "\
  set -e; \
  latest_bak=\$(ls -dt /root/demo.bak.* 2>/dev/null | head -n 1); \
  test -n \"\$latest_bak\"; \
  mv /root/demo /root/demo.failed.\$(date +%Y%m%d-%H%M%S); \
  mv \"\$latest_bak\" /root/demo"
```

After rollback, re-run `./sensor_demo --help`, `./imu_reader_demo --help`, and one RTSP pull verification.

## 5. ROS2 install Pre-Check

ROS2 uses the independent directory `/root/ros2_demo`; do not mix it with non-ROS `/root/demo`.

Host preparation:

```bash
ROS2_ROOT="$HOME/RoboBaton_4P_ROS2_demo"  # change to the actual repository directory
cd "$ROS2_ROOT"
test -d 1.ros2_build/install
test -x 1.ros2_build/install/robobaton_ros2_env.bash
python3 script/verify_install.py 1.ros2_build/install
test -f 1.ros2_build/install/lib/robobaton_4p_ros2_demo/abi_manifest.sha256
```

Confirm on-device ROS2 and camera service:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh "root@${X5_IP}" "test -f /opt/ros/humble/setup.bash && pgrep -a cam-service"
```

Keep `cam-service` running; before deployment only exit the old `robobaton_sensors_node` or other camera applications.

## 6. ROS2 Upload, Verify, Switch, and Smoke

ROS2 uses the same order as non-ROS: unique temporary directory, full archive checksum, runtime manifest after unpacking, check old application, back up old directory, atomic switch, help/smoke, and restore the most recent backup on failure.

```bash
X5_IP=192.168.1.12  # change to the actual board address
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
REMOTE_NEW="/root/ros2_demo.new.${RUN_ID}"
REMOTE_BACKUP="/root/ros2_demo.bak.${RUN_ID}"
ARCHIVE="/tmp/robobaton_4p_ros2_install.${RUN_ID}.tar"

# Generate a deterministic archive and checksum of the full install tree on the host.
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

The archive checksum covers the transferred content of the full install tree; the runtime `abi_manifest.sha256` covers the runtime/ABI subset declared in the package. Both must pass. The pre-switch old-package backup is `${REMOTE_BACKUP}`; if the ROS2 topic smoke or later runtime verification fails, first exit the new node, then restore that backup.

## 7. ROS2 Minimal Verification

Terminal A: SSH into the X5 and run the ROS2 node:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh "root@${X5_IP}"
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 launch robobaton_4p_ros2_demo robobaton_sensors.launch.py
```

Terminal B: load the same environment and check topics:

```bash
source /root/ros2_demo/install/robobaton_ros2_env.bash
ros2 topic list --no-daemon --include-hidden-topics
ros2 topic hz /robobaton/cam0/image_raw
ros2 topic hz /robobaton/cam0/image_raw/compressed
ros2 topic echo /robobaton/cam0/camera_info --once
ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor
```

After verification, exit the node normally with `Ctrl+C` in terminal A.

## 9. ROS2 Rollback

If minimal verification fails after switching, first exit the new ROS2 node, then restore the most recent backup:

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh "root@${X5_IP}" "\
  set -e; \
  latest_bak=\$(ls -dt /root/ros2_demo.bak.* 2>/dev/null | head -n 1); \
  test -n \"\$latest_bak\"; \
  mv /root/ros2_demo /root/ros2_demo.failed.\$(date +%Y%m%d-%H%M%S); \
  mv \"\$latest_bak\" /root/ros2_demo"
```

After rollback, re-run `source /root/ros2_demo/install/robobaton_ros2_env.bash`, the launch, and the topic checks.
