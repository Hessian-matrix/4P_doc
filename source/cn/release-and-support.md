# 发布、授权与支持

本页记录公开交付物的发布状态、用户会遇到的已知限制、授权和问题反馈信息。

## 文档版本政策

本文是整套公开文档的统一版本定义；[版本更新记录](changelog.md) 按此政策记录用户可见更新。

- 文档版本采用“主版本.次版本.修订号”。末位修订号表示同一版本系列内的小 bug 修复、构建脚本调整或文档内容修正，不自动改变各软件版本号。
- `4P_doc/VERSION` 是文档修订号的唯一来源；中英文 Sphinx 配置直接读取它。修订时同步两棵树的最新版本化 changelog 条目和本页版本信息。
- 主仓、non-ROS、ROS2 的软件版本仍以各自 `VERSION`、ROS2 `package.xml`、包版本和 `--version` 输出为准。文档修订不得联动修改这些版本，也不要求文档版本与软件版本相等。
- SO 的 SONAME/ABI 独立于文档和软件版本，例如 `libicm42670.so.5` 中的 `5` 表示 ABI major；real SO `5.0.0` 与产品 `--version` 也是不同标识。文档修订不表示软件重新发布或板端已更新。


| 库 | 实体文件 | SONAME | 符号节点 |
|---|---|---|---|
| ICM42670 | `libicm42670.so.5.0.0` | `libicm42670.so.5` | `ICM42670_X5_5.0` |
| SC132 | `libsc132.so.3.0.0` | `libsc132.so.3` | `LIBSC132_3.0` |
| PRRTSP | `libprrtsp.so.2.0.1` | `libprrtsp.so.2` | `LIBPRRTSP_2.0` |

实体库修订标识实现；SONAME major 标识可替换的公开合同；符号节点区分兼容扩展与不兼容切换，不与产品代号机械同步。SC132 当前 ABI 为 3.0：consumer 必须按当前头文件的时间域、触发模式及 frame-info 语义成套重建，禁止 `.so.2 -> .so.3` 链接。ROS2 只包含 ICM42670 和 SC132。

当前 IMU 使用内核 IIO 公共 ABI 5.0，九个导出使用表中符号节点。全部 consumer 与匹配头文件/库成套重建，清除旧 major，不做 shim。设备必须已绑定匹配的 **内核 IIO V3 capture 模块**；现有 V2 即使 host 模式也不兼容，应用包不升级模块。启动 `camera_timestamp_path=observer|official`（默认 observer）与 `imu_timestamp_mode=host|tmst`（默认 host）提供四组合，共用相同二进制和 IIO 读取/owner，停止/重启后切换。host 保留 MONOTONIC，无物理上界；tmst 依据内核 FIFO/UI 证据增加有界仿射 RAW 映射，同时保留原生 host/burst 值。保存/ROS2 将所选原生模式桥接到 realtime，RAW/MONOTONIC 桥字段独立，timing schema 为 v2。无用户态 SPI/spidev、FSYNC 恢复或自动回退。official 相机时间绝不使用 SIF observer，物理误差未知（validity0/uncertainty `UINT32_MAX`）；observer `500µs` admission 不变。见[数据合同](development/data-contracts.md)、[non-ROS 使用](usage/non-ros-demo.md) 与 [ROS2 使用](usage/ros2-demo.md)。

## 版本集合

| 项目 | 当前版本 | 状态 |
|---|---|---|
| 文档修订 | `2.0.81` | 本站持续更新；修订内容见 [版本更新记录](changelog.md)，不表示软件版本升级。 |
| non-ROS demo/运行包 | `v2.0.0` | 默认安装位置为 `/root/demo`，按 `manifest.sha256` 整包校验；不表示目标板已安装当前源码对应工件。 |
| ROS2 package/install | `v2.0.0` | 默认安装位置为 `/root/ros2_demo/install`，包名 `robobaton_4p_ros2_demo`。源码更新或本地重编译不等于目标板已安装修订或正式升级；目标板实际安装版本须核对 manifest 与所加载库。使用前应按 [ROS2 Demo 使用](usage/ros2-demo.md)、[non-ROS Demo 使用](usage/non-ros-demo.md) 和 [保存数据](usage/save-data-guide.md) 完成对应路径的实际检查。 |
| 系统镜像包 | `V2.0.0` | [4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz)；烧录步骤、校验值与硬件匹配要求见[系统烧录](ops/system-flashing.md)。 |

功能新增、修复和兼容性变化见 [版本更新记录](changelog.md)。

