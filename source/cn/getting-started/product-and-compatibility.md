# 产品版本与兼容性

本页说明 RoboBaton 4P V2 当前源码、non-ROS/ROS2 demo 与运行环境的匹配关系。技术事实以公开头文件、配置、VERSION 和运行包 manifest 为准。

## 文档与软件版本

当前文档修订号、软件发布版本和统一版本定义见 [发布、授权与支持](../release-and-support.md#文档版本政策)。文档修订不要求软件版本同步递增。

硬件标识、软件 `2.0.0`、文档和 SO ABI 独立识别。参数受支持不等于所有模式/负载/时长已通过；当前高帧率、压力、长录及外设限制见{ref}`能力与验证边界 <capability-verification-boundary>`。

当前 IMU 使用内核 IIO 公共 ABI 6.0：实体 `libicm42670.so.6.0.0`、SONAME `libicm42670.so.6`，九个导出均为 `ICM42670_X5_6.0`。设备必须已绑定匹配的内核 IIO V4 capture 模块；现有 V2/V3 模块即使 host 模式也不兼容。全部 consumer 与匹配头文件/库成套重建并清除旧 major 工件，不建立跨 major 链接。启动 `camera_timestamp_path=observer|official`（默认 observer）与 `imu_timestamp_mode=host|tmst`（默认 host）提供四种组合，共用同一二进制和同一 IIO 读取/owner，停止/重启后切换。host 保留 MONOTONIC，物理误差未知；tmst 依据内核 FIFO/UI 跳变证据增加有界仿射 RAW sample 映射，同时保留 MONOTONIC，`200µs` 计算 admission 不是物理精度。official 相机时间是物理上界未知的同帧 IRQ 派生估计，绝不是 SIF observer 结果。保存/ROS2 将所选原生模式桥接到 realtime 并保留原生证据。无用户态 SPI/spidev、FSYNC 关联或回退。见 [non-ROS 使用](../usage/non-ros-demo.md)、[ROS2 使用](../usage/ros2-demo.md) 与[数据合同](../development/data-contracts.md)。当前 non-ROS HO 短窗证据及未验收范围见{ref}`能力与验证边界 <capability-verification-boundary>`。不声明四组合实板验收；软件、文档、ABI 与发布状态独立。

| 交付物 | 用户入口 |
|---|---|
| 文档 | 本站与 `4P_doc` 仓库。 |
| non-ROS demo/运行包 | `/root/demo`，来自 `RoboBaton_4p_demo` 的 `demo/`。 |
| ROS2 package/install | `/root/ros2_demo/install`，包名 `robobaton_4p_ros2_demo`。 |


## 功能与运行目录

| 路径 | 主要能力 | 运行目录 | 备注 |
|---|---|---|---|
| non-ROS | 四路 RTSP、IMU、UART、互斥 bag/MP4 保存、IMU 时钟元数据 与曝光观测 | `/root/demo` | RTSP `554..557/PRR`，H.264 默认、H.265 可选；四路拼接示例为 `558/PRR`。 |
| ROS2 | raw/compressed 图像、CameraInfo、逐帧曝光观测、IMU、温度与IMU 时钟元数据 | `/root/ros2_demo/install` | ROS2 Humble；compressed 使用 X5 `MEDIA_CODEC_ID_JPEG` 硬件编码；不提供 RTSP。 |

两条路径不要混用目录、头文件或 `.so`，同一时间只运行一个占用 camera/VIO/编码资源的应用。

## 运行要求

| 项目 | 要求 |
|---|---|
| 板端平台 | X5；相机运行依赖 `cam-service`，不建议停止或重配该服务。 |
| ROS2 | Humble underlay；通过 `robobaton_ros2_env.bash` 加载环境。 |
| 交叉编译 | 只在开发机使用 X5 交叉编译包；不建议在 X5 板端原生编译。 |
| non-ROS相机配置 | 默认`1280x1088@30fps`；支持`25/30/40/50/60fps`；输出画布 `1280x1088`/`640x480`/`720x480`/`1280x720`。 |
| Trigger | 所有相机入口仅支持 `vin_lpwm`（VIN LPWM 硬件触发）；不提供 free-run 或软件 GPIO 触发。 |
| 权限与调度 | 仅相机 `observer` 需要只读 `/dev/mem` 与 `SCHED_FIFO/60`；`official` 不启动该 observer。IMU owner/consumer 实时线程需要调度权限，失败拒绝启动；详见[数据合同](../development/data-contracts.md)。 |

相机仅完整四路或单颗诊断，不支持 2/3 路；旋转 `180` 仅支持 `30fps`。单颗诊断已由用户确认，不扩展为所有模式或压力负载验收。

ROS2 路径不提供 RTSP；需要 RTSP 时使用 non-ROS 路径。ROS2 不提供 TF、外参、相机内参或畸变标定输出；CameraInfo 只有宽高，IMU orientation 不可用。独立 non-ROS `panorama_demo` 可读取匹配设备的 KB4／外参标定进行环视投影，但不发布 TF、不自动标定，也不证明示例参数适用于任意设备，见{ref}`环视用法 <non-ros-panorama>`。

相机 ABI 3.0 的 `exposure` 冻结固定单硬件帧关联估计：采集原始硬件帧 N 时取得的 getter 只估计相邻 N+1（允许 uint32 回绕），不使用归一化组号或 SDK 源帧号匹配。无前驱、硬件缺口或无效前驱查询时不可用且全零，来源保留更早 getter 原值；consumer 原样转发不得再移一帧。估计不认证实际生效曝光或已测物理误差上界。frame-info 前缀尺寸读取、公开布局、SONAME、软件版本和默认触发 stamp 不变；显式中点模式使用匹配估计且仍在不可用时停止。时间戳仍由启动 selector 选择 observer 或 official；详见[数据合同](../development/data-contracts.md)。软件版本相同不证明包组成相同，须核对 [changelog](../changelog.md)、manifest、头文件与实际库；完整状态/warmup 合同见[逐帧曝光观测](../development/data-contracts.md#逐帧曝光观测)。

固定 N→N+1 只是估计关联规则；真实 AE 的有效滞后可能不同，不提供逐帧实际应用曝光保证或 AE 验收结论。

## 出厂系统镜像与目标板兼容性

V2 系统镜像已完成制作并已有烧录启动的设备；当前匹配镜像预装 non-ROS、ROS2 Humble、IIO capture 模块和系统依赖，仅 non-ROS 默认自启。当前固件支持按住 SW1 上电或复位，再通过 USB3 Fastboot 使用 XBurn 烧录，无需连接调试串口，具体操作见[系统烧录](../ops/system-flashing.md)。镜像下载：[4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz)；发布包 SHA-256 与适用硬件须在烧录前向产品支持核对。镜像完成不等于全部接口验收；烧录前须确认镜像适用于当前硬件并备份数据，不要将未确认兼容的镜像写入设备。

以上镜像制作／启动记录不表示已发布下载或已有设备包含当前 ABI6／IIO V4、曝光关联或环视源码更新。升级前须核对匹配 V4 模块、公开头、SO、consumer 与 manifest；应用包不升级模块，原 V3／ABI5 验证不认证新组成。

## 版本查询与整包匹配

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
/root/ros2_demo/install/robobaton_ros2_env.bash \
  /root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/robobaton_ros2_env.bash \
  /root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

部署时按整包更新和校验：non-ROS使用`manifest.sha256`，ROS2 install使用archive checksum和runtime `abi_manifest.sha256`。不要只替换单个可执行文件或单个`.so`；运行包中的程序、头文件和运行库应来自同一经验证的软件包，不能根据文档修订号判断软件或 ABI 是否匹配。
