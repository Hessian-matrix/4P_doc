# Troubleshooting

## SSH Cannot Connect

| Item | Content |
|---|---|
| Symptom | `ssh root@192.168.1.12` (adjust to the actual board address) times out or refuses the connection. |
| Check | `ping 192.168.1.12` (adjust to the actual board address); confirm the host and X5 are on the same network; confirm the SSH service is provided by the product system. |
| Normal result | Ping succeeds and SSH enters the on-device shell. |
| Common causes | Wrong IP configuration, cable/switch problems, target board not fully booted, SSH service not ready. |
| Recovery / info to collect | Collect the host IP, X5 IP, network topology, and ping/ssh error text. |

## On-Board Wi-Fi Configuration Failure

For the full upload, interactive configuration, and log paths see [Wi-Fi Configuration](getting-started/wifi-configuration.md).

| Item | Content |
|---|---|
| Symptom | `/userdata/wifi_setup.sh` reports a missing command, cannot scan any SSID, authentication fails, DHCP fails, AP cannot start, or Wi-Fi is not restored after boot. |
| Check | Log in through the wired network or `1.8V` DEBUG_UART; run `/userdata/wifi_setup.sh --status`; check `ip link show wlan0`, `iw dev wlan0 info`, `/userdata/wifi/logs/`, and `/userdata/wifi/boot.log`. |
| Normal result | AP mode shows hostapd `ENABLED` and clients get addresses in the configured subnet; STA mode shows association and a DHCP address; with boot-restore enabled, `/userdata/startup.sh` and `current.conf` exist. |
| Common causes | Missing Wi-Fi user-space tools, antenna/signal problems, wrong SSID/password, hidden SSID, router DHCP problems, AP channel/IP/DHCP subnet misconfiguration, or a pre-existing `/userdata/startup.sh` not managed by this script. |
| Recovery / info to collect | Do not switch modes in the same Wi-Fi SSH session; reconfigure through the wired entry. To disable, run `/userdata/wifi_setup.sh --disable`; collect full script errors, interface state, and credential-stripped logs. |

## Runtime Package Verification Failure

| Item | Content |
|---|---|
| Symptom | `sha256sum -c manifest.sha256` in the unique temporary directory `${REMOTE_NEW}` for this deployment reports failure or missing files. |
| Check | Use the `${REMOTE_NEW}` computed from this deployment's `RUN_ID`; confirm the host `demo/manifest.sha256` exists and re-upload to the same temporary directory before verifying. |
| Normal result | All files in the manifest output `OK`. |
| Common causes | Interrupted upload, only partial files copied, or the outer `demo/` copied as `${REMOTE_NEW}/demo/`. |
| Recovery / info to collect | Only delete this deployment's `${REMOTE_NEW}`, keep the old `/root/demo`; collect failed filenames, `RUN_ID`, and the upload command. |

## Dynamic Library Not Found

| Item | Content |
|---|---|
| Symptom | `error while loading shared libraries`, or `.so` missing when running a `bin/` program. |
| Check | `ls -l /root/demo/lib`; run from the `/root/demo` top-level launcher script; run `. ./env.sh` before directly running `bin/`. |
| Normal result | `libsc132.so*`, `libicm42688.so*`, `libprrtsp.so*` exist and load preferentially from `/root/demo/lib`. |
| Common causes | Only a single ELF copied, `lib/` omitted, `env.sh` not loaded, or same-named `.so` mixed from other projects. |
| Recovery / info to collect | Re-deploy the full package and provide `ls -l /root/demo /root/demo/lib` and the full error text. |

## ROS2 Build Cannot Find `ament_package`

| Item | Content |
|---|---|
| Symptom | Cross-build reports `ModuleNotFoundError: No module named 'ament_package'`. |
| Check | On the host, run `source /opt/ros/humble/setup.bash`, then run `python3 -c 'import ament_package'`. |
| Normal result | Python import succeeds and `script/build_x5_ros2.sh --clean --cross-root <cross-root>` can enter the colcon/CMake build. |
| Common causes | Only the X5 target cross environment was loaded, without the host ROS Humble Python environment. |
| Recovery / info to collect | Re-source the host ROS environment; collect the full build command and error text. |

