# 版本更新记录

本文件记录 RoboBaton 4P 公开交付的用户可见更新。版本号遵循 [Semantic Versioning 2.0.0](https://semver.org/)；SO 的 SONAME/ABI 版本与产品发布版本独立，例如 `libicm42688.so.2` 中的 `2` 表示 ABI major，不等于产品版本。

## v1.0.0 - 2026-08-06


### 新增

- non-ROS四目相机H.264/H.265 RTSP示例，默认四路`1280x1088@30fps`。
- `25/30/40/50fps`离散功能配置；`60fps`保留为显式high-rate stress档。
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

- 四路 `60fps` 仅为 stress 档，不是 V1 稳定发布 profile；高负载场景下可能出现接收端吞吐退化。
- V1 稳定性和正式交付主门使用四路 `30fps`。
- 四路 `trigger=none` 和 `vin_lpwm` 仍未纳入 V1 稳定验收；当前稳定验证模式为 `software_gpio`。
- `180`度旋转只在`30fps`配置下受支持。
