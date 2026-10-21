# 发布、授权与支持

本页记录公开交付物的发布状态、用户会遇到的已知限制、授权和问题反馈信息。

## 文档版本政策

本文是整套公开文档的统一版本定义；[版本更新记录](changelog.md) 按此政策记录用户可见更新。

- 文档版本采用“主版本.次版本.修订号”。末位修订号表示同一版本系列内的小 bug 修复、构建脚本调整或文档内容修正，不自动改变各软件版本号。
- `4P_doc/VERSION` 是文档修订号的唯一来源；中英文 Sphinx 配置直接读取它。修订时同步两棵树的最新版本化 changelog 条目和本页版本信息。
- 主仓、non-ROS、ROS2 的软件版本仍以各自 `VERSION`、ROS2 `package.xml`、包版本和 `--version` 输出为准。文档修订不得联动修改这些版本，也不要求文档版本与软件版本相等。
- SO 的 SONAME/ABI 独立于文档和软件版本，例如 `libicm42670.so.2` 中的 `2` 表示 ABI major；real SO `2.0.0` 与产品 `--version` 也是不同标识。文档修订不表示软件重新发布或板端已更新。

## 版本集合

| 项目 | 当前版本 | 状态 |
|---|---|---|
| 文档修订 | `2.0.3` | 本站持续更新；修订内容见 [版本更新记录](changelog.md)，不表示软件版本升级。 |
| non-ROS demo/运行包 | `v2.0.0` | 部署到`/root/demo`，按`manifest.sha256`整包校验。 |
| ROS2 package/install | `v2.0.0` | 软件包部署到`/root/ros2_demo/install`，包名`robobaton_4p_ros2_demo`。目标板使用前应按 [ROS2 Demo 使用](usage/ros2-demo.md)、[non-ROS Demo 使用](usage/non-ros-demo.md) 和 [保存数据](usage/save-data-guide.md) 完成对应路径的实际检查；软件包发布不替代目标板运行检查。 |

功能新增、修复和兼容性变化见 [版本更新记录](changelog.md)。

在线文档会根据用户反馈继续更新；当前没有单独固定的 `stable` 文档版本。文档修订号按上述政策识别，Read the Docs 的 `latest` 是部署标识，不是软件版本。软件正式发布不等同于跳过目标板运行检查。相机参数集合公开支持 `25/30/40/50/60fps`，默认 `30fps`；保存和 ROS2 路径应以实际结果、退出码、manifest 和目标板环境检查判定。

当前使用指南覆盖标识为 `2.0.0` 的 V2 软件及 changelog 中明确列出的未发布源码更新；同一个版本字符串不证明工件组成相同，应核对运行包 manifest、实际链接库和对应说明。ICM-42670-P 头文件、库、consumer 与配置必须成套迁移，不兼容 V1。ICM 原生 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`，旧 `500/1000/2000Hz` 明确拒绝。历史 V1 changelog 不改写，不能用于宣称 V2 实板或整机验收。

## 已知限制

- 当前不提供TF 外参、相机内参或畸变标定。
- ROS2 不提供 RTSP；需要 RTSP 时使用 non-ROS `/root/demo`。
- 相机应用独占 camera/VIO/编码资源；切换前先退出旧应用，并保持 `cam-service` 运行。
- non-ROS相机、RTSP、ROS1 bag、H.264 MP4和ROS2图像节点公开支持`25/30/40/50/60fps`，默认`30fps`；`--rotate 180` 仍只支持 `30fps`。
- 所有相机采集入口仅支持 `vin_lpwm`（VIN LPWM 硬件触发）；不再提供 `none`、free-run 或 `software_gpio` 路径。
- CameraInfo 只有宽高，IMU orientation 不可用。
- 当前相机 ABI 2.2 的 `exposure` 是逐帧冻结的最新 ISP 观测；`status=1` 只是估计，`0` 表示不可用，不保证实际生效帧、误差上界或真实曝光中点。
- FSYNC 默认关闭，仅 `800/1600Hz` 可显式开启；`status=1` 才是唯一触发—样本关联，不改变 IMU 相位，也不保证曝光同步。容器完整不等于关联完整或 DDS 全部送达。
- 相机捕获、IMU owner/observer/consumer 需要实时调度权限；配置失败拒绝启动。饱和负载可能造成显式丢样或采集停止，应用不自动改变系统 IRQ、debug 或实时配额。完整性须结合最终健康记录及实际保存/接收载荷，见[数据合同](development/data-contracts.md)。
- H.265 或四路高帧率播放依赖客户端解码和渲染能力。
- UART1/UART7 电平保持 `3.3V`，DEBUG_UART 保持 `1.8V`；相机物理映射和 FOV 不变，独立 PPS IO 默认启用。V2 完整 5pin 线序、供电脚额定值和热插拔条件以正式硬件资料为准，不沿用 V1 `500 mA` 或历史验收；见[硬件连接与安全](getting-started/hardware-and-safety.md)。相机/IMU 共触发线不自动提供样本/曝光关联。

## 授权与支持

| 项目 | 当前状态 |
|---|---|
| 文档/源码授权 | 文档、non-ROS 示例源码和 ROS2 示例源码采用 Apache-2.0；以各仓库 `LICENSE` 为准。 |
| 预编译 vendor 动态库授权 | 不属于 Apache-2.0 授权范围，保留当前产品二进制限制；随 RoboBaton 4P 产品交付，仅授权在 RoboBaton 4P 硬件和配套系统上运行，具体见 demo 仓 `LICENSE_SCOPE.md`。 |
| 技术支持入口 | 微信：189-2619-5421 |

## 问题反馈清单

提交问题时建议包含版本、使用路径、执行命令、错误文本和必要日志摘要：non-ROS 附 `manifest.sha256` 校验结果、camera ID、RTSP URL、codec/fps 和 `ffprobe` 输出；ROS2 附 launch 命令、topic 名称、`robobaton_imu_rate_monitor` 输出和 `abi_manifest.sha256` 校验结果；UART 附设备节点、baud、mode 和接线说明。不要提交真实 IP、账号、凭据、内部路径、内部日志包或未公开验证资料。
