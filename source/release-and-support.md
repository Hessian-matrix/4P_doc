# 发布、授权与支持

本页记录公开交付物的发布状态、已知限制、授权和支持信息。没有明确权威信息的项目统一标记“待产品确认”；授权明确前，不把整套交付物笼统称为开放源代码交付物。

## 版本记录

| 项目 | 当前记录 | 状态 |
|---|---|---|
| 文档版本 | `1.0.0` | 第一版候选；正式发布日期和tag待发布审批 |
| non-ROS 示例仓 | `RoboBaton_4p_demo` | 当前推荐入口，待产品确认 release/tag |
| non-ROS 运行包 | `demo/` + `manifest.sha256` | 当前可按 manifest 校验部署，待产品确认发布编号 |
| X5 交叉编译包 | `x5_4cam_cross_toolchain_20260708.tar.gz` | 待产品确认包大小、SHA256 和下载保留策略 |
| ROS2 示例仓 | `RoboBaton_4P_ROS2_demo` | 当前候选`package.xml`版本`1.0.0`，正式release/tag待发布审批 |

功能新增、问题修复和已知限制统一维护在[版本更新记录](changelog.md)。仓库、non-ROS运行包和ROS2 install中的`VERSION`必须一致；正式release不得只修改tag而不更新版本文件和更新记录。

## 已知限制

- 当前不提供相机/IMU 硬同步。
- 当前不提供公开 TF 外参、相机内参或畸变标定。
- ROS2 示例当前可用于构建、部署和 topic 使用；正式 Git release/tag、产品发布编号和支持周期仍待产品确认。
- V1 稳定相机功能配置为 `25/30/40/50fps`，默认 `30fps`；`60fps` 是显式 `stress-only` 压力配置，不是稳定发布 profile。
- V1 已验证的 Trigger 模式只有 `software_gpio`；`vin_lpwm` 和 `none` 为实验性 / 未验收。
- 相机应用需要独占 camera/VIO/编码资源。
- `cam-service` 是相机运行依赖，不建议停止。
- H.265 四路高帧率播放对客户端解码和渲染能力有要求。
- UART TX/RX 逻辑电平为 `3.3V`，公开 pinout 见硬件页；Pin 1、3V3 供电方向/电流和热插拔要求仍待产品确认。
- V1 只交付 `serial_port_demo` 软件示例，UART 实际硬件通信未纳入 V1 验收。
- 其他硬件电气、FPC 方向、热插拔和散热要求待产品确认。

## 授权与第三方声明

| 项目 | 当前状态 |
|---|---|
| 文档许可证 | 待产品确认 |
| `RoboBaton_4p_demo` 示例源码许可证 | 待产品确认 |
| 预编译动态库授权 | 待产品确认 |
| X5 交叉编译包授权/再分发权限 | 待产品确认 |
| 第三方组件声明 | 待产品确认 |

授权明确前，文档只把 `RoboBaton_4p_demo` 描述为“公开 demo 仓”或“用户交付仓”，不把完整产品、动态库或交叉编译包统称为开放源代码交付物。

## 支持渠道

| 项目 | 状态 |
|---|---|
| 技术支持邮箱 | 待产品确认 |
| 问题反馈入口 | 待产品确认 |
| 发布公告入口 | 待产品确认 |
| 安全问题上报方式 | 待产品确认 |

## 问题反馈信息清单

提交问题时建议包含：

- 产品名称和待确认的硬件版本/系统版本。
- 使用路径：non-ROS `demo/`、自行交叉编译产物，或 ROS2 `/root/ros2_demo/install`。
- `demo/manifest.sha256` 校验结果。
- 执行的完整命令，使用 `<x5-ip>` 替代真实地址。
- 相机问题：camera ID、RTSP URL、codec、fps、`ffprobe` 输出、板端 demo 日志。
- IMU 问题：采样率、`SENSOR_IMU_RESULT` 或 `imu_reader_demo` 输出摘要。
- ROS2 问题：launch 命令、topic 名称、`robobaton_imu_rate_monitor` 输出摘要、`abi_manifest.sha256` 校验结果。
- UART 问题：设备节点、baud、mode、接线说明；不要附带未经确认的电气推断。
- 不要提交账号、敏感网络地址、非公开路径、未公开验证资料或历史调试记录。
