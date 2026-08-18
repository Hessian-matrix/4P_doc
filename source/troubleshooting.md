# 故障排查

## SSH 无法连接

| 项目 | 内容 |
|---|---|
| 现象 | `ssh root@<x5-ip>` 超时或拒绝连接。 |
| 检查 | `ping <x5-ip>`；确认开发机和 X5 在同一网络；确认 SSH 服务由产品系统提供。 |
| 正常结果 | 能 ping 通，SSH 能进入板端 shell。 |
| 常见原因 | IP 配置错误、网线/交换机问题、目标板未启动完成、SSH 服务未就绪。 |
| 恢复/需收集信息 | 收集开发机 IP、X5 IP、网络拓扑、ping/ssh 错误文本。 |

## 运行包校验失败

| 项目 | 内容 |
|---|---|
| 现象 | `/root/demo.new` 中 `sha256sum -c manifest.sha256` 报失败或缺文件。 |
| 检查 | 开发机确认 `demo/manifest.sha256` 存在；重新上传到 `/root/demo.new` 后校验。 |
| 正常结果 | manifest 中所有文件均输出 `OK`。 |
| 常见原因 | 上传中断、只复制了部分文件、把外层 `demo/` 复制成 `/root/demo.new/demo/`。 |
| 恢复/需收集信息 | 删除 `/root/demo.new`，保留旧 `/root/demo`；收集失败文件名和上传命令。 |

## 找不到动态库

| 项目 | 内容 |
|---|---|
| 现象 | `error while loading shared libraries` 或运行到 `bin/` 程序时报 `.so` 缺失。 |
| 检查 | `ls -l /root/demo/lib`；从 `/root/demo` 顶层启动脚本运行；直接运行 `bin/` 前执行 `. ./env.sh`。 |
| 正常结果 | `libsc132.so*`、`libicm42688.so*`、`libprrtsp.so*` 存在，且优先从 `/root/demo/lib` 加载。 |
| 常见原因 | 只复制单个 ELF、漏复制 `lib/`、未加载 `env.sh`、混用了其他工程的同名 `.so`。 |
| 恢复/需收集信息 | 重新整包部署并提供 `ls -l /root/demo /root/demo/lib` 和完整错误文本。 |

## ROS2 构建找不到 `ament_package`

| 项目 | 内容 |
|---|---|
| 现象 | 交叉构建时报 `ModuleNotFoundError: No module named 'ament_package'`。 |
| 检查 | 在开发机执行 `source /opt/ros/humble/setup.bash` 后，再运行 `python3 -c 'import ament_package'`。 |
| 正常结果 | Python import 成功，`script/build_x5_ros2.sh --clean --cross-root <cross-root>` 可以进入 colcon/CMake 构建。 |
| 常见原因 | 只加载了 X5 目标侧交叉环境，没有加载宿主机 ROS Humble Python 环境。 |
| 恢复/需收集信息 | 重新 source 宿主机 ROS 环境；收集完整构建命令和错误文本。 |

## ROS2 setup 或动态库问题

| 项目 | 内容 |
|---|---|
| 现象 | `ros2 launch` 找不到包、节点启动时报 `.so` 缺失，或搬迁 install 后环境不正确。 |
| 检查 | 使用 Bash：`source /root/ros2_demo/install/robobaton_ros2_env.bash`；确认 `ls /root/ros2_demo/install/lib/robobaton_4p_ros2_demo`。 |
| 正常结果 | 能找到 `robobaton_ros2_env.bash`、`robobaton_sensors_node`、`robobaton_imu_rate_monitor`、`abi_manifest.sha256`、NV12 compressed 插件、`libicm42688.so*` 和 `libsc132.so*`。 |
| 常见原因 | 只上传了单个 ELF、没有上传完整 install、ROS2 underlay 路径不是默认 `/opt/ros/humble/setup.bash`、使用搬迁后的 POSIX `setup.sh` 但未设置 `COLCON_CURRENT_PREFIX`。 |
| 恢复/需收集信息 | 重新部署完整 `/root/ros2_demo/install`；非默认 underlay 用 `ROBOBATON_ROS_UNDERLAY=/path/to/setup.bash` 覆盖；确需 `sh` 时用 `COLCON_CURRENT_PREFIX=/root/ros2_demo/install . /root/ros2_demo/install/setup.sh`。 |

