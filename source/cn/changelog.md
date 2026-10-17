# 版本更新记录

本文件记录 RoboBaton 4P 公开交付的用户可见更新，版本定义统一遵循 [文档版本政策](release-and-support.md#文档版本政策)。本页文档修订号不自动改变软件版本，也不等于 SO 的 SONAME/ABI 版本。

## 未发布

- IMU CLI、保存和 ROS2 stamp 直接保留 `CLOCK_MONOTONIC_RAW` 样本时间；bag record time 使用 RAW，不再提供 RAW→realtime 冻结 offset。使用旧 UTC epoch 的消费端必须迁移，不能与 ROS `now()` 或 `/clock` 直接比较。
- 相机仍保留 SIF 硬件触发沿捕获，SIF→RAW 映射尚未实现；本次消费链切换不代表相机/IMU 已同域或已硬件同步。

## 2.0.0 - 2026-10-15

V2.0.0 发布：软件与文档版本统一至 2.0.0，默认触发模式切换为 LPWM。

- 所有相机采集入口仅支持 `vin_lpwm`（VIN LPWM 硬件触发），移除软件 GPIO 与 free-run 路径。
- 相机时间戳保留随帧传播的 `trig_tv` 触发捕获（SIF 原生计数器域），不伪装为 RAW/UTC；相机与 IMU 共线不等于样本/曝光已关联。
- V2 镜像标记待发布；删除 V1 TF/风扇设备树修复、ISP 参数替换和 UART7→PPS 复用步骤，改为默认独立 PPS IO。旧产品/接口图标注发布前替换；相机映射、FOV、出厂网络和串口电平不变。
- PTP master 的 PHC 使用 PTP/TAI 时间尺度，`phc2sys -w` 跟随 `ptp4l` 的 UTC offset，不再使用 `-O 0`；启用硬件 `hwts_filter full`，使 master 正确接收 Delay_Req 并返回 Delay_Resp。master/报文通过不代表 slave 锁定或绝对 UTC 精度。
- bag 使用独立、非递减的统一记录时钟；图像和 CameraInfo 保留相机捕获时间，IMU 保留样本时间，session 配置分别声明三个时间域，避免跨域数值比较破坏记录顺序。缺失 LPWM 捕获时由 dispatcher 串行投递至多一次终止回调，支持回调内请求停止。

## 1.3.3 - 2026-10-11

本次为 V2 硬件迁移的中英文文档修订；软件 VERSION 不变，不代表 V2 全功能或整机验收通过。

- 当前 IMU 指南/API/示例切换至 ICM-42670-P、`icm42670_*`、`icm42670_driver.h`；real SO `libicm42670.so.2.0.0`、SONAME `libicm42670.so.2`、节点 `ICM42670_X5_2.0`。
- 原生 ODR 为 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；旧 `500/1000/2000Hz` 明确拒绝，需用户显式迁移配置。
- 相机 producer 解析触发控制器 `34130000.gpio` offset `0`，INT1 为 `34120000.gpio` offset `8`；IMU FSYNC 与相机触发共网不代表相机/IMU 硬件对齐。
- 时间字段按新公开头文件说明；V2 pinout、电气、物理映射、IMU 方向及照片仍标记待确认。历史 V1 下载 URL、工件身份和以下 changelog 原样保留，不构成 V2 兼容或验收承诺。

## 1.3.2 - 2026-10-10

本次为 1.3 系列内的构建与文档修订，各软件版本号保持不变。

### 改进与修复

- 修正 ROS2 显式工具链参数优先级及运行库来源，支持从独立 non-ROS 仓库生成并验证运行包。
- 补充 Ubuntu 22.04 x86_64 主机准备、五个 non-ROS 示例和 ROS2 节点/插件的完整构建步骤，见 [公开 Demo 源码编译](development/open-source-build.md)。构建与包验证不替代板端硬件验收。
- 统一文档版本定义与维护约束；文档修订号独立于软件版本，中英文构建从 `4P_doc/VERSION` 读取同一修订号。

## 20261009 工具链 - 2026-10-10

- 发布 [x5_4cam_cross_toolchain_20261009.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20261009.tar.gz)，补齐目标 ROS Humble、image_transport/pluginlib 及环境入口，固定包内编译器和 sysroot 查找路径。大小、SHA-256 和用法见 [公开 Demo 源码编译](development/open-source-build.md)。

## 1.3.1 - 2026-09-20

### 新增

- 运行包新增 `sensor_demo` 开机自启动脚本 `start_sensor_demo.sh`：无参数前台启动，`enable`/`disable`/`status` 管理开机自启动。自启动通过板端 `/userdata/startup.sh` 实现（系统 `S99auto_startup` 在 `/userdata` 挂载后执行），脚本只追加/删除自己带标记的块，可与 `wifi_setup.sh` 等内容共存；用法见{ref}`non-ROS Demo 使用：开机自启动 <non-ros-autostart>`。
- 发布板端软件 `v1.3.0` 配套的出厂系统镜像与烧录工具，支持出厂系统恢复和系统版本升级；镜像获取、烧录步骤与验收见{ref}`修复和升级：系统烧录 <system-flashing>`。

## 1.3.0 - 2026-09-16

### 新增

- 发布 non-ROS `mosaic_rtsp_demo`：把四路 SC132 `1280x1088` NV12 帧在 CPU 内合成为 `2560x2176` 单帧，经 `libprrtsp` 输出固定 H.264 RTSP；公开帧率集合 `25/30/40/50/60fps`，默认 `30fps`，固定地址 `rtsp://<X5_IP>:558/PRR`。应用细节、退出统计与资源占用见{ref}`non-ROS Demo 使用：四路拼接 RTSP（mosaic_rtsp_demo） <non-ros-mosaic>`。

### 改进与修复

- 发布更新版 SC132GS ISP 调优参数 `patch/sc132gs_tuning.json`，改善部分光照场景下的图像质量表现。

## 1.2.0 - 2026-09-14

### 新增

- non-ROS `cam_demo`/`sensor_demo` 支持 VSE 硬件整幅缩放输出画布：`640x480`、`720x480`、`1280x720`，两种轴向写法均合法；缩放不改变 FOV，软件旋转（180/270）在缩放之后由 Nano2D 完成，外部旋转 `90/270` 的交付画布宽高交换。
- ROS2 图像节点帧率扩展到 `25/30/40/50/60fps`（默认 `30fps`），与 non-ROS/RTSP 公开集合对齐。
- `libsc132` real SO 从 `libsc132.so.2.0.0` 升级为 `libsc132.so.2.0.1`；SONAME 仍为 `libsc132.so.2`，ABI 节点 `LIBSC132_2.0` 不变。
- 文档增加 NTP、PPS 输入/UART7 IO 复用及 X5 master + Mid-360 slave 的 PTP 参考配置；PPS 固定使用当前产品组合中的 `/dev/pps2`。
- 更新部署校验、公开 API、版本兼容入口和时间同步边界。保存模式逐帧率的完整性与压力（stress）边界统一以{ref}`数据保存：帧率与压力边界 <persistence-fps-boundary>`为准。

## 1.1.1 - 2026-09-08


### 新增

- 相对v1.0.0，non-ROS `sensor_demo` 新增ROS1 bag v2.0保存，包含四路同步JPEG图像、相机信息、帧元数据、独立IMU和session状态。
- non-ROS `sensor_demo` 新增互斥的H.264 MP4 session保存模式，输出四路MP4、四路精确timestamp CSV、独立IMU CSV、相机参数、session status和publication receipt。
- 新增MP4 session到时间戳命名JPEG的Host离线转换工具，支持complete与recovery源且不会把partial升级为complete。
- ICM real SO从`libicm42688.so.2.0.0`提升为`libicm42688.so.2.1.0`，ABI minor为2.1；SONAME继续为`libicm42688.so.2`。既有函数保留`ICM42688_X5_2.0`节点，新增`icm42688_get_runtime_health()`使用`ICM42688_X5_2.1`节点，sample/config布局不变。
- 新增[保存数据](usage/save-data-guide.md)，覆盖整包校验、ROS1 bag/MP4配置、优雅退出、验收、离线转换和恢复。
- non-ROS 公开仓新增交互式 `scripts/wifi_setup.sh`，支持板载 Wi-Fi AP/STA 配置、状态查看、停用和可选开机恢复；新增[Wi-Fi 配置](getting-started/wifi-configuration.md)使用说明。

### 改进与修复

- 强化ROS1 bag和MP4的临时写入、partial/quarantine、原子no-replace发布、receipt、目录耐久化和崩溃恢复。
- 强化SC132、RTSP、IMU、writer和外部工具的停止顺序、callback ownership、超时进程组清理及错误传播。
- MP4 complete严格绑定完整四路inventory、四路等量非零帧、IMU final health和status/receipt identity。

### 已知限制与发布门

- ROS1 bag与MP4当前只能选择一种保存模式，不能在同一进程同时开启。
- MP4只支持H.264完整四路，不支持frame skip；板端需要`ffmpeg`，离线提取需要Host完整`ffmpeg`/`ffprobe`。
- v1.1.1 non-ROS相机与RTSP的公开帧率集合为`25/30/40/50/60fps`，默认`30fps`；ROS2图像节点为`25/30fps`。IMU支持`25/50/100/200/500/1000/2000Hz`。保存后端的参数接受、完整性和压力边界见{ref}`数据保存：帧率与压力边界 <persistence-fps-boundary>`。
- `trigger_mode=none` 仅用于显式 free-run 诊断，不属于 V1 稳定发布合同；V1 验证模式为 `software_gpio`。
- non-ROS ROS1 bag 与 H.264 MP4 的完整保存判据和逐帧率边界见[保存数据](usage/save-data-guide.md)；历史证据仍按原始帧率保留，不替代当前发布门。

## v1.0.0 - 2026-08-06


### 新增

- non-ROS四目相机H.264/H.265 RTSP示例，默认四路`1280x1088@30fps`。
- 初始版本暴露`25/30/40/50/60fps`离散相机与RTSP配置。
- camera ID 0/1/2/3单路诊断、0/90/180/270度旋转及配置前置校验。
- ICM-42688 FIFO/TMST时间戳、`25/50/100/200/500/1000/2000Hz`离散ODR和non-ROS联合`sensor_demo`。
- ROS2 四路 NV12 raw、X5 硬件 JPEG compressed image 和 IMU topic 发布。
- ROS2 运行环境脚本、FastDDS SHM 配置、发布率指标和 IMU 频率检查工具。
- ROS2 install 根目录环境脚本 `robobaton_ros2_env.bash`，统一加载 underlay、overlay、FastDDS SHM profile 和日志缓冲设置。
- 所有自研SO提供`*_get_version()` C ABI；交付可执行文件提供无需硬件的`--version`。
- UART1/UART7 3.3V 硬件通信已通过 V1 验收；两个 UART 3.3V 供电脚对外设供电合计额定边界为 `500 mA`。

### 已知限制

- 40/50/60fps可用，但是当系统CPU压力过高的时候，可能会出现掉帧的情况，尤其是60fps。
- V1 稳定性和正式交付默认使用四路 `30fps`。
- 四路 `trigger` 当前稳定验证模式为 `software_gpio`。
- `180`度旋转只在`30fps`配置下受支持。
