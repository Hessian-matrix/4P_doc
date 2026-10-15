# 产品版本与兼容性

本页说明 RoboBaton 4P V2 当前源码、non-ROS/ROS2 demo 与运行环境的匹配关系；历史 V1 下载包不自动兼容 V2。技术事实以公开头文件、配置、VERSION 和运行包 manifest 为准。

## 文档与软件版本

当前文档修订号、软件发布版本和统一版本定义见 [发布、授权与支持](../release-and-support.md#文档版本政策)。文档修订不要求软件版本同步递增。

V2 IMU 为 ICM-42670-P，API `icm42670_*`，real SO `libicm42670.so.2.0.0`、SONAME `libicm42670.so.2`、节点 `ICM42670_X5_2.0`。不兼容 V1 ICM 库；头文件、库、consumer 和配置必须成套更新。原生 ODR `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；旧 `500/1000/2000Hz` 明确拒绝，不静默重采样。

| 交付物 | 用户入口 |
|---|---|
| 文档 | 本站与 `4P_doc` 仓库。 |
| non-ROS demo/运行包 | `/root/demo`，来自 `RoboBaton_4p_demo` 的 `demo/`。 |
| ROS2 package/install | `/root/ros2_demo/install`，包名 `robobaton_4p_ros2_demo`。 |


## 功能与运行目录

| 路径 | 主要能力 | 运行目录 | 备注 |
|---|---|---|---|
| non-ROS | 四路 RTSP、IMU、UART 示例、公开 C ABI | `/root/demo` | RTSP 端口 `554..557`，path `/PRR`；H.264 默认，H.265 可选。 |
| ROS2 | raw/compressed 图像、CameraInfo、IMU、温度 topic | `/root/ros2_demo/install` | ROS2 Humble；compressed 使用 X5 `MEDIA_CODEC_ID_JPEG` 硬件编码；不提供 RTSP。 |

两条路径不要混用目录、头文件或 `.so`，同一时间只运行一个占用 camera/VIO/编码资源的应用。

## 运行要求

| 项目 | 要求 |
|---|---|
| 板端平台 | X5；相机运行依赖 `cam-service`，不建议停止或重配该服务。 |
| ROS2 | Humble underlay；通过 `robobaton_ros2_env.bash` 加载环境。 |
| 交叉编译 | 只在开发机使用 X5 交叉编译包；不建议在 X5 板端原生编译。 |
| non-ROS相机配置 | 默认`1280x1088@30fps`；支持`25/30/40/50/60fps`；输出画布 `1280x1088`/`640x480`/`720x480`/`1280x720`。 |
| Trigger | `vin_lpwm` 是 V2.0.0 默认 trigger（VIN 硬件触发）；`none` 仅用于显式 free-run 诊断；`software_gpio` 仅主仓内部调试。 |

ROS2 路径不提供 RTSP；需要 RTSP 时使用 non-ROS 路径。当前不提供TF、外参、相机内参或畸变标定；CameraInfo 只有宽高，IMU orientation 不可用。

## 出厂系统镜像与目标板兼容性

板端软件 `v1.3.0` 的历史出厂镜像与烧录工具只适用于其 V1 原产品原板，不能写入 V2；URL 和工件不可原地改写。V2 匹配 BSP/系统镜像和恢复通道的公开资料待确认，见[系统烧录](../ops/system-flashing.md)。

## 版本查询与整包匹配

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

部署时按整包更新和校验：non-ROS使用`manifest.sha256`，ROS2 install使用archive checksum和runtime `abi_manifest.sha256`。不要只替换单个可执行文件或单个`.so`；运行包中的程序、头文件和运行库应来自同一经验证的软件包，不能根据文档修订号判断软件或 ABI 是否匹配。