## ROS2 topic list 只看到系统话题

| 项目 | 内容 |
|---|---|
| 现象 | `ros2 topic list` 只看到 `/parameter_events`、`/rosout`，或 graph 结果与节点日志不一致。 |
| 检查 | 先 `source /root/ros2_demo/install/robobaton_ros2_env.bash`，再执行 `ros2 topic list --no-daemon --include-hidden-topics`；必要时执行 `/root/ros2_demo/install/robobaton_ros2_env.bash --restart-daemon`。 |
| 正常结果 | 能看到 `/robobaton/cam0/image_raw`、`/robobaton/cam0/image_raw/compressed`、`/robobaton/cam0/camera_info`、`/robobaton/imu/data` 等 topic。 |
| 常见原因 | `ros2 daemon` 在未加载本包 overlay 或 FastDDS SHM profile 时启动；`/dev/shm` 不可写、空间不足或残留异常 FastDDS segment。 |
| 恢复/需收集信息 | 使用环境脚本重新加载后重启 daemon；用 `/root/ros2_demo/install/robobaton_ros2_env.bash --check` 查看 profile 和 `/dev/shm`；只有确认 ROS2 节点、launch 和 run 进程都已退出后，才运行 `--clean-shm`。 |

## ROS2 raw NV12 无法通用显示

| 项目 | 内容 |
|---|---|
| 现象 | `rqt_image_view`、`cv_bridge` 或 RGB/BGR 工具不能直接显示 `/robobaton/cam0/image_raw`。 |
| 检查 | `ros2 topic echo /robobaton/cam0/image_raw --once` 查看 `encoding`、`width`、`height`、`step`。 |
| 正常结果 | `encoding` 为 `nv12`；`step` 和 `data.size()` 保留底层 stride/vstride 对齐语义。 |
| 常见原因 | 通用工具按 RGB/BGR 或紧凑 NV12 假设解释 raw topic。 |
| 恢复/需收集信息 | 使用 `/robobaton/cam0/image_raw/compressed` 做通用可视化，或在用户程序中按 NV12 stride 处理。 |

## ROS2 compressed 无消息

| 项目 | 内容 |
|---|---|
| 现象 | `/robobaton/cam0/image_raw/compressed` 没有持续消息。 |
| 检查 | 确认节点参数 `camera.publish_compressed_image:=true`；启动 `ros2 topic hz /robobaton/cam0/image_raw/compressed` 形成 compressed 订阅者。 |
| 正常结果 | 有 compressed 订阅者时才执行 X5 media-codec 硬件 JPEG 压缩并发布 JPEG payload。 |

| 常见原因 | compressed 发布关闭、没有订阅者、节点未启动相机、相机资源被其他应用占用。 |
| 恢复/需收集信息 | 确认参数和订阅者；收集 launch 命令、topic list、节点日志。 |

## ROS2 IMU 1000Hz CLI 低估

| 项目 | 内容 |
|---|---|
| 现象 | `ros2 topic hz /robobaton/imu/data` 显示明显低于 1000Hz。 |
| 检查 | 使用 `ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor`。 |
| 正常结果 | C++ monitor 每秒输出 `ROB2_IMU_RATE topic=/robobaton/imu/data hz=...`，稳定频率看启动后的连续多行。 |
| 常见原因 | Python `ros2 topic hz` 对 1000Hz `sensor_msgs/msg/Imu` 有消息构造、回调和统计开销。 |
| 恢复/需收集信息 | 用 C++ monitor 作为 IMU 频率检查工具；`ros2 topic hz` 仅作为低频 topic 快速诊断参考。 |