## ROS2 Setup or Dynamic Library Problem

| Item | Content |
|---|---|
| Symptom | `ros2 launch` cannot find the package, node startup reports a missing `.so`, or the environment is wrong after relocating the install. |
| Check | Using Bash: `source /root/ros2_demo/install/robobaton_ros2_env.bash`; confirm `ls /root/ros2_demo/install/lib/robobaton_4p_ros2_demo`. |
| Normal result | `robobaton_ros2_env.bash`, `robobaton_sensors_node`, `robobaton_imu_rate_monitor`, `abi_manifest.sha256`, the NV12 compressed plugin, `libicm42688.so*`, and `libsc132.so*` are found. |
| Common causes | Only a single ELF uploaded, the full install not uploaded, the ROS2 underlay path is not the default `/opt/ros/humble/setup.bash`, or a relocated POSIX `setup.sh` was used without setting `COLCON_CURRENT_PREFIX`. |
| Recovery / info to collect | Re-deploy the full `/root/ros2_demo/install`; for a non-default underlay use `ROBOBATON_ROS_UNDERLAY=/path/to/setup.bash`; when `sh` is required, use `COLCON_CURRENT_PREFIX=/root/ros2_demo/install . /root/ros2_demo/install/setup.sh`. |

## ROS2 `topic list` Only Shows System Topics

| Item | Content |
|---|---|
| Symptom | `ros2 topic list` only shows `/parameter_events`, `/rosout`, or the graph result is inconsistent with the node log. |
| Check | First `source /root/ros2_demo/install/robobaton_ros2_env.bash`, then run `ros2 topic list --no-daemon --include-hidden-topics`; if needed run `/root/ros2_demo/install/robobaton_ros2_env.bash --restart-daemon`. |
| Normal result | `/robobaton/cam0/image_raw`, `/robobaton/cam0/image_raw/compressed`, `/robobaton/cam0/camera_info`, `/robobaton/imu/data`, etc. are visible. |
| Common causes | `ros2 daemon` started without loading this package's overlay or FastDDS SHM profile; `/dev/shm` not writable, insufficient space, or leftover abnormal FastDDS segments. |
| Recovery / info to collect | Reload via the environment script and restart the daemon; use `/root/ros2_demo/install/robobaton_ros2_env.bash --check` to view the profile and `/dev/shm`; run `--clean-shm` only after confirming the ROS2 node, launch, and run processes have all exited. |

## ROS2 raw NV12 Cannot Be Displayed Generally

| Item | Content |
|---|---|
| Symptom | `rqt_image_view`, `cv_bridge`, or RGB/BGR tools cannot display `/robobaton/cam0/image_raw` directly. |
| Check | `ros2 topic echo /robobaton/cam0/image_raw --once` to view `encoding`, `width`, `height`, `step`. |
| Normal result | `encoding` is `nv12`; `step` and `data.size()` keep the underlying stride/vstride alignment semantics. |
| Common causes | General tools interpret the raw topic with RGB/BGR or compact-NV12 assumptions. |
| Recovery / info to collect | Use `/robobaton/cam0/image_raw/compressed` for general visualization, or handle NV12 stride in your own program. |

## ROS2 Compressed Has No Messages

| Item | Content |
|---|---|
| Symptom | `/robobaton/cam0/image_raw/compressed` has no continuous messages. |
| Check | Confirm the node parameter `camera.publish_compressed_image:=true`; start `ros2 topic hz /robobaton/cam0/image_raw/compressed` to form a compressed subscriber. |
| Normal result | X5 media-codec hardware JPEG compression and JPEG payload publishing only occur when there is a compressed subscriber. |