V2 源码和文档仓库统一使用 `V2_main` 主分支，仓库浏览、源码链接和 clone 示例均显式选择该分支；分支名不代替版本、manifest 或兼容性检查。远端链接须在分支及修订推送后才可访问，Read the Docs 构建配置独立管理。

在线文档会根据用户反馈继续更新；当前没有单独固定的 `stable` 文档版本。文档修订号按上述政策识别，Read the Docs 的 `latest` 是部署标识，不是软件版本。软件正式发布不等同于跳过目标板运行检查。相机参数集合公开支持 `25/30/40/50/60fps`，默认 `30fps`；保存和 ROS2 路径应以实际结果、退出码、manifest 和目标板环境检查判定。

当前使用指南覆盖标识为 `2.0.0` 的 V2 软件及 changelog 中明确列出的未发布源码更新；同一个版本字符串不证明工件组成相同，应核对运行包 manifest、实际链接库和对应说明。ICM-42670-P 头文件、库、consumer 与配置必须成套匹配。ICM 原生 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；不支持的速率明确拒绝，不静默重采样。文档修订不代表实板或整机验收。

硬件标识、软件 `2.0.0`、文档修订及各 SO ABI 是独立维度；不能互相代替兼容性或验收结论。本次只同步文档，不改变软件行为或发布状态。

UVC 源码、独立构建、USB 管理与离线安装工具统一在 non-ROS Demo 的 `scripts/env_setup/x5_usb/`，命令及更新边界见{ref}`USB 开发修改入口 <usb-uvc-development>`。新增在线源码链接须随对应 Demo 修订发布才可访问；源码移动和安装 CLI 调整不新增运行功能、软件版本或 ABI，也不代表板端已部署或完成验收。

## 当前实现能力

以下是当前公开源码接受的参数和输出合同，不是所有模式、负载和时长组合都已通过验收。

| 路径 | 当前能力 | 约束 |
|---|---|---|
| 相机 | `25/30/40/50/60fps`，默认 `30fps`；NV12 native `1280x1088`，离散 VSE `640x480`/`720x480`/`1280x720` | 仅完整四路或单颗诊断，不支持 2/3 路；旋转 `180` 仅 `30fps`。所有入口仅 `vin_lpwm`。 |
| IMU | 原生 `25/50/100/200/400/800/1600Hz`，默认800Hz；host/tmst 启动 selector | 同一 IIO V3 采集，两模式均保留 MONOTONIC 主机证据，tmst 增加 RAW sample 映射；watermark1，buffer 默认4096且为256..8192的2次幂；库/独立 demo 不转 realtime。 |
| non-ROS | 四路 H.264/H.265 RTSP，可同时选择 ROS1 bag 或 H.264 MP4 保存 | bag 与 MP4 互斥；MP4 仅 H.264、完整四路。独立 UART/CAN 示例不代表外设和整机负载已验收。 |
| ROS2 | raw/compressed Image、CameraInfo、曝光观测、IMU、温度及IMU 时钟元数据 | 无 RTSP、TF 或标定；发布成功不等于 DDS 实际收到。 |
| 曝光/时钟元数据 | 相机为最新 ISP 曝光估计；IMU 输出保存原生时钟和桥证据 | 曝光不是实际生效帧保证，桥半宽不是物理精度；不提供触发—样本关联。 |

相机 `observer` 线程使用 `SCHED_FIFO/60`（`official` 不启动该线程），IMU owner 为 `SCHED_FIFO/20`，non-ROS consumer/ROS2 发布为 `SCHED_RR/3`；调度失败拒绝启动，不自动调整 IRQ/debug/实时配额。observer 保留 `500µs` 捕获窗口 admission；official 物理误差未知。host 无物理误差上界；tmst `200µs` 计算样本映射 admission 与输出桥括号均不是物理精度。见[数据合同](development/data-contracts.md)。

(capability-verification-boundary)=
## 能力与验证边界

