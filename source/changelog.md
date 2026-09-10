# 版本更新记录

本文件记录 RoboBaton 4P 公开交付的用户可见更新。版本号遵循 [Semantic Versioning 2.0.0](https://semver.org/)；SO 的 SONAME/ABI 版本与产品发布版本独立，例如 `libicm42688.so.2` 中的 `2` 表示 ABI major，不等于产品版本。

## 1.2.0 - 2026-09-09

### 变更

- 统一主仓、non-ROS、ROS2 和公开文档的产品版本为 `1.2.0`，并重新生成对应的运行包版本信息。
- 重新构建并同步 ICM42688、SC132、PRRTSP AArch64 发布库；ICM ABI 2.1、SC132 ABI 2.0、PRRTSP ABI 2.0 及各自 SONAME 保持不变。
- 运行包、程序 `--version` 输出和版本匹配说明同步更新为 `1.2.0`。

## 1.1.1 - 2026-09-08


### 新增

- 相对v1.0.0，non-ROS `sensor_demo` 新增ROS1 bag v2.0保存，包含四路同步JPEG图像、相机信息、帧元数据、独立IMU和session状态。
- non-ROS `sensor_demo` 新增互斥的H.264 MP4 session保存模式，输出四路MP4、四路精确timestamp CSV、独立IMU CSV、相机参数、session status和publication receipt。
- 新增MP4 session到时间戳命名JPEG的Host离线转换工具，支持complete与recovery源且不会把partial升级为complete。
- ICM real SO从`libicm42688.so.2.0.0`提升为`libicm42688.so.2.1.0`，ABI minor为2.1；SONAME继续为`libicm42688.so.2`。既有函数保留`ICM42688_X5_2.0`节点，新增`icm42688_get_runtime_health()`使用`ICM42688_X5_2.1`节点，sample/config布局不变。
- 新增[保存数据应用说明](save-data-application-guide.md)，覆盖整包校验、ROS1 bag/MP4配置、优雅退出、验收、离线转换和恢复。
- non-ROS 公开仓新增交互式 `scripts/wifi_setup.sh`，支持板载 Wi-Fi AP/STA 配置、状态查看、停用和可选开机恢复；新增[板载 Wi-Fi 配置](wifi-configuration.md)使用说明。

### 改进与修复

- 强化ROS1 bag和MP4的临时写入、partial/quarantine、原子no-replace发布、receipt、目录耐久化和崩溃恢复。
- 强化SC132、RTSP、IMU、writer和外部工具的停止顺序、callback ownership、超时进程组清理及错误传播。
- MP4 complete严格绑定完整四路inventory、四路等量非零帧、IMU final health和status/receipt identity。

### 已知限制与发布门

- ROS1 bag与MP4当前只能选择一种保存模式，不能在同一进程同时开启。
- MP4只支持H.264完整四路，不支持frame skip；板端需要`ffmpeg`，离线提取需要Host完整`ffmpeg`/`ffprobe`。
- v1.1.1正式支持non-ROS相机和RTSP的`25/30/40/50/60fps`档位，以及`25/50/100/200/500/1000/2000Hz` IMU档位；ROS2相机当前支持`25/30fps`。40/50/60fps属于显式高帧率配置，CPU占用过高时可能出现少量丢帧。
- `trigger_mode=none` 仅用于显式 free-run 诊断，不属于 V1 稳定发布合同；V1 验证模式为 `software_gpio`。
- non-ROS正式stress/压力矩阵覆盖上述全部公开帧率；历史证据仍按原始帧率保留，不替代当前发布门。

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
