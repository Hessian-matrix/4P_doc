# 故障排查

## 局域网预览无画面或 IMU 失效

| 项目 | 内容 |
|---|---|
| 现象 | `sensor_demo` 运行，但页面打不开、单路等待关键帧、视频停顿或六轴显示失效。 |
| 检查 | 确认当前运行包包含匹配的 `bin/sensor_web` 与 SO；检查有效 `web.enabled`、`rtsp.enabled`、H.264 配置、应用日志中的 `web=degraded` 及源采集错误。确认 HTTP TCP 80（或显式端口）与媒体 UDP/TCP 8189 均可达；检查端口 owner，勿终止其他服务。 |
| 正常结果 | 默认仅 Web 开启，四路解码帧数持续增加；IMU 新值持续到达。RTSP 关闭时没有其 listener，网页不依赖 RTSP。 |
| 常见原因 | 混用旧工件、80/8189 冲突、跨网段/防火墙、H.265 不受 Web 支持、浏览器不支持真实 H.264 profile/level、源启动失败或遥测超过 500ms 未更新。 |
| 恢复/需收集信息 | 整包校验后部署；有端口冲突时显式配置备用端口，不抢占。提供版本、有效配置、源/Web 日志、浏览器版本、逐路 decoded/lost/decoder 及网络信息。`decoder: unknown` 只表示诊断未提供，不证明软解或硬解失败。匿名 HTTP 仅用于可信 LAN；不开放公网来排障。 |

### 手机连接热点后出现 `invalid host or query`

在板端执行 `ip -4 addr show wlan0`，手机浏览器直接输入 `http://<AP地址>/`，不要附加 `?` 查询参数或使用自定义域名。确认有效 `web.listen_address` 为 `0.0.0.0` 或当前 AP 地址。当前实现不缓存启动时的地址列表；AP 后就绪时，HTTP 和新建 WebRTC 会话使用当前地址。若运行包仍有启动时地址缓存，按部署流程更新完整匹配包并正常重启应用，单纯重启系统可能重复启动时序，不能视为修复。保留 Host/Origin 校验，不以开放跨域或关闭安全校验排障。

### Windows 视频彩色竖条，但 decoded 仍增加

旧 H.264 producer 可能声明 Main 却保留 SDK 默认的 High-only 8×8 transform；部分硬解器会持续输出错误画面，即使 lost 为零。当前 producer 显式关闭该功能，H.265 不受此修改影响。校验并更新完整运行包后正常重启 `sensor_demo`，再刷新网页；只换网页资源无法修复正在运行的编码器。可在独立浏览器进程临时禁用加速视频解码作对照，但这不是正式修复，也不要据此关闭所有用户浏览器。收集实际截图、浏览器/系统/驱动版本及源 SPS/PPS；当前 SDK 仍可能输出取值为零的 PPS 扩展字段，不承诺严格 Main 语法合规或全部硬解器兼容。

### 关闭网页后 Web 进程内存仍未归零

RSS 包含存活对象、栈和分配器保留页，不等于泄漏字节；关闭网页也不停止应用或录制。当前源码已将旧 Zig 分配器改为静态 musl `1.2.5` / mallocng，允许空闲分配组归还内核，但不保证 RSS 归零或完全回到启动值。使用匹配工具链重建并验证完整运行包，再按[部署与回滚](development/deployment-and-upgrade.md)正常更新应用；刷新网页不会更换运行中的分配器，不要用周期性重启掩盖增长或中断正在收尾的录制。

若同一负载下仍持续增长，收集软件版本、manifest、应用启动时间、网页数量、视频配置、传输方式及一段连续的 RSS/PSS、线程数和 fd 数；标明网页打开/关闭及重连时刻。比较同龄进程和相同负载，不把重启后的绝对下降或跨重连的负斜率当作长期无泄漏证明。此内存修复也不保证所有采集异常已解决；采集退出须另行保留完整错误并排查，不通过停止 `cam-service` 规避。