| 项目 | 当前结论与用户限制 |
|---|---|
| 高帧率 | 参数支持不承诺所有保存、推流和 ROS2 组合的持续吞吐。历史 non-ROS `60fps` + `1600Hz` FSYNC 在 CPU/BPU 负载下约 `300s` 的控制台关联仅认证原组成的关联观察，不证明保存解码、ROS2 吞吐或新 IIO 组成无损；当前不提供 FSYNC。 |
| bag 压力与丢组 | 默认最小丢组间隔 `10`，按连续 `source_group_order` 而非 producer `group_id` 计距；只淘汰已编码、未被 writer 领取的完整四路组，已领取组受保护。无合法旧组或新组可丢时停止，排空为可读 partial 并非零退出。主动隔组保存需显式设为 `2`。历史高 CPU/存储压力下策略耗尽、未达到 `300s` 的失败保留原边界。录制到 eMMC／TF 时尽量只保留 bag 或 MP4 一个大吞吐写盘任务，避免额外存储写压；这降低竞争风险，不保证持续无丢失。任何丢组均为 `data_complete=false`，见{ref}`数据保存 <persistence-fps-boundary>`。 |
| 启动自动 MP4 提前停录 | [INFERENCE] 当前源码中，网页提前停止 CLI/YAML 启动自动 MP4 时缺少最终 producer health，不能按 complete 发布；网页固定 `health_scope` 标签也不证明接管会话健康范围。未在本轮修复或实板复现。网页动态会话与保留至正常退出的启动自动会话分开判断，见{ref}`保存限制 <startup-mp4-web-stop>`。 |
| 样本完整性 | 已修复历史提前关闭 IMU 接纳及 ROS2 正常退出顺序缺陷；当前 STOP 期间保持接纳并排空，核对最终 generation、fatal、scan、record/ACK、停止返回值及实际载荷。`transport_complete` 只认证停止集合，不覆盖物理尾部。历史 DDS 差额的精确身份/原因仍不可恢复，短窗计数相等或保存序列连续不证明所有硬件样本已保存。`allow-counted` 只允许计数无效六轴 payload，`strict` 遇此失败，均不保证任意负载零丢失。 |
| ROS2 速率与 SHM | 历史 `30fps`/`1600Hz` 短窗 producer/sink/DDS 数量相等不认证当前组成，也不替代历史差额根因证明或所有路径持续 `60fps` 验收。SHM 每 participant `256 MiB` 是容量预算，不是初始化根因修复或任意负载保证。metrics 关闭表示不可用；开启只统计 sink 的 `publish()` 正常返回，不确认 DDS 接收。 |
| 长时间录制 | 本轮未提供最终集成组成的长录或全部压力模式验收。旧 FSYNC/`8h` 结果不能认证当前 IIO 组成；持续能力仍需在单一录制写盘任务条件下核验，不以额外存储写压为前置。 |
| 时间戳 selector 与短窗验证 | 最终默认 HO（相机 observer + IMU host），另外三种启动组合保留比较。匹配 IIO V3／ABI5 整合包的 non-ROS HO 在四路30fps／IMU800Hz下完成 Web 预览与姿态、bag／MP4 动态录制、完整载荷回读与正常停止短窗验证；不认证其余三组合、ROS2 板端、物理精度、压力、长录或重启。示例和历史证据不扩大此范围。 |
| 捕获和启动 | 所选相机路径失败即停止，不回退；observer 的 LPWM `500µs` 长尾停止问题不因 IIO 迁移而关闭。IIO 要求匹配 V3 模块（V2 不兼容）、唯一设备及合法 scan/控制身份。overflow、push/evidence、I/O、quiesce、时间证据与 fatal 不得用成功前缀掩盖。旧用户态 FSYNC/Arm 特殊分支仅为历史，不定义当前启动合同。 |
| 编码 | 原生 bag JPEG 去除私有 JPU APP9，不改变 ROS2 JPEG 插件。bag JPEG 解码正常不关闭 H.264 RTSP `60fps` 的 missing-reference/slice 告警问题。 |
| USB/CAN | 配套新 V2 Buildroot 镜像候选集成 USB3 Host/Device 切换与 CDC NCM、RNDIS、CDC ECM、四目 UVC、ADB、专用 MSD，出厂默认 NCM，由系统工具 `switch_usb_gadget` 管理；较旧固件可能仍默认 RNDIS 或不支持 NCM，安装更新保留已有的开机选择。电脑须支持 CDC NCM，Windows 兼容性尚未认证；RNDIS/ECM 可手动选择，不自动回退，见 [USB 接口功能与切换边界](usage/usb-gadget-switch.md)。使用镜像已有的 `usb_f_ncm.ko`，内核不变；集成不代替电脑端枚举、收流、磁盘弹出、反复切换或重启验收，既有 RNDIS 检查不认证 NCM。USB 状态相关和双向不对称吞吐仍未闭环。CAN 应用功能不等于匹配 BSP 的载荷完整性、持续吞吐、组合负载、延迟或错误恢复验收，不对当前整机组合承诺吞吐。 |
| TF 与单颗诊断 | TF 录制或写入期间禁止拔卡或断电，取卡前正常收尾、同步并成功卸载，见[TF 卡使用](getting-started/tf-card.md)。单颗相机诊断已由用户确认。 |
| 系统镜像、时间与运行依赖 | V2 镜像已完成制作，烧录启动设备已检查 Buildroot/内核、预装应用清单、non-ROS 加载库、Python `3.10.12` 与 ROS2 包环境下版本/包查询。当前固件支持按住 SW1 上电或复位，再通过 USB3 Fastboot 使用 XBurn 烧录，无需调试串口；镜像下载、操作、校验值与硬件匹配要求见[系统烧录](ops/system-flashing.md)。该设备检查到 `ntpd` 自启，但无授时 association、`stratum=16`，不认证 UTC。按 [NTP 同步](time-sync/ntp-sync.md)在采集前核对选星和系统同步；无电池断电不保持 UTC，冷启动、晚联网与持续锁定仍须核验。预装、版本查询或包校验不替代 ROS2 topic/DDS、全部保存路径、USB 或整机验收。 |

