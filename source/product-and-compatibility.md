# 产品版本与兼容性

本页说明 RoboBaton 4P 第一版文档、non-ROS demo、ROS2 demo 和 X5 运行环境之间的匹配关系。技术事实以公开仓、公开头文件、默认配置、`VERSION` 和运行包 manifest 为准。

## 当前 v1.0.0 发布组成

| 交付物 | 当前版本 | 用户入口 |
|---|---|---|
| 文档 | `1.0.0` | 本站与 `4P_doc` 仓库。 |
| non-ROS demo/运行包 | `1.0.0` | `/root/demo`，来自 `RoboBaton_4p_demo` 的 `demo/`。 |
| ROS2 package/install | `1.0.0` | `/root/ros2_demo/install`，包名 `robobaton_4p_ros2_demo`。 |


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
| 相机配置 | 默认`1280x1088@30fps`；`25/30/40/50/60fps`均为受支持配置。ROS1 bag 60fps单独按stress管理，MP4 60fps属于稳定发布。 |
| Trigger | `software_gpio` 是 V1 唯一稳定 trigger；`vin_lpwm` 和 `none` 为实验性。 |

ROS2 路径不提供 RTSP；需要 RTSP 时使用 non-ROS 路径。当前不提供相机/IMU 硬同步、TF、外参、相机内参或畸变标定；CameraInfo 只有宽高，IMU orientation 不可用。

## 出厂系统镜像版本

```{note}
出厂系统镜像版本标识、兼容范围和只读查询命令将在产品版本方法定版后补充。本文档、non-ROS demo 和 ROS2 package 的 `v1.0.0` 不单独代表出厂系统镜像版本。
```

## 版本查询与整包匹配

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

部署时按整包更新和校验：non-ROS 使用 `manifest.sha256`，ROS2 install 使用 archive checksum 和 runtime `abi_manifest.sha256`。不要只替换单个可执行文件或单个 `.so`；文档、运行包和 ROS2 package 的 `1.0.0` 应作为同一 v1.0.0 发布集合使用。