## SSH 无法连接

| 项目 | 内容 |
|---|---|
| 现象 | `ssh root@192.168.1.12`（按实际板卡地址修改）超时或拒绝连接。 |
| 检查 | `ping 192.168.1.12`（按实际板卡地址修改）；确认开发机和 X5 在同一网络；确认 SSH 服务由产品系统提供。 |
| 正常结果 | 能 ping 通，SSH 能进入板端 shell。 |
| 常见原因 | IP 配置错误、网线/交换机问题、目标板未启动完成、SSH 服务未就绪。 |
| 恢复/需收集信息 | 收集开发机 IP、X5 IP、网络拓扑、ping/ssh 错误文本。 |

## 板载 Wi-Fi 配置失败

完整镜像集成、交互配置和日志路径见 [板载 Wi-Fi 配置](getting-started/wifi-configuration.md)。

| 项目 | 内容 |
|---|---|
| 现象 | `wifi_setup` 提示缺少命令、扫描不到 SSID、认证失败、DHCP 失败、AP 无法启动，或开机后没有恢复 Wi-Fi。 |
| 检查 | 使用有线网络或 `1.8V` DEBUG_UART 登录；执行 `wifi_setup --status`；检查 `ip link show wlan0`、`iw dev wlan0 info`、`/run/4p-wifi/logs/` 和 `/run/4p-wifi/boot.log`。 |
| 正常结果 | AP 模式显示 hostapd `ENABLED`，客户端能获得配置网段地址；STA 模式显示已关联并获得 DHCP 地址；启用开机恢复时 `/etc/4p/wifi/autostart.enabled` 和 `current.conf` 存在。 |
| 常见原因 | Wi-Fi 用户态工具缺失、天线或信号问题、SSID/密码错误、隐藏 SSID、路由器 DHCP 异常、AP 信道/IP/DHCP 网段配置错误，专用入口早于驱动就绪，或系统分区只读导致配置无法保存。 |
| 恢复/需收集信息 | 不要在同一条 Wi-Fi SSH 会话中切换模式；通过有线入口重新配置。需要停用时执行 `wifi_setup --disable`；收集脚本完整错误、接口状态和去除凭据后的日志。 |

## 运行包校验失败

| 项目 | 内容 |
|---|---|
| 现象 | 本次部署生成的唯一临时目录 `${REMOTE_NEW}` 中 `sha256sum -c manifest.sha256` 报失败或缺文件。 |
| 检查 | 以部署命令中本次 `RUN_ID` 计算出的 `${REMOTE_NEW}` 为准；确认开发机 `demo/manifest.sha256` 存在并重新上传到同一个临时目录后校验。 |
| 正常结果 | manifest 中所有文件均输出 `OK`。 |
| 常见原因 | 上传中断、只复制了部分文件、把外层 `demo/` 复制成 `${REMOTE_NEW}/demo/`。 |
| 恢复/需收集信息 | 只删除本次部署对应的 `${REMOTE_NEW}`，保留旧 `/root/demo`；收集失败文件名、`RUN_ID` 和上传命令。 |

## 找不到动态库

| 项目 | 内容 |
|---|---|
| 现象 | `error while loading shared libraries` 或运行到 `bin/` 程序时报 `.so` 缺失。 |
| 检查 | `ls -l /root/demo/lib`；从 `/root/demo` 顶层启动脚本运行；直接运行 `bin/` 前执行 `. ./env.sh`。 |
| 正常结果 | `libsc132.so*`、`libicm42670.so*`、`libprrtsp.so*` 优先从 `/root/demo/lib` 加载；ICM 为 SONAME `libicm42670.so.6`、实体 `libicm42670.so.6.0.0`、九个 `ICM42670_X5_6.0` 导出及成套重建 consumer，无旧 `.2/.3/.4/.5` 库或跨 major 链接。 |
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
| 正常结果 | 能找到 `robobaton_ros2_env.bash`、`robobaton_sensors_node`、`robobaton_imu_rate_monitor`、`abi_manifest.sha256`、NV12 compressed 插件、`libicm42670.so*` 和 `libsc132.so*`。 |
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