分别核对功能、实际保存/接收载荷、退出状态和目标环境，不用参数可接受、元数据或完整容器替代当前组成验收。


## 已知限制

- 当前不提供TF 外参、相机内参或畸变标定。
- ROS2 不提供 RTSP；需要 RTSP 时使用 non-ROS `/root/demo`。
- 相机应用独占 camera/VIO/编码资源；切换前先退出旧应用，并保持 `cam-service` 运行。
- non-ROS相机、RTSP、ROS1 bag、H.264 MP4和ROS2图像节点公开支持`25/30/40/50/60fps`，默认`30fps`；`--rotate 180` 仍只支持 `30fps`。
- 所有相机采集入口仅支持 `vin_lpwm`（VIN LPWM 硬件触发）；不再提供 `none`、free-run 或 `software_gpio` 路径。
- CameraInfo 只有宽高，IMU orientation 不可用。
- 当前相机 ABI 3.0 的 `exposure` 是逐帧冻结的最新 ISP 观测；`status=1` 只是估计，`0` 表示不可用，不保证实际生效帧、误差上界或真实曝光中点。
- 不提供 FSYNC 启用选项或关联输出；共同 realtime epoch 不提供曝光/物理采样同步。
- 相机捕获 observer、IMU owner/consumer 需要实时调度权限；配置失败拒绝启动。饱和负载可能造成显式丢样或采集停止，应用不自动改变系统 IRQ、debug 或实时配额。完整性须结合最终健康记录及实际保存/接收载荷，见[数据合同](development/data-contracts.md)。
- H.265 或四路高帧率播放依赖客户端解码和渲染能力。
- UART1/UART7 逻辑电平为 `3.3V`，DEBUG_UART 为 `1.8V`；相机映射及 FOV 见对应使用指南。UART1 为 CN1 4pin，UART7 为 CN2 5pin；独立 PPS 输入默认启用，使用 `3.3V` 逻辑电平，接线与输入检查见[PPS 同步](time-sync/pps-sync.md)。UART 供电脚额定负载和热插拔条件仍待确认，默认断电接线；针号与线序见[硬件连接与安全](getting-started/hardware-and-safety.md)。相机/IMU 共触发线不自动提供样本/曝光关联。

## 授权与支持

| 项目 | 当前状态 |
|---|---|
| 文档/源码授权 | 文档、non-ROS 示例源码和 ROS2 示例源码采用 Apache-2.0；以各仓库 `LICENSE` 为准。 |
| 预编译 vendor 动态库授权 | 不属于 Apache-2.0 授权范围，保留当前产品二进制限制；随 RoboBaton 4P 产品交付，仅授权在 RoboBaton 4P 硬件和配套系统上运行，具体见 demo 仓 `LICENSE_SCOPE.md`。 |
| 技术支持入口 | 微信：189-2619-5421 |

## 问题反馈清单

提交问题时建议包含版本、使用路径、执行命令、错误文本和必要日志摘要：non-ROS 附 `manifest.sha256` 校验结果、camera ID、RTSP URL、codec/fps 和 `ffprobe` 输出；ROS2 附 launch 命令、topic 名称、`robobaton_imu_rate_monitor` 输出和 `abi_manifest.sha256` 校验结果；UART 附设备节点、baud、mode 和接线说明。不要提交真实 IP、账号、凭据、内部路径、内部日志包或未公开验证资料。
