# 版本更新记录

本文件记录 RoboBaton 4P 公开交付的用户可见更新。版本号遵循 [Semantic Versioning 2.0.0](https://semver.org/)；SO 的 SONAME/ABI 版本与产品发布版本独立，例如 `libicm42688.so.2` 中的 `2` 表示 ABI major，不等于产品版本。

## 1.1.0 - 未发布

> 本节是下一minor版本候选，不代表已正式发布。合并正式版本前必须同步四仓`VERSION`、重新构建运行包，并通过Host与目标板发布门。

### 新增

- 相对v1.0.0，non-ROS `sensor_demo` 新增ROS1 bag v2.0保存，包含四路同步JPEG图像、相机信息、帧元数据、独立IMU和session状态。
- non-ROS `sensor_demo` 新增互斥的H.264 MP4 session保存模式，输出四路MP4、四路精确timestamp CSV、独立IMU CSV、相机参数、session status和publication receipt。
- 新增MP4 session到时间戳命名JPEG的Host离线转换工具，支持complete与recovery源且不会把partial升级为complete。
- ICM real SO从`libicm42688.so.2.0.0`提升为`libicm42688.so.2.1.0`，ABI minor为2.1；SONAME继续为`libicm42688.so.2`。既有函数保留`ICM42688_X5_2.0`节点，新增`icm42688_get_runtime_health()`使用`ICM42688_X5_2.1`节点，sample/config布局不变。
- 新增[保存数据应用说明](save-data-application-guide.md)，覆盖整包校验、ROS1 bag/MP4配置、优雅退出、验收、离线转换和恢复。

### 改进与修复

- 强化ROS1 bag和MP4的临时写入、partial/quarantine、原子no-replace发布、receipt、目录耐久化和崩溃恢复。
- 强化SC132、RTSP、IMU、writer和外部工具的停止顺序、callback ownership、超时进程组清理及错误传播。
- MP4 complete严格绑定完整四路inventory、四路等量非零帧、IMU final health和status/receipt identity。

### 已知限制与发布门

- ROS1 bag与MP4当前只能选择一种保存模式，不能在同一进程同时开启。
- MP4只支持H.264完整四路，不支持frame skip；板端需要`ffmpeg`，离线提取需要Host完整`ffmpeg`/`ffprobe`。
- ROS1 bag的30fps是完整保存硬门、40fps是扩展目标，50/60fps压力下可明确降级为partial，其中60fps是bag的stress档。H.264 MP4的25/30/40/50/60fps均为稳定发布矩阵，正常case必须complete；目标板矩阵通过前不得发布1.1.0。

## v1.0.0 - 2026-08-06


### 新增

- non-ROS四目相机H.264/H.265 RTSP示例，默认四路`1280x1088@30fps`。
- `25/30/40/50/60fps`离散相机与RTSP功能配置；保存后端按各自合同判定，ROS1 bag 60fps的stress策略不扩展到MP4。
- camera ID 0/1/2/3单路诊断、0/90/180/270度旋转及配置前置校验。
- ICM-42688 FIFO/TMST时间戳、25至2000Hz离散ODR和non-ROS联合`sensor_demo`。
- ROS2 四路 NV12 raw、X5 硬件 JPEG compressed image 和 IMU topic 发布。
- ROS2 运行环境脚本、FastDDS SHM 配置、发布率指标和 IMU 频率检查工具。
- ROS2 install 根目录环境脚本 `robobaton_ros2_env.bash`，统一加载 underlay、overlay、FastDDS SHM profile 和日志缓冲设置。
- 所有自研SO提供`*_get_version()` C ABI；交付可执行文件提供无需硬件的`--version`。
- UART1/UART7 3.3V 硬件通信已通过 V1 验收；两个 UART 3.3V 供电脚对外设供电合计额定边界为 `500 mA`。


### 修复

- 修复IMU高频终端输出对采集线程造成背压的问题。
- 修复SC132 trigger匹配失败后四路frame-set停止及关闭生命周期不完整的问题。
- 修复SC132 retained frame、callback和worker关闭顺序中的所有权风险。
- 修复RTSP external NV12帧租约、close重试和错误状态传播问题。
- 修复 ROS2 相机/IMU 时间戳映射、发布率诊断和高频 IMU topic 检查方式。
- 将 ROS2 compressed image 从 CPU 压缩路径切换到 X5 硬件 JPEG codec，降低默认联合负载。
- 修复 FastDDS 配置 hook 不可重定位和高吞吐本机传输配置问题。

### 已知限制

- 四路60fps属于受支持高吞吐配置；客户端接收/解码能力不足仍可能造成播放端退化。ROS1 bag全量JPEG保存的60fps stress限制在1.1.0中单独说明。
- V1 稳定性和正式交付主门使用四路 `30fps`。
- 四路 `trigger=none` 和 `vin_lpwm` 仍未纳入 V1 稳定验收；当前稳定验证模式为 `software_gpio`。
- `180`度旋转只在`30fps`配置下受支持。
