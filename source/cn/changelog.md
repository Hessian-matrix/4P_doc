# 版本更新记录

本文件记录 RoboBaton 4P 公开交付的用户可见更新，版本定义统一遵循 [文档版本政策](release-and-support.md#文档版本政策)。本页文档修订号不自动改变软件版本，也不等于 SO 的 SONAME/ABI 版本。

## 未发布

### 改进与修复

- 新增独立 `can_demo`：默认经典 CAN，显式 `--fd` 支持最长 64 字节 FD 发送和经典/FD 混合接收，`--brs` 开启 TX 数据段速率切换，标准/扩展 ID 均可用。FD 发送采用可精确编码的长度且不隐式补零；接入构建、完整运行包和校验。接口配置仍由用户/BSP 完成；应用支持不代替 BSP 长载荷完整性验收，本机回环与排队成功不构成外部总线验收。
- 相机、IMU、CLI、保存和 ROS2 对外传感器时间戳统一为 `CLOCK_REALTIME` 系统时间。相机通过有界 VSYNC 交叉采样及同计数器触发差值还原硬件触发沿，不使用 IRQ/到帧时间兜底；缺少有效映射即停止。
- RAW 仅用于内部映射/配组；每次发布刷新 realtime 桥接，运行中校时允许回拨。bag record time 独立读取 realtime，不再强制递增，chunk index 按时间排序。统一时间域不代表相机/IMU 样本或曝光已硬件同步；旧 SIF/RAW 时间消费端必须成套迁移头文件、SO 和应用。
- 新增显式开启的 LPWM→ICM-42670-P FSYNC 触发—样本关联：硬件 FIFO 标记、相邻绝对 TMST 有界重建、RAW 唯一候选匹配及缺失/歧义状态。non-ROS `--fsync`、YAML/ROS2 `imu.fsync_enabled` 默认关闭，仅支持 `800/1600Hz`；保留 `200µs` admission 策略，不保证所有触发均匹配或曝光同步。结果传至 stdout、bag `/robobaton/fsync`、MP4 `fsync.jsonl` 和 ROS2 同名 topic。
- ICM ABI minor 为 `2.1`：新增独立 FSYNC callback 使用 `ICM42670_X5_2.1`，原函数节点、结构尺寸、real SO 文件名及 SONAME 不变。相机 frame-set reserved 字段提供 RAW 触发、组不确定度与 generation，外部时间仍为 realtime。
- 关联结果保留逐路原始 realtime stamp，支持与 ROS2 Image/CameraInfo 精确核对；整数 JSON 需无损解析。MP4 timestamp CSV 是微秒量化的组触发时间（以 ns 表示），逐路原始值见开启 FSYNC 后的 `fsync.jsonl`，不再宣称 CSV 为逐路原始纳秒时间。
- 修复跨优先级队列锁导致的采集阻塞；IMU consumer/ROS2 发布使用显式实时调度，SPI 为 `10MHz`，INT1 使用 `100µs` 异步复位脉冲。启动失败释放资源，最终健康快照保留尾部无效 FIFO 包计数。保持相位、唯一匹配和 `200µs` 检查；高负载仍受系统 IRQ/debug 与订阅端调度约束，不保证每个触发或任意负载零丢失。
- 最终 IMU 健康行增加 timing drop 和 FSYNC captured/dropped 总数；non-ROS 终止摘要使用 stop 后的最终计数，无效 FIFO 包与 timing 拒绝重叠时不再漏计。
- INT1→RAW 转换保留沿时观测历史，并按读取窗口与调速距离的完整不确定度选择证书；独立实时 observer 在 SPI/callback 阻塞期间继续观测，启动握手及优先级继承锁保证初始化和历史顺序，原相位与发布门限不变。
- 相机 ABI 2.2 增加逐帧冻结的 ISP 曝光观测，保留旧 frame-info 前缀读取，SONAME 不变；bag/tee 元数据、MP4 `exposure.jsonl` 与 ROS2 `/robobaton/camN/exposure` 同步交付。估计值与不可用状态分开，不保证实际生效帧或误差上界，不改变触发时间戳、不宣称真实曝光中点。捕获 observer 继承允许 CPU 集合，不再强制 CPU0。
- 修复 sensor 探测阶段重复申请 MCLK 引用未释放的问题；探测引用在 VIN 接管前释放，不清除历史遗留引用。相机捕获使用 FIFO/60 并正确处理扫描内 VSYNC 更新，INT1 observer 改为继承 CPU 集合的 FIFO/30，避免压过默认 GPIO IRQ。IMU 使用读取区间约束拟合、拒绝过宽观测污染解绕并保留更长沿时历史；`500µs`/`200µs` 门限不变，高负载仍可能显式拒绝或停止。
- IMU 区间观测与旧时钟证书矛盾时立即使旧证书失效，禁止继续发布；过宽观测仍只拒绝该次观测。修复 bag 收尾时最终编码帧在预取后入队被误判为顺序缺口的竞态，真实缺口继续报错。实时线程仍受系统调度与 IRQ 延迟约束，不修改系统实时配额，不承诺任意负载零丢失。
- 相机增加默认关闭的 `SC132_TEST_EXPOSURE_MIDPOINT`：测试时逐路时间戳为触发时间加半曝光时长，忽略触发到积分起点延迟；曝光不可用时停止采集。配组、触发 skew 和 FSYNC RAW 审计不变，关闭恢复原逻辑；仅当前源码重建库支持，不代表软件发布或硬件验收。

## 2.0.5 - 2026-10-21

本次补充 non-ROS 曝光中点测试开关的 YAML 配置说明；软件版本和 SO ABI 不变。

### 改进与修复

- non-ROS `sensor_demo` 增加 YAML `camera.test_exposure_midpoint`，随包及自动生成配置默认关闭，显式配置优先于环境变量；同步估算曝光中点、ROS1 bag 图像 stamp、重建及重启要求。

## 2.0.4 - 2026-10-21

本次为曝光中点测试开关的中英文文档修订；软件版本与 SO ABI 不变，不宣称已校准曝光中点或硬件验收。

### 改进与修复

- 同步曝光中点测试开关的中英文用法、默认关闭、估算公式、失败边界及组/逐路时间语义。

## 2.0.3 - 2026-10-21

本次补全公开图像输出结构的中英文 API 参考；仅修订文档，不改变软件版本、SO ABI 或硬件验收范围。

### 改进与修复

- 补全单帧、帧组、曝光观测及全部字段的单位、序号/时间语义、NV12 padding、引用生命周期和 ROS2/编码输出区别；数据合同增加直达链接。

## 2.0.2 - 2026-10-20

本次补充中英文 CAN 使用文档；软件版本仍为 `2.0.0`，不代表 CAN 硬件或整机验收通过。

### 改进与修复

- 补充 CAN 接线前置条件、手动接口配置、收发命令、参数、构建与部署入口。

## 2.0.1 - 2026-10-20

本次仅同步当前源码的用户文档，软件版本仍为 `2.0.0`；上述未发布功能不因文档修订变成正式软件发布或整机验收。

### 改进与修复

- 对齐 realtime 时间域、可选 FSYNC、相机 ABI 2.2 曝光观测与 IMU ABI 2.1；补齐默认配置、topic 和保存 sidecar 的使用入口。
- 区分 ISP 曝光估计、触发—样本关联、保存完整性及 DDS 实际送达；说明实时调度权限、最终健康计数和高负载拒绝边界。
- 更正 MP4/bag 帧率完整性保证、`max_skew_ns` 的曝光精度误读和系统回拨下的时间戳检查；历史版本记录不改写。

## 2.0.0 - 2026-10-15

V2.0.0 发布：软件与文档版本统一至 2.0.0，默认触发模式切换为 LPWM。

### 改进与修复

- 所有相机采集入口仅支持 `vin_lpwm`（VIN LPWM 硬件触发），移除软件 GPIO 与 free-run 路径。
- 相机时间戳保留随帧传播的 `trig_tv` 触发捕获（SIF 原生计数器域），不伪装为 RAW/UTC；相机与 IMU 共线不等于样本/曝光已关联。
- V2 镜像标记待发布；删除 V1 TF/风扇设备树修复、ISP 参数替换和 UART7→PPS 复用步骤，改为默认独立 PPS IO。旧产品/接口图标注发布前替换；相机映射、FOV、出厂网络和串口电平不变。
- PTP master 的 PHC 使用 PTP/TAI 时间尺度，`phc2sys -w` 跟随 `ptp4l` 的 UTC offset，不再使用 `-O 0`；启用硬件 `hwts_filter full`，使 master 正确接收 Delay_Req 并返回 Delay_Resp。master/报文通过不代表 slave 锁定或绝对 UTC 精度。
- bag 使用独立、非递减的统一记录时钟；图像和 CameraInfo 保留相机捕获时间，IMU 保留样本时间，session 配置分别声明三个时间域，避免跨域数值比较破坏记录顺序。缺失 LPWM 捕获时由 dispatcher 串行投递至多一次终止回调，支持回调内请求停止。

## 1.3.3 - 2026-10-11

本次为 V2 硬件迁移的中英文文档修订；软件 VERSION 不变，不代表 V2 全功能或整机验收通过。

### 改进与修复

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
