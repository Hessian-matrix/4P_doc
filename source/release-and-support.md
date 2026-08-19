# 发布、授权与支持

本页记录公开交付物的发布状态、用户会遇到的已知限制、授权和问题反馈信息。

## 版本集合

| 项目 | 当前记录 | 状态 |
|---|---|---|
| 文档 | `v1.1.0` | 发布候选；通过最终门禁后发布。 |
| non-ROS demo/运行包 | `v1.1.0` | 发布候选；部署到`/root/demo`，按`manifest.sha256`整包校验。 |
| ROS2 package/install | `v1.1.0` | 发布候选；部署到`/root/ros2_demo/install`，包名`robobaton_4p_ros2_demo`。 |

功能新增、修复和兼容性变化见 [版本更新记录](changelog.md)。正式 release 不应只修改 tag；公开仓、运行包、ROS2 install、`VERSION` 和发布说明需要保持一致。

在线文档会根据用户反馈继续更新；当前没有单独固定的 `stable` 文档版本。代码和包版本识别仍以仓库 tag、`VERSION`、package version 和 changelog 为准。

## 已知限制

- 当前不提供相机/IMU 硬同步、TF 外参、相机内参或畸变标定。
- ROS2 不提供 RTSP；需要 RTSP 时使用 non-ROS `/root/demo`。
- 相机应用独占 camera/VIO/编码资源；切换前先退出旧应用，并保持 `cam-service` 运行。
- 相机、RTSP、ROS2、ROS1 bag和H.264 MP4仅支持`25fps`和`30fps`，默认`30fps`。
- `software_gpio` 是 V1 唯一稳定 trigger；`vin_lpwm` 和 `none` 为实验性。
- CameraInfo 只有宽高，IMU orientation 不可用。
- H.265 或四路高帧率播放依赖客户端解码和渲染能力。
- DEBUG_UART 是 `1.8V` 系统控制台/调试口；用户可编程 UART1/UART7 使用 `3.3V` TX/RX/GND 并共地，3.3V 硬件通信已通过 V1 验收，两个 UART 3.3V 供电脚对外设供电合计额定边界为 `500 mA`，`serial_port_demo` 只适用于 UART1/UART7。

## 授权与支持

| 项目 | 当前状态 |
|---|---|
| 文档/源码授权 | 文档、non-ROS 示例源码和 ROS2 示例源码采用 Apache-2.0；以各仓库 `LICENSE` 为准。 |
| 预编译 vendor 动态库授权 | 不属于 Apache-2.0 授权范围，保留当前产品二进制限制；随 RoboBaton 4P 产品交付，仅授权在 RoboBaton 4P 硬件和配套系统上运行，具体见 demo 仓 `LICENSE_SCOPE.md`。 |
| 技术支持入口 | 微信：189-2619-5421 |

## 问题反馈清单

提交问题时建议包含版本、使用路径、执行命令、错误文本和必要日志摘要：non-ROS 附 `manifest.sha256` 校验结果、camera ID、RTSP URL、codec/fps 和 `ffprobe` 输出；ROS2 附 launch 命令、topic 名称、`robobaton_imu_rate_monitor` 输出和 `abi_manifest.sha256` 校验结果；UART 附设备节点、baud、mode 和接线说明。不要提交真实 IP、账号、凭据、内部路径、内部日志包或未公开验证资料。
