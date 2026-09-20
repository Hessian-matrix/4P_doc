# 版本更新记录

本文件记录 RoboBaton 4P 公开交付的用户可见更新。版本号遵循 [Semantic Versioning 2.0.0](https://semver.org/)；SO 的 SONAME/ABI 版本与产品发布版本独立，例如 `libicm42688.so.2` 中的 `2` 表示 ABI major，不等于产品版本。

## 1.3.1 - 2026-09-20

### 新增

- 运行包新增 `sensor_demo` 开机自启动脚本 `start_sensor_demo.sh`：无参数前台启动，`enable`/`disable`/`status` 管理开机自启动。自启动通过板端 `/userdata/startup.sh` 实现（系统 `S99auto_startup` 在 `/userdata` 挂载后执行），脚本只追加/删除自己带标记的块，可与 `wifi_setup.sh` 等内容共存；用法见{ref}`non-ROS Demo 使用：开机自启动 <non-ros-autostart>`。
- 发布板端软件 `v1.3.0` 配套的出厂系统镜像与烧录工具，支持出厂系统恢复和系统版本升级；镜像获取、烧录步骤与验收见{ref}`修复和升级：系统烧录 <system-flashing>`。

## 1.3.0 - 2026-09-16

### 新增

- 发布 non-ROS `mosaic_rtsp_demo`：把四路 SC132 `1280x1088` NV12 帧在 CPU 内合成为 `2560x2176` 单帧，经 `libprrtsp` 输出固定 H.264 RTSP；公开帧率集合 `25/30/40/50/60fps`，默认 `30fps`，固定地址 `rtsp://<X5_IP>:558/PRR`。应用细节、退出统计与资源占用见{ref}`non-ROS Demo 使用：四路拼接 RTSP（mosaic_rtsp_demo） <non-ros-mosaic>`。

### 改进与修复

- 发布更新版 SC132GS ISP 调优参数 `patch/sc132gs_tuning.json`，改善部分光照场景下的图像质量表现；使用方法与回滚见{ref}`修复和升级：ISP 图像质量修复 <isp-image-quality-fix>`。

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
- 新增[保存数据](save-data-guide.md)，覆盖整包校验、ROS1 bag/MP4配置、优雅退出、验收、离线转换和恢复。
- non-ROS 公开仓新增交互式 `scripts/wifi_setup.sh`，支持板载 Wi-Fi AP/STA 配置、状态查看、停用和可选开机恢复；新增[Wi-Fi 配置](wifi-configuration.md)使用说明。

### 改进与修复

- 强化ROS1 bag和MP4的临时写入、partial/quarantine、原子no-replace发布、receipt、目录耐久化和崩溃恢复。
- 强化SC132、RTSP、IMU、writer和外部工具的停止顺序、callback ownership、超时进程组清理及错误传播。
- MP4 complete严格绑定完整四路inventory、四路等量非零帧、IMU final health和status/receipt identity。

### 已知限制与发布门

- ROS1 bag与MP4当前只能选择一种保存模式，不能在同一进程同时开启。
- MP4只支持H.264完整四路，不支持frame skip；板端需要`ffmpeg`，离线提取需要Host完整`ffmpeg`/`ffprobe`。
- v1.1.1 non-ROS相机与RTSP的公开帧率集合为`25/30/40/50/60fps`，默认`30fps`；ROS2图像节点为`25/30fps`。IMU支持`25/50/100/200/500/1000/2000Hz`。保存后端的参数接受、完整性和压力边界见{ref}`数据保存：帧率与压力边界 <persistence-fps-boundary>`。
- `trigger_mode=none` 仅用于显式 free-run 诊断，不属于 V1 稳定发布合同；V1 验证模式为 `software_gpio`。
- non-ROS ROS1 bag 与 H.264 MP4 的完整保存判据和逐帧率边界见[保存数据](save-data-guide.md)；历史证据仍按原始帧率保留，不替代当前发布门。

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
