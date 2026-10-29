# 发布、授权与支持

本页记录公开交付物的发布状态、用户会遇到的已知限制、授权和问题反馈信息。

## 文档版本政策

本文是整套公开文档的统一版本定义；[版本更新记录](changelog.md) 按此政策记录用户可见更新。

- 文档版本采用“主版本.次版本.修订号”。末位修订号表示同一版本系列内的小 bug 修复、构建脚本调整或文档内容修正，不自动改变各软件版本号。
- `4P_doc/VERSION` 是文档修订号的唯一来源；中英文 Sphinx 配置直接读取它。修订时同步两棵树的最新版本化 changelog 条目和本页版本信息。
- 主仓、non-ROS、ROS2 的软件版本仍以各自 `VERSION`、ROS2 `package.xml`、包版本和 `--version` 输出为准。文档修订不得联动修改这些版本，也不要求文档版本与软件版本相等。
- SO 的 SONAME/ABI 独立于文档和软件版本，例如 `libicm42670.so.3` 中的 `3` 表示 ABI major；real SO `3.0.0` 与产品 `--version` 也是不同标识。文档修订不表示软件重新发布或板端已更新。


| 库 | 实体文件 | SONAME | 符号节点 |
|---|---|---|---|
| ICM42670 | `libicm42670.so.3.0.0` | `libicm42670.so.3` | `ICM42670_X5_3.0` |
| SC132 | `libsc132.so.3.0.0` | `libsc132.so.3` | `LIBSC132_3.0` |
| PRRTSP | `libprrtsp.so.2.0.1` | `libprrtsp.so.2` | `LIBPRRTSP_2.0` |

实体库修订标识实现；SONAME major 标识可替换的公开合同；符号节点区分兼容扩展与不兼容切换，不与产品代号机械同步。SC132 当前 ABI 为 3.0：consumer 必须按当前头文件的时间域、触发模式及 frame-info 语义成套重建，禁止 `.so.2 -> .so.3` 链接。ROS2 只包含 ICM42670 和 SC132。