| Common causes | Compressed publishing disabled, no subscriber, the node did not start the camera, or camera resources are held by another application. |
| Recovery / info to collect | Confirm parameters and subscribers; collect the launch command, topic list, and node logs. |

## ROS2 IMU Frequency Does Not Match Configuration

| Item | Content |
|---|---|
| Symptom | The statistics frequency of `/robobaton/imu/data` clearly deviates from the configured `25/50/100/200/500/1000/2000Hz` target. |
| Check | Use `ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor` and view the consecutive statistics windows after startup. |
| Normal result | The C++ monitor outputs `ROB2_IMU_RATE topic=/robobaton/imu/data hz=...` every second, with the stable value close to the configured target. |
| Common causes | YAML not applied, DDS receive-link sample loss, process resource contention, or still observing the first incomplete statistics window. |
| Recovery / info to collect | Confirm `imu.sample_rate_hz` is one of `25/50/100/200/500/1000/2000`; collect node parameters, consecutive monitor output, and process logs. |

## ROS2 Topic Has No Data or Resource Conflict

| Item | Content |
|---|---|
| Symptom | After the ROS2 node starts, raw/compressed/IMU topics have no data, or the camera fails to start. |
| Check | `pgrep -a cam-service`; `pgrep -af 'sensor_demo|cam_demo|robobaton_sensors_node' || true`; confirm only one camera application holds camera/VIO resources at a time. |
| Normal result | `cam-service` running; the old non-ROS demo or old ROS2 node has exited. |
| Common causes | Camera/VIO resources held by a non-ROS demo, an old ROS2 node, or a custom camera application. |
| Recovery / info to collect | Exit the old camera application normally and retry; do not stop `cam-service`; collect the process list and ROS2 node logs. |

## Camera Service or Resource Conflict

| Item | Content |
|---|---|
| Symptom | `sensor_demo` or `cam_demo` fails to start, no image on four channels, or a resource-busy prompt. |
| Check | `pgrep -a cam-service`; `pgrep -af 'sensor_demo|cam_demo' || true`. |
| Normal result | `cam-service` running; only one camera application holds camera/VIO/encoding resources at a time. |
| Common causes | Old camera application not exited, port occupied, or camera/VIO resources held by another program. |
| Recovery / info to collect | Exit the old application normally and retry; do not stop `cam-service`; collect the demo startup log and process list. |

## Single-Channel Camera Failure

| Item | Content |
|---|---|
| Symptom | Only a certain camera ID has no image or a single-sensor diagnostic fails. |
| Check | `./cam_demo --camera-id <0|1|2|3> --diagnostics`; pull the corresponding RTSP port from the host. Physical silkscreen mapping is CAM1 -> cam0, CAM2 -> cam1, CAM3 -> cam2, CAM4 -> cam3. |
| Normal result | The corresponding camera ID starts alone and streams on the matching port among `554/555/556/557`. |
| Common causes | The corresponding FPC, power, I2C, or MIPI/VIN link is abnormal. |
| Recovery / info to collect | Record the failed camera ID, port, and demo log. |

## Four-Channel RTSP Cannot Be Pulled

| Item | Content |
|---|---|
| Symptom | After four channels start, the client cannot open URLs like `rtsp://192.168.1.12:554/PRR` (adjust to the actual board address). |
| Check | `ffprobe -v error -rtsp_transport tcp ... rtsp://192.168.1.12:554/PRR`; confirm ports `554/555/556/557` and path `/PRR`. |
| Normal result | `codec_name=h264` or `codec_name=hevc`, `width=1280`, `height=1088`. |
| Common causes | Network port unreachable, wrong path, demo exited, or the port session held by another client. |
| Recovery / info to collect | Close excess clients and restart a single demo; collect the ffprobe output and on-device logs. |

## Save Output Incomplete or Cannot Be Extracted