## ROS2 topic 无数据或资源冲突

| 项目 | 内容 |
|---|---|
| 现象 | ROS2 节点启动后 raw/compressed/IMU topic 无数据，或相机启动失败。 |
| 检查 | `pgrep -a cam-service`；`pgrep -af 'sensor_demo|cam_demo|robobaton_sensors_node' || true`；确认同一时间只有一个相机应用占用 camera/VIO 资源。 |
| 正常结果 | `cam-service` 运行；旧 non-ROS demo 或旧 ROS2 节点已退出。 |
| 常见原因 | 相机/VIO 资源被 non-ROS demo、旧 ROS2 节点或用户自研相机应用占用。 |
| 恢复/需收集信息 | 正常退出旧相机应用后重试；不要停止 `cam-service`；收集进程列表和 ROS2 节点日志。 |

## 相机服务或资源冲突

| 项目 | 内容 |
|---|---|
| 现象 | `sensor_demo` 或 `cam_demo` 启动失败、四路无图或提示资源忙。 |
| 检查 | `pgrep -a cam-service`；`pgrep -af 'sensor_demo|cam_demo' || true`。 |
| 正常结果 | `cam-service` 运行；同一时间只有一个相机应用占用 camera/VIO/编码资源。 |
| 常见原因 | 旧相机应用未退出、端口被占用、camera/VIO 资源被其他程序占用。 |
| 恢复/需收集信息 | 正常退出旧应用后重试；不要停止 `cam-service`；收集 demo 启动日志和进程列表。 |

## 单路相机失败

| 项目 | 内容 |
|---|---|
| 现象 | 只有某个 camera ID 无图或单颗诊断失败。 |
| 检查 | `./cam_demo --camera-id <0|1|2|3> --diagnostics`；开发机拉对应端口 RTSP。物理丝印映射为 CAM1 -> cam0、CAM2 -> cam1、CAM3 -> cam2、CAM4 -> cam3。 |
| 正常结果 | 对应 camera ID 单独启动并能在端口 `554/555/556/557` 中的对应端口出流。 |
| 常见原因 | 对应 FPC、供电、I2C、MIPI/VIN 链路异常。 |
| 恢复/需收集信息 | 记录失败 camera ID、端口、demo 日志。 |

## 四路 RTSP 无法拉流

| 项目 | 内容 |
|---|---|
| 现象 | 四路启动后客户端打不开 `rtsp://<x5-ip>:554/PRR` 等 URL。 |
| 检查 | `ffprobe -v error -rtsp_transport tcp ... rtsp://<x5-ip>:554/PRR`；确认端口 `554/555/556/557` 和 path `/PRR`。 |
| 正常结果 | `codec_name=h264` 或 `codec_name=hevc`，`width=1280`，`height=1088`。 |
| 常见原因 | 网络端口不可达、path 写错、demo 已退出、端口会话被其他客户端占用。 |
| 恢复/需收集信息 | 关闭多余客户端，重新启动单个 demo；收集 ffprobe 命令输出和板端日志。 |

## 保存输出不完整或无法提取

| 项目 | 内容 |
|---|---|
| 现象 | MP4/rosbag 保存后没有预期 final 输出，或离线提取脚本拒绝输入。 |
| 检查 | 查看 `SENSOR_MP4_RESULT` 或 `SENSOR_BAG_RESULT`；确认 `outcome`、`data_complete`、`path` 和 `configured_path`。MP4 complete 还需要 `session_status.json`、`publication_receipt.json`、四路 MP4 和四路 timestamp CSV。 |
| 正常结果 | complete 运行退出码为 `0`，`data_complete=yes`，且 `path` 是真实输出。若配置目录已存在，MP4 会自动写入同级时间戳目录。 |
| 常见原因 | 配置路径已存在导致输出切到时间戳目录；输入是 `.partial` recovery 数据；MP4 使用了 H.265、非四路或 frame-skip；Host 缺少完整 `ffmpeg`/`ffprobe`。 |
| 恢复/需收集信息 | 使用 `SENSOR_MP4_RESULT path=` 指向的真实目录重新提取；`.partial` 只作为 recovery 数据；收集退出摘要、session 目录文件列表和提取脚本错误文本。 |