## ROS2 IMU 频率与配置不符

| 项目 | 内容 |
|---|---|
| 现象 | `/robobaton/imu/data` 的统计频率明显偏离配置的原生 `25/50/100/200/400/800/1600Hz` 目标（默认 `800Hz`）。 |
| 检查 | 使用`ros2 run robobaton_4p_ros2_demo robobaton_imu_rate_monitor`并查看启动后的连续统计窗口。 |
| 正常结果 | C++ monitor每秒输出`ROB2_IMU_RATE topic=/robobaton/imu/data hz=...`，稳定值接近配置目标。 |
| 常见原因 | YAML未生效、DDS接收链路丢样、进程资源争用或仍在观察首个不完整统计窗口。 |
| 恢复/需收集信息 | 确认 `imu.sample_rate_hz` 为 `25/50/100/200/400/800/1600` 中之一；其他值会被拒绝。收集 node 参数、连续 monitor 输出和进程日志。 |

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
| 检查 | `./cam_demo --camera-id <0|1|2|3> --diagnostics`；开发机拉对应端口 RTSP。CAM1..CAM4 依次对应软件 cam0..cam3。 |
| 正常结果 | 对应 camera ID 单独启动并能在端口 `554/555/556/557` 中的对应端口出流。 |
| 常见原因 | 对应 FPC、供电、I2C、MIPI/VIN 链路异常。 |
| 恢复/需收集信息 | 记录失败 camera ID、端口、demo 日志。 |

## 四路 RTSP 无法拉流

| 项目 | 内容 |
|---|---|
| 现象 | 四路启动后客户端打不开 `rtsp://192.168.1.12:554/PRR`（按实际板卡地址修改）等 URL。 |
| 检查 | `ffprobe -v error -rtsp_transport tcp ... rtsp://192.168.1.12:554/PRR`；确认端口 `554/555/556/557` 和 path `/PRR`。 |
| 正常结果 | `codec_name=h264` 或 `codec_name=hevc`，`width=1280`，`height=1088`。 |
| 常见原因 | 网络端口不可达、path 写错、demo 已退出、端口会话被其他客户端占用。 |
| 恢复/需收集信息 | 关闭多余客户端，重新启动单个 demo；收集 ffprobe 命令输出和板端日志。 |

## 保存输出不完整或无法提取

| 项目 | 内容 |
|---|---|
| 现象 | MP4/rosbag 保存后没有预期 final 输出，或离线提取脚本拒绝输入。 |
| 检查 | 查看 `SENSOR_MP4_RESULT` 或 `SENSOR_BAG_RESULT`；确认 `outcome`、`data_complete`、`path` 和 `configured_path`。MP4 complete 还需要 `session_status.json`、`publication_receipt.json`、四路 MP4 和四路 timestamp CSV。 |
| 正常结果 | complete 运行退出码为 `0`，`data_complete=yes`，且 `path` 是真实输出。若配置目录已存在，MP4 会自动写入同级时间戳目录。 |
| 常见原因 | 路径冲突切到时间戳目录；`.partial` recovery 数据；编码/队列/存储丢帧、最终 IMU 无效 payload 丢弃或 IIO 证据／停止错误；MP4 使用 H.265、非四路或 frame-skip；Host 缺少完整 `ffmpeg`/`ffprobe`。四路 MP4 能播放不代表 final health 满足 complete；详见[数据保存](usage/save-data-guide.md)。 |
| 恢复/需收集信息 | 使用 `SENSOR_MP4_RESULT path=` 指向的真实目录重新提取；`.partial` 只作为 recovery 数据；收集退出摘要、session 目录文件列表和提取脚本错误文本。 |

## H.265 客户端卡顿

