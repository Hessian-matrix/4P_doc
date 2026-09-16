# 发布、授权与支持

本页记录公开交付物的发布状态、用户会遇到的已知限制、授权和问题反馈信息。

## 版本集合

| 项目 | 当前正式发布 | 状态 |
|---|---|---|
| 文档 | `v1.3.0` | 随 v1.3.0 四仓发布；发布日期以仓库 tag 为准。 |
| non-ROS demo/运行包 | `v1.3.0` | 部署到`/root/demo`，按`manifest.sha256`整包校验。 |
| ROS2 package/install | `v1.3.0` | 软件包部署到`/root/ros2_demo/install`，包名`robobaton_4p_ros2_demo`。目标板使用前应按 [ROS2 Demo 使用](ros2-demo.md)、[non-ROS Demo 使用](non-ros-demo.md) 和 [保存数据](save-data-guide.md) 完成对应路径的实际检查；软件包发布不替代目标板运行检查。 |

功能新增、修复和兼容性变化见 [版本更新记录](changelog.md)。

在线文档会根据用户反馈继续更新；当前没有单独固定的 `stable` 文档版本。代码和包版本识别仍以仓库 tag、`VERSION`、package version 和 changelog 为准。这里的“正式发布”表示版本化文档/仓库/包已经发布，不等同于跳过目标板运行检查。相机参数集合公开支持 `25/30/40/50/60fps`，默认 `30fps`；保存和 ROS2 路径应以实际结果、退出码、manifest 和目标板环境检查判定。

## 已知限制

- 当前不提供TF 外参、相机内参或畸变标定。
- ROS2 不提供 RTSP；需要 RTSP 时使用 non-ROS `/root/demo`。
- 相机应用独占 camera/VIO/编码资源；切换前先退出旧应用，并保持 `cam-service` 运行。
- non-ROS相机、RTSP、ROS1 bag、H.264 MP4和ROS2图像节点公开支持`25/30/40/50/60fps`，默认`30fps`；`--rotate 180` 仍只支持 `30fps`。
- `software_gpio` 是 V1 唯一稳定 trigger；`none` 仅用于显式 free-run 诊断。
- CameraInfo 只有宽高，IMU orientation 不可用。
- H.265 或四路高帧率播放依赖客户端解码和渲染能力。
- DEBUG_UART 是 `1.8V` 系统控制台/调试口；普通模式下 UART1/UART7 使用 `3.3V` TX/RX/GND 并共地，硬件通信已通过 V1 验收。UART1/UART7 的 `3V3` 脚支持输入/输出并可为外设供电，两个接口共享合计 `500 mA` 限制并支持热插拔；`serial_port_demo` 只适用于普通 UART 模式。PPS 模式另占用 UART7 RX 为 `/dev/pps2`，并释放 UART7 TX 为 GPIO/IO，详见 [PPS 同步](pps-sync.md)。

## 授权与支持

| 项目 | 当前状态 |
|---|---|
| 文档/源码授权 | 文档、non-ROS 示例源码和 ROS2 示例源码采用 Apache-2.0；以各仓库 `LICENSE` 为准。 |
| 预编译 vendor 动态库授权 | 不属于 Apache-2.0 授权范围，保留当前产品二进制限制；随 RoboBaton 4P 产品交付，仅授权在 RoboBaton 4P 硬件和配套系统上运行，具体见 demo 仓 `LICENSE_SCOPE.md`。 |
| 技术支持入口 | 微信：189-2619-5421 |

## 问题反馈清单

提交问题时建议包含版本、使用路径、执行命令、错误文本和必要日志摘要：non-ROS 附 `manifest.sha256` 校验结果、camera ID、RTSP URL、codec/fps 和 `ffprobe` 输出；ROS2 附 launch 命令、topic 名称、`robobaton_imu_rate_monitor` 输出和 `abi_manifest.sha256` 校验结果；UART 附设备节点、baud、mode 和接线说明。不要提交真实 IP、账号、凭据、内部路径、内部日志包或未公开验证资料。
