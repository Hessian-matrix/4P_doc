# 版本更新记录

本文件是RoboBaton 4P第一版公开交付的唯一版本更新记录。版本号遵循[Semantic Versioning 2.0.0](https://semver.org/)。SO的SONAME/ABI版本与产品发布版本独立：例如`libicm42688.so.2`中的`2`表示ABI major，不等于产品版本。

## 1.0.0 - 2026-08-03

### 新增

- non-ROS四目相机H.264/H.265 RTSP示例，默认四路`1280x1088@30fps`。
- `25/30/40/50fps`离散功能配置；`60fps`保留为显式high-rate stress档。
- camera ID 0/1/2/3单路诊断、0/90/180/270度旋转及配置前置校验。
- ICM-42688 FIFO/TMST时间戳、25至2000Hz离散ODR和non-ROS联合`sensor_demo`。
- ROS2四路NV12 raw、X5硬件JPEG compressed image和IMU topic发布。
- FastDDS SHM运行配置、发布率指标、typed C++ topic-rate probe和矩阵化证据。
- ROS2 install 根目录环境脚本 `robobaton_ros2_env.bash`，统一加载 underlay、overlay、FastDDS SHM profile 和日志缓冲设置。
- 所有自研SO提供`*_get_version()` C ABI；交付可执行文件提供无需硬件的`--version`。

### 修复

- 修复IMU高频终端输出对采集线程造成背压的问题。
- 修复SC132 trigger匹配失败后四路frame-set停止及关闭生命周期不完整的问题。
- 修复SC132 retained frame、callback和worker关闭顺序中的所有权风险。
- 修复RTSP external NV12帧租约、close重试和错误状态传播问题。
- 修复ROS2相机/IMU时间戳映射、发布率诊断和IMU probe QoS不兼容问题。
- 将ROS2 compressed image从CPU TurboJPEG切换到X5硬件JPEG codec，降低默认联合负载。
- 修复FastDDS配置hook不可重定位和高吞吐本机传输配置问题。

### 已知限制

- 四路`60fps`仅为stress档，不是V1稳定发布profile；C++持续观察压力下存在DDS/source接收退化。
- V1稳定性和正式交付主门使用四路`30fps`。
- 四路`trigger=none`和`vin_lpwm`仍需要匹配fixture完成正式验收；当前稳定验证模式为`software_gpio`。
- UART demo提供软件接口；物理pinout、电平和loopback需由最终硬件资料与fixture确认。
- `180`度旋转只在`30fps`配置下受支持。