| 项目 | 内容 |
|---|---|
| 现象 | `--codec h265` 能出流但播放卡顿。 |
| 检查 | 用 `ffprobe` 确认能持续接收 `hevc`；观察板端日志中的 fps 和队列指标。 |
| 正常结果 | 板端持续送帧，客户端具备 H.265 硬件解码能力。 |
| 常见原因 | 客户端软件解码或渲染吞吐不足；四路H.265仍可能超过客户端能力。 |
| 恢复/需收集信息 | 更换支持H.265硬解的播放器，或从`30fps`降到`25fps`并减少播放路数；收集客户端型号、播放器、codec 和帧率。 |

## 相机缺少有界 LPWM 映射

`missing bounded LPWM clock mapping; fail closed` 表示正式交付帧未取得有效触发时间，不使用到帧时间或最近邻代替。`reason=exact_record_rejected` 表示精确触发已记录但未通过有界重建；保留 `record_vsync_ticks`、`record_trigger_ticks`、`lower_raw_ns`、`upper_raw_ns`，检查计数器关系及 `500000ns` 采样窗口上限。`reason=not_retained` 只说明查找时历史中没有该触发，不能仅凭历史已满断言覆盖；请求等于 `last_overwritten_trigger_ns` 才证明最近一次覆盖了该身份。收集整行日志、启动配置和系统调度状态，不放宽窗口或把此诊断当作稳定性修复。

上述有界映射诊断适用于 `camera_timestamp_path=observer`，`500µs` admission 不变。`official` 绝不启动 SIF observer；`invalid official same-frame timestamp` 表示同帧 IRQ RAW/AON 元数据或算术非法。保留所选模式与完整 reason 行，不用到帧时间替代，也不自动换模式恢复。official 即使算术成功仍为 timing validity0、uncertainty `UINT32_MAX`，不是物理有界结果。

selector 非法或只读参数错误时，使用准确的顶层 `camera_timestamp_path: observer|official` 与 `imu_timestamp_mode: host|tmst`（默认 observer/host）、CLI `--camera-timestamp-path`/`--imu-timestamp-mode`，或 ROS2 同名顶层参数。切换须停止/重启，ROS2 不能用 `ros2 param set` 热切换。四组合均为同一二进制/IIO owner，不是另一套 SPI 后端。见 [non-ROS 使用](usage/non-ros-demo.md) 与 [ROS2 使用](usage/ros2-demo.md)。

## IMU 无数据或异常

| 项目 | 内容 |
|---|---|
| 检查 | 运行 `./imu_reader_demo --sample-rate-hz 800 --count 800 --print-metrics --imu-timestamp-mode host`（停止后也可选 `tmst`）；核对 ABI6 头文件/库、匹配内核 IIO V4 capture 模块，以及唯一 `icm42670-capture` sysfs/控制身份。现有 V2/V3 模块两模式均不兼容，不硬编码编号。 |
| 正常合同 | 两模式均分开保留 MONOTONIC 主机估计和 RAW burst 观测。host 的 `sample_raw_ns=0`、uncertainty `UINT32_MAX`；tmst 增加 RAW sample 映射，不替代 MONOTONIC。count 为 STOP 阈值，最终数量可更大；独立 CLI 不转 Unix 时间。 |
| 常见原因 | V4 模块/设备树缺失或不匹配、身份歧义、scan 布局不符、其他 owner 占用、调度权限、内核 I/O/overflow/push/evidence/quiesce 错误，或 TMST FIFO/UI 时间证据非法。库不加载模块、不抢资源、不使用 spidev、不回退到 host；部署应用不升级模块。 |
| 需保留信息 | 完整启动/退出日志、stop返回值、`IMU_TIMING_SUMMARY`、最终`IMU_RUNTIME_HEALTH`和实际序号/载荷；stop失败仍读取终态诊断。检查record/ACK与transport_complete，不把物理尾部排除解释为所有物理采样已交付。 |

