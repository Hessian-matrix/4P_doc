# 产品版本与兼容性

本页说明 RoboBaton 4P V2 当前源码、non-ROS/ROS2 demo 与运行环境的匹配关系。技术事实以公开头文件、配置、VERSION 和运行包 manifest 为准。

## 文档与软件版本

当前文档修订号、软件发布版本和统一版本定义见 [发布、授权与支持](../release-and-support.md#文档版本政策)。文档修订不要求软件版本同步递增。

硬件标识、软件 `2.0.0`、文档和 SO ABI 独立识别。参数受支持不等于所有模式/负载/时长已通过；当前高帧率、压力、长录及外设限制见{ref}`能力与验证边界 <capability-verification-boundary>`。

V2 IMU 为 ICM-42670-P，API `icm42670_*`，ABI 3.0，real SO `libicm42670.so.3.0.0`、SONAME `libicm42670.so.3`；全部导出仅使用 `ICM42670_X5_3.0`，无旧别名。字段布局不变但 host 时间改为 SPI FIFO burst 完成观测，INT1 仅唤醒；FIFO 顺序与实测 TMST 定义样本。必须同步头文件、库、consumer 与配置并重建全部 consumer，移除旧 `.2` 库，不建立跨 major 链接；软件 VERSION 不变。原生 ODR `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；不支持的速率明确拒绝，不静默重采样。

| 交付物 | 用户入口 |
|---|---|
| 文档 | 本站与 `4P_doc` 仓库。 |
| non-ROS demo/运行包 | `/root/demo`，来自 `RoboBaton_4p_demo` 的 `demo/`。 |
| ROS2 package/install | `/root/ros2_demo/install`，包名 `robobaton_4p_ros2_demo`。 |


## 功能与运行目录

| 路径 | 主要能力 | 运行目录 | 备注 |
|---|---|---|---|
| non-ROS | 四路 RTSP、IMU、UART、互斥 bag/MP4 保存、可选 FSYNC 与曝光观测 | `/root/demo` | RTSP `554..557/PRR`，H.264 默认、H.265 可选；四路拼接示例为 `558/PRR`。 |
| ROS2 | raw/compressed 图像、CameraInfo、逐帧曝光观测、IMU、温度与可选 FSYNC | `/root/ros2_demo/install` | ROS2 Humble；compressed 使用 X5 `MEDIA_CODEC_ID_JPEG` 硬件编码；不提供 RTSP。 |

两条路径不要混用目录、头文件或 `.so`，同一时间只运行一个占用 camera/VIO/编码资源的应用。

## 运行要求

| 项目 | 要求 |
|---|---|
| 板端平台 | X5；相机运行依赖 `cam-service`，不建议停止或重配该服务。 |
| ROS2 | Humble underlay；通过 `robobaton_ros2_env.bash` 加载环境。 |
| 交叉编译 | 只在开发机使用 X5 交叉编译包；不建议在 X5 板端原生编译。 |
| non-ROS相机配置 | 默认`1280x1088@30fps`；支持`25/30/40/50/60fps`；输出画布 `1280x1088`/`640x480`/`720x480`/`1280x720`。 |
| Trigger | 所有相机入口仅支持 `vin_lpwm`（VIN LPWM 硬件触发）；不提供 free-run 或软件 GPIO 触发。 |
| 权限与调度 | 相机需要只读 `/dev/mem`，捕获和 IMU 实时线程需要调度权限，失败拒绝启动；详见[数据合同](../development/data-contracts.md)。 |

相机仅完整四路或单颗诊断，不支持 2/3 路；旋转 `180` 仅支持 `30fps`。单颗诊断已由用户确认，不扩展为所有模式或压力负载验收。

ROS2 路径不提供 RTSP；需要 RTSP 时使用 non-ROS 路径。当前不提供TF、外参、相机内参或畸变标定；CameraInfo 只有宽高，IMU orientation 不可用。

当前相机 ABI 3.0 新增逐帧冻结的 ISP `exposure` 观测，保留 frame-info 前缀尺寸读取，但 SONAME 已切到 `libsc132.so.3`，旧二进制必须重建；估计值不证明该帧实际生效曝光。FSYNC 默认关闭，仅 `800/1600Hz` 可开启，提供触发—样本唯一关联而非曝光同步。软件版本相同不证明包内功能相同：按 [changelog](../changelog.md) 区分未发布更新，并核对 manifest、头文件和实际库。

## 出厂系统镜像与目标板兼容性

V2 匹配 BSP/系统镜像和恢复通道的公开资料待确认，当前没有公开镜像下载或已确认的烧录步骤；见[系统烧录](../ops/system-flashing.md)。不要将未确认适用于当前硬件的镜像写入设备。

## 版本查询与整包匹配

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

部署时按整包更新和校验：non-ROS使用`manifest.sha256`，ROS2 install使用archive checksum和runtime `abi_manifest.sha256`。不要只替换单个可执行文件或单个`.so`；运行包中的程序、头文件和运行库应来自同一经验证的软件包，不能根据文档修订号判断软件或 ABI 是否匹配。