| Item | Content |
|---|---|
| Symptom | After MP4/rosbag saving, there is no expected final output, or the offline extraction script rejects the input. |
| Check | View `SENSOR_MP4_RESULT` or `SENSOR_BAG_RESULT`; confirm `outcome`, `data_complete`, `path`, and `configured_path`. MP4 complete also requires `session_status.json`, `publication_receipt.json`, four MP4s, and four timestamp CSVs. |
| Normal result | A complete run exits `0`, `data_complete=yes`, and `path` is the real output. If the configured directory already exists, MP4 automatically writes to a sibling timestamped directory. |
| Common causes | The configured path already exists so output switched to a timestamped directory; the input is `.partial` recovery data; MP4 used H.265, non-four-channel, or frame-skip; the Host lacks a full `ffmpeg`/`ffprobe`. |
| Recovery / info to collect | Re-extract using the real directory from `SENSOR_MP4_RESULT path=`; `.partial` is recovery-only; collect the exit summary, session directory listing, and extraction-script error text. |

## H.265 Client Stuttering

| Item | Content |
|---|---|
| Symptom | `--codec h265` streams but playback stutters. |
| Check | Use `ffprobe` to confirm continuous `hevc` reception; observe fps and queue metrics in the on-device log. |
| Normal result | The device sends frames continuously and the client has H.265 hardware decode capability. |
| Common causes | Insufficient client software-decode/render throughput; four-channel H.265 may still exceed client capability. |
| Recovery / info to collect | Switch to a player with H.265 hardware decode, or drop from `30fps` to `25fps` and reduce the number of channels; collect client model, player, codec, and frame rate. |

## IMU Has No Data or Is Abnormal

| Item | Content |
|---|---|
| Symptom | `imu_reader_demo` has no output, fails to start, or reports nonzero timestamp duplicate/regression. |
| Check | `ls -l /dev/spidev2.0`; `./imu_reader_demo --sample-rate-hz 1000 --print-metrics`. |
| Normal result | Samples output continuously; `timestamp_duplicates=0`, `timestamp_regressions=0`. |
| Common causes | SPI device missing, IMU power/soldering/device-tree abnormal, or sample-rate parameter not in the supported list. |
| Recovery / info to collect | Collect the startup log, `SENSOR_IMU_RESULT` or demo exit summary, and `/dev/spidev2.0` state. |

## UART Has No Data

| Item | Content |
|---|---|
| Symptom | `serial_port_demo` sends or receives no data. |
| Check | `ls -l /dev/ttyS1 /dev/ttyS7`; verify interfaces only for UART1/UART7 per the formal harness/product pinout. Board TX to peer RX, board RX to peer TX, always common ground; both sides of UART1/UART7 TX/RX must be `3.3V` logic, and DEBUG_UART is not part of this demo path. |
| Software-example expectation | Device nodes exist and both sides agree on 8N1/raw/no-flow-control; `serial_port_demo` applies only to UART1/UART7, not DEBUG_UART. |
| Common causes | Wrong port, mismatched baud rate, TX/RX not crossed or miswired, or the peer not sending. |
| Recovery / info to collect | Collect port, baud, mode, the `3.3V` peer, and wiring direction; UART1/UART7 3.3V hardware communication passed V1 acceptance, `serial_port_demo` is a public user example and does not apply to DEBUG_UART. Do not connect `3.3V` or `5V` logic to DEBUG_UART; DEBUG_UART uses only a `1.8V` USB-UART adapter. |

## Resources Not Released After Exit

| Item | Content |
|---|---|
| Symptom | Restarting the camera or IMU demo fails. |
| Check | Confirm the previous demo exited normally with `Ctrl+C`; view `pgrep -af 'sensor_demo|cam_demo|imu_reader_demo'`. |
| Normal result | The old demo process does not exist and the new demo can start. |
| Common causes | The old process still runs, the terminal disconnected but the process did not exit, or an external program still holds the device. |
| Recovery / info to collect | End the old process normally and retry; if it still fails, collect the process list and full startup log. |