## H.265 客户端卡顿

| 项目 | 内容 |
|---|---|
| 现象 | `--codec h265` 能出流但播放卡顿。 |
| 检查 | 用 `ffprobe` 确认能持续接收 `hevc`；观察板端日志中的 fps 和队列指标。 |
| 正常结果 | 板端持续送帧，客户端具备 H.265 硬件解码能力。 |
| 常见原因 | 客户端软件解码或渲染吞吐不足；四路`1280x1088@60fps`高吞吐配置对客户端能力要求较高，但该配置本身不是全局stress-only。 |
| 恢复/需收集信息 | 更换支持 H.265 硬解的播放器，或回到 V1 稳定的 `25/30/40/50fps` 配置并减少播放路数；收集客户端型号、播放器、codec 和帧率。 |

## IMU 无数据或异常

| 项目 | 内容 |
|---|---|
| 现象 | `imu_reader_demo` 无输出、启动失败或 timestamp duplicate/regression 非零。 |
| 检查 | `ls -l /dev/spidev2.0`；`./imu_reader_demo --sample-rate-hz 1000 --print-metrics`。 |
| 正常结果 | 能持续输出样本；`timestamp_duplicates=0`、`timestamp_regressions=0`。 |
| 常见原因 | SPI 设备不存在、IMU 供电/焊接/设备树异常、采样率参数不在支持列表。 |
| 恢复/需收集信息 | 收集启动日志、`SENSOR_IMU_RESULT` 或 demo 退出摘要、`/dev/spidev2.0` 状态。 |

## UART 无数据

| 项目 | 内容 |
|---|---|
| 现象 | `serial_port_demo` 发送或接收无数据。 |
| 检查 | `ls -l /dev/ttyS1 /dev/ttyS7`；按公开板卡顶视图核对 UART1/UART7接口位置。板端 TX 接适配器 RX，板端 RX 接适配器 TX，并始终共地；双方 TX/RX 必须为 `3.3V` 逻辑。 |
| 软件示例预期 | 设备节点存在，双方 8N1/raw/no-flow-control 参数一致；`serial_port_demo` 只适用于 UART1/UART7，不适用于 DEBUG_UART。 |
| 常见原因 | 端口选错、波特率不一致、TX/RX 未交叉或接线错误、对端未发送。 |
| 恢复/需收集信息 | 收集端口、baud、mode、`3.3V` 对端和接线方向；UART1/UART7 3.3V 硬件通信已通过 V1 验收，`serial_port_demo` 是公开用户示例且不适用于 DEBUG_UART。禁止把 `3.3V` 或 `5V` 逻辑接到 DEBUG_UART；DEBUG_UART 仅使用 `1.8V` USB-UART 适配器。 |

## 退出后资源未释放

| 项目 | 内容 |
|---|---|
| 现象 | 重新启动相机或 IMU demo 失败。 |
| 检查 | 确认前一个 demo 已通过 `Ctrl+C` 正常退出；查看 `pgrep -af 'sensor_demo|cam_demo|imu_reader_demo'`。 |
| 正常结果 | 旧 demo 进程不存在，新 demo 可启动。 |
| 常见原因 | 旧进程仍在运行、终端断开但进程未退出、外部程序仍占用设备。 |
| 恢复/需收集信息 | 正常结束旧进程后重试；如仍失败，收集进程列表和完整启动日志。 |