ICM42670 ABI 3.0 保留字段布局但改变 host 时间语义：INT1 仅唤醒，FIFO/实测 TMST 定义样本；host 为 burst 完成时 RAW 观测经当次桥接转换的原始 realtime 值，详见[数据合同](development/data-contracts.md#imu)。必须重建全部 consumer、同步头/SO 并移除旧 `.2` 库；所有导出只保留 `ICM42670_X5_3.0`，无旧别名或跨 major shim。软件 VERSION 不因本次 ABI 变化自动变更。

## 版本集合

| 项目 | 当前版本 | 状态 |
|---|---|---|
| 文档修订 | `2.0.14` | 本站持续更新；修订内容见 [版本更新记录](changelog.md)，不表示软件版本升级。 |
| non-ROS demo/运行包 | `v2.0.0` | 默认安装位置为 `/root/demo`，按 `manifest.sha256` 整包校验；不表示目标板已安装当前源码对应工件。 |
| ROS2 package/install | `v2.0.0` | 默认安装位置为 `/root/ros2_demo/install`，包名 `robobaton_4p_ros2_demo`。源码更新或本地重编译不等于目标板已安装修订或正式升级；目标板实际安装版本须核对 manifest 与所加载库。使用前应按 [ROS2 Demo 使用](usage/ros2-demo.md)、[non-ROS Demo 使用](usage/non-ros-demo.md) 和 [保存数据](usage/save-data-guide.md) 完成对应路径的实际检查。 |

功能新增、修复和兼容性变化见 [版本更新记录](changelog.md)。

在线文档会根据用户反馈继续更新；当前没有单独固定的 `stable` 文档版本。文档修订号按上述政策识别，Read the Docs 的 `latest` 是部署标识，不是软件版本。软件正式发布不等同于跳过目标板运行检查。相机参数集合公开支持 `25/30/40/50/60fps`，默认 `30fps`；保存和 ROS2 路径应以实际结果、退出码、manifest 和目标板环境检查判定。

当前使用指南覆盖标识为 `2.0.0` 的 V2 软件及 changelog 中明确列出的未发布源码更新；同一个版本字符串不证明工件组成相同，应核对运行包 manifest、实际链接库和对应说明。ICM-42670-P 头文件、库、consumer 与配置必须成套匹配。ICM 原生 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；不支持的速率明确拒绝，不静默重采样。文档修订不代表实板或整机验收。

硬件标识（当前硬件修订为 V2.2）、软件 `2.0.0`、文档修订及各 SO ABI 是独立维度；不能互相代替兼容性或验收结论。本次只同步文档，不改变软件行为或发布状态。

## 当前实现能力

以下是当前公开源码接受的参数和输出合同，不是所有模式、负载和时长组合都已通过验收。

| 路径 | 当前能力 | 约束 |
|---|---|---|
| 相机 | `25/30/40/50/60fps`，默认 `30fps`；NV12 native `1280x1088`，离散 VSE `640x480`/`720x480`/`1280x720` | 仅完整四路或单颗诊断，不支持 2/3 路；旋转 `180` 仅 `30fps`。所有入口仅 `vin_lpwm`。 |
| IMU | 原生 `25/50/100/200/400/800/1600Hz`，默认 `800Hz` | `500/1000/2000Hz` 明确拒绝，不重采样。FIFO 顺序和实测 TMST 定义样本；INT1 仅唤醒，无逐包 GPIO 身份或独立 INT1→RAW observer。 |
| non-ROS | 四路 H.264/H.265 RTSP，可同时选择 ROS1 bag 或 H.264 MP4 保存 | bag 与 MP4 互斥；MP4 仅 H.264、完整四路。独立 UART/CAN 示例不代表外设和整机负载已验收。 |
| ROS2 | raw/compressed Image、CameraInfo、曝光观测、IMU、温度及可选 FSYNC | 无 RTSP、TF 或标定；发布成功不等于 DDS 实际收到。 |
| 曝光/FSYNC | 曝光为采集后冻结的最新 ISP 估计；FSYNC 默认关闭，仅 `800/1600Hz` | 曝光 `status=1` 是估计，`status=0` 不可用；FSYNC 是芯片 tag/delta、有界实测端点及唯一 RAW 关联，不保证实际生效曝光或曝光同步。显式曝光中点测试模式仍只是估算，见[数据合同](development/data-contracts.md)。 |

相机捕获线程使用 `SCHED_FIFO/60`，IMU 采集 owner 使用 `SCHED_FIFO/20`，non-ROS IMU consumer 和 ROS2 IMU 发布使用 `SCHED_RR/3`；旧 IMU `SCHED_FIFO/30` observer 已移除。所需实时调度不可用时拒绝启动，不静默降级，也不自动修改 IRQ、debug 或系统实时配额。相机 `500µs` 捕获窗口和 IMU `200µs` admission 保持不变，无 IRQ、主机当前时间或最近邻兜底。公开时间为可重复、可回拨的 `CLOCK_REALTIME`；RAW 仅用于内部身份和关联，host burst 观测与 sample/trigger 时间不可混用，详见[数据合同](development/data-contracts.md)。

(capability-verification-boundary)=
## 能力与验证边界

| 项目 | 当前结论与用户限制 |
|---|---|
| 高帧率与 FSYNC | 当前组成已有 non-ROS `60fps` + `1600Hz` FSYNC 在 CPU/BPU 负载下约 `300s` 的控制台关联结果；这仅支持该次关联观察，不证明已保存图像可解码、ROS2 吞吐或所有数据无损。 |
| bag 压力与丢组 | 默认最小丢组间隔 `10`，按连续 `source_group_order` 而非 producer `group_id` 计距；只淘汰已编码、未被 writer 领取的完整四路组，已领取组受保护。无合法旧组或新组可丢时停止，排空为可读 partial 并非零退出。主动隔组保存需显式将最小间隔设为 `2`。高 CPU/存储压力下已发生策略耗尽、未达到 `300s`；策略正确停止不是持续压力或全传感器通过。任何丢组均为 `data_complete=false`，见{ref}`数据保存 <persistence-fps-boundary>`。 |
| 样本完整性 | bag 图像停止提前关闭 IMU 接纳、ROS2 producer 静止前拒收回调及正常信号退出先关 context 的缺陷已修复；正常收尾先静止 producer，再排空 consumer。历史 DDS 差额的精确身份/原因仍不可恢复；短窗计数相等不关闭持续完整性缺口。已保存序列连续或 bag complete 均不证明所有硬件样本已保存。`allow-counted` 允许可观察拒样，`strict` 遇拒样失败，均不保证任意负载零丢失。 |
| ROS2 速率与 SHM | 修复后 `30fps`/`1600Hz` 短窗 smoke 的 producer、sink 和 DDS 数量相等；不替代此前发布/接收差额的根因证明，也不承诺所有路径持续 `60fps`，此前高档未达到目标。SHM 每 participant `256 MiB` 是容量预算，不是历史初始化根因修复；专项暂停。metrics 关闭表示不可用；开启只统计 sink 的 `publish()` 正常返回，不确认 DDS 接收。 |
| 长时间录制 | 当前新组成的 `8h` MP4 + FSYNC 长录因压力前置条件未通过而尚未启动。历史 `8h` 结果不能认证当前组成，不承诺当前已完成长录验收。 |
| 捕获和启动 | LPWM `500µs` 窗口 fail-closed 的长尾停止问题尚未解决；FIFO/TMST 重构不代表 BSP GPIO/IRQ 或 LPWM 已修复。首个 FSYNC 标记包等待绝对右端点及实测 Arm 的分支已实现，但没有该特殊分支明确实板命中的证明。FIFO 使能错过最早实测 ODR guard 会拒绝启动；overflow、坏包、时钟/epoch 歧义仍 fail-closed。 |
| 编码 | 原生 bag JPEG 去除私有 JPU APP9，不改变 ROS2 JPEG 插件。bag JPEG 解码正常不关闭 H.264 RTSP `60fps` 的 missing-reference/slice 告警问题。 |
| USB/CAN | USB 状态相关和双向不对称吞吐、Bulk 完整模式组合及重新枚举仍未闭环。CAN 应用功能不等于匹配 BSP 的载荷完整性、持续吞吐、组合负载、延迟或错误恢复验收，不对当前整机组合承诺吞吐。 |
| TF 与单颗诊断 | TF 热插拔硬件修复和单颗相机诊断已由用户确认；不推导新的硬件版本、所有卡兼容性或录制中安全拔卡，具体操作见[TF 卡使用](getting-started/tf-card.md)。 |
| 系统时间与运行依赖 | realtime 字段语义不认证持久 RTC、重启后校时或绝对 UTC。干净系统镜像中 `python3`/`libstdc++` 的镜像与包归属仍待确认，不能把包校验通过当作全部运行依赖已验证。 |

判读原则是分别核对功能、实际保存/接收载荷、退出状态和目标环境，不以参数可接受、关联 JSON、完整容器或历史单项结果替代当前组成验收。


## 已知限制

- 当前不提供TF 外参、相机内参或畸变标定。
- ROS2 不提供 RTSP；需要 RTSP 时使用 non-ROS `/root/demo`。
- 相机应用独占 camera/VIO/编码资源；切换前先退出旧应用，并保持 `cam-service` 运行。
- non-ROS相机、RTSP、ROS1 bag、H.264 MP4和ROS2图像节点公开支持`25/30/40/50/60fps`，默认`30fps`；`--rotate 180` 仍只支持 `30fps`。
- 所有相机采集入口仅支持 `vin_lpwm`（VIN LPWM 硬件触发）；不再提供 `none`、free-run 或 `software_gpio` 路径。
- CameraInfo 只有宽高，IMU orientation 不可用。
- 当前相机 ABI 3.0 的 `exposure` 是逐帧冻结的最新 ISP 观测；`status=1` 只是估计，`0` 表示不可用，不保证实际生效帧、误差上界或真实曝光中点。
- FSYNC 默认关闭，仅 `800/1600Hz` 可显式开启；`status=1` 才是唯一触发—样本关联，不改变 IMU 相位，也不保证曝光同步。容器完整不等于关联完整或 DDS 全部送达。
- 相机捕获 observer、IMU owner/consumer 需要实时调度权限；配置失败拒绝启动。饱和负载可能造成显式丢样或采集停止，应用不自动改变系统 IRQ、debug 或实时配额。完整性须结合最终健康记录及实际保存/接收载荷，见[数据合同](development/data-contracts.md)。
- H.265 或四路高帧率播放依赖客户端解码和渲染能力。
- UART1/UART7 逻辑电平为 `3.3V`，DEBUG_UART 为 `1.8V`；相机映射及 FOV 见对应使用指南，独立 PPS IO 默认启用。V2 完整 5pin 线序、供电脚额定值和热插拔条件仍待正式硬件资料确认，默认断电接线；见[硬件连接与安全](getting-started/hardware-and-safety.md)。相机/IMU 共触发线不自动提供样本/曝光关联。

## 授权与支持

| 项目 | 当前状态 |
|---|---|
| 文档/源码授权 | 文档、non-ROS 示例源码和 ROS2 示例源码采用 Apache-2.0；以各仓库 `LICENSE` 为准。 |
| 预编译 vendor 动态库授权 | 不属于 Apache-2.0 授权范围，保留当前产品二进制限制；随 RoboBaton 4P 产品交付，仅授权在 RoboBaton 4P 硬件和配套系统上运行，具体见 demo 仓 `LICENSE_SCOPE.md`。 |
| 技术支持入口 | 微信：189-2619-5421 |

## 问题反馈清单

提交问题时建议包含版本、使用路径、执行命令、错误文本和必要日志摘要：non-ROS 附 `manifest.sha256` 校验结果、camera ID、RTSP URL、codec/fps 和 `ffprobe` 输出；ROS2 附 launch 命令、topic 名称、`robobaton_imu_rate_monitor` 输出和 `abi_manifest.sha256` 校验结果；UART 附设备节点、baud、mode 和接线说明。不要提交真实 IP、账号、凭据、内部路径、内部日志包或未公开验证资料。