`timestamp_hz`是主机赋时统计，`acquisition_hz`来自普通burst的独立RAW端点且需`acquisition_valid=yes`；二者不证明物理精度。不要跨MONOTONIC/RAW作差。保存/ROS2输出桥失败会令输出失败，不能扩大括号或合成递增值掩盖错误。参考[IMU数据合同](development/data-contracts.md#imu)。

TMST 证据缺失、矛盾、过期、歧义或超预算均失败，`200µs` 计算 admission 不是物理精度，不得扩大门限掩盖失败。保存/ROS2 使用 host MONOTONIC→REALTIME 或 tmst RAW→REALTIME；核对 `bridge_clock`、独立 `bridge_monotonic_ns`/`bridge_raw_ns` 和 schema `robobaton_imu_timing_v3`。不恢复 FSYNC 关联。当前 non-ROS HO 短窗证据及未验收范围见{ref}`能力与验证边界 <capability-verification-boundary>`。

## 曝光观测不可用

从 bag frame metadata、MP4 `exposure.jsonl` 或 ROS2 `/robobaton/camN/exposure` 读取。曝光按采集原始硬件帧 N 的 getter→相邻 N+1 估计，允许 uint32 回绕，不按归一化组号或 SDK 源帧号匹配。首个无前驱采集帧、硬件帧号缺口或无效前驱查询均为 `status=0` 且全零，不跨缺口延用；N 查询失败使 N+1 不可用，有效前驱仍可估计 N。各 worker 会话状态清零，frame-set warmup 即预热，不增加图像缓冲或交付延迟；关闭 warmup 不会生成前驱。默认触发 stamp 和图像交付不变，显式中点使用匹配估计、不可用时仍停止，不回退。`status=1` 不证明实际生效曝光、真实中点或已测物理误差上界；来源字段是更早 getter 的原值，不要改为目标图像或在消费端再移一帧。按相机/组交付时间核对输入和编码帧，不按 sidecar 行号或源帧号作为 MP4 索引。当前软件没有 FSYNC 关联选项、topic 或 sidecar。详见[逐帧曝光观测](development/data-contracts.md#逐帧曝光观测)。

固定 N→N+1 不等于通用 AE 生效延迟；真实 AE 的有效滞后可能不同，不能用这项估计保证逐帧实际应用曝光或判断 AE 已验收。

## UART 无数据

| 项目 | 内容 |
|---|---|
| 现象 | `serial_port_demo` 发送或接收无数据。 |
| 检查 | `ls -l /dev/ttyS1 /dev/ttyS7`；UART1/UART7 为 `3.3V`，DEBUG_UART 为 `1.8V`。UART1 为 CN1 4pin，UART7 为 CN2 5pin；对照{ref}`接口接线示意图 <wiring-diagram>`核实线序、对端电平和共地后断电接线，不凭插头左右位置猜测针序。 |
| 软件示例预期 | 设备节点存在，双方 8N1/raw/no-flow-control 参数一致；`serial_port_demo` 只适用于 UART1/UART7，不适用于 DEBUG_UART。 |
| 常见原因 | 端口选错、波特率不一致、TX/RX 未交叉或接线错误、对端未发送。 |
| 恢复/需收集信息 | 收集设备节点、baud、mode 和已核实的接线方向；供电脚额定值和热插拔条件待确认，不接适配器 VCC，不反灌。`serial_port_demo` 仅用于普通用户 UART，不用于 DEBUG_UART。 |

## 退出后资源未释放

| 项目 | 内容 |
|---|---|
| 现象 | 重新启动相机或 IMU demo 失败。 |
| 检查 | 确认前一个 demo 已通过 `Ctrl+C` 正常退出；查看 `pgrep -af 'sensor_demo|cam_demo|imu_reader_demo'`。 |
| 正常结果 | 旧 demo 进程不存在，新 demo 可启动。 |
| 常见原因 | 旧进程仍在运行、终端断开但进程未退出、外部程序仍占用设备。 |
| 恢复/需收集信息 | 正常结束旧进程后重试；如仍失败，收集进程列表和完整启动日志。 |
