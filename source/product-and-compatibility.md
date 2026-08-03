# 产品版本与兼容性

本页用于记录 RoboBaton 4P 文档、硬件、系统、运行包和示例代码之间的兼容关系。没有公开权威值的项目均标记为“待产品确认”；确认前不要用 `latest`、仓库默认分支或单次本地构建结果替代兼容性证明。

## 兼容性表

| 项目 | 当前公开状态 | 兼容性/约束 | 待确认项 |
|---|---|---|---|
| RoboBaton 4P 硬件版本 | 待产品确认 | 文档仅按“RoboBaton 4P”公开名称描述，不区分硬件批次。 | 硬件版本号、丝印、BOM/批次边界。 |
| X5 系统版本 | 待产品确认 | 相机 demo 依赖 X5 板端 camera/vpf/hbmem/multimedia/FFmpeg/OpenSSL 等系统运行库。 | 可支持的系统镜像版本、内核版本、板端预装库版本。 |
| non-ROS 示例仓 | `RoboBaton_4p_demo` | 当前推荐入口；提供四目 RTSP、IMU 和 UART 示例、公开头文件与预编译 `.so`。 | 对外发布 tag、release 编号。 |
| non-ROS 运行包 | `demo/` | 可部署到 X5 `/root/demo`；包含启动脚本、`env.sh`、`config/`、`bin/`、`lib/`、`manifest.sha256`。 | 对外发布包名和下载位置。 |
| 运行包 manifest | `demo/manifest.sha256` | 部署前必须在临时目录执行 `sha256sum -c manifest.sha256`。 | manifest 所属发布版本号。 |
| X5 交叉编译包 | `x5_4cam_cross_toolchain_20260708.tar.gz` | 用于开发机交叉编译公开 demo；不建议在 X5 板端原生编译。 | 包大小、SHA256、正式下载页和保留策略。 |
| 文档版本 | 待产品确认 | 本站是第一版可审阅用户文档；内容以当前公开 demo 仓和公开头文件为准。 | 文档版本号、发布日期、对应产品发布版本。 |
| ROS2 示例仓 | `RoboBaton_4P_ROS2_demo` | 当前可用；包名 `robobaton_4p_ros2_demo`，`package.xml` 版本 `0.1.0`，提供 ROS2 构建、install 部署、raw/compressed 图像、CameraInfo、IMU 和温度 topic。 | 对外 release/tag、正式发布编号和支持周期。 |
| ROS2 install 包 | `1.ros2_build/install` | 可部署到 X5 `/root/ros2_demo/install`；runtime 文件位于 `lib/robobaton_4p_ros2_demo/`，使用 `abi_manifest.sha256` 校验。 | install 包名、下载位置、发布编号。 |

## 运行包 manifest 摘要

当前 non-ROS `demo/manifest.sha256` 覆盖以下文件类别：

| 类别 | 文件 |
|---|---|
| 启动脚本 | `cam_demo`、`sensor_demo`、`imu_reader_demo`、`serial_port_demo` |
| ELF 程序 | `bin/cam_demo`、`bin/sensor_demo`、`bin/imu_reader_demo`、`bin/serial_port_demo` |
| 配置 | `config/sensor_config.yaml`、`env.sh` |
| 动态库 | `lib/libsc132.so*`、`lib/libicm42688.so*`、`lib/libprrtsp.so*` |

部署时必须整包更新，禁止只替换单个可执行文件或单个 `.so`。如果 manifest 校验失败，停止本次更新并保留旧 `/root/demo`。

## 确认前处理规则

- 硬件、电气、系统镜像、授权和支持渠道未确认前，只能写“待产品确认”。
- ROS2 当前可作为用户构建、部署和运行路径；正式 Git release/tag 和产品发布编号未确认前，不声称已经发布正式版本。
- 公开文档只引用用户可见仓库、公开头文件、默认配置和运行包 manifest，不引用内部测试报告、板卡地址、账号或长测日志。
