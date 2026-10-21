# 数据合同

本页记录用户可以依赖的数据格式、字段和时间语义。未公开的物理方位、坐标系、外参和硬同步能力均明确列为限制，不在文档中伪造。

## 相机图像与 RTSP

| 项目 | 合同 |
|---|---|
| `libsc132.so` / camera callback 原始帧 | NV12；native `1280x1088` 或 VSE 缩放 `640x480`/`720x480`/`1280x720`；旋转 `0/180` 宽高不变，`90/270` 宽高交换 |
| RTSP 对外流 | H.264 默认；支持 H.265 |
| FOV | 相机 A/B 保持水平 `148.4°`/`115.6°`、垂直 `126.6°`/`96.8°`、对角 `193.8°`/`157.2°`。 |
| camera FPS | 默认`30fps`，支持`25fps`、`30fps`、`40fps`、`50fps`和`60fps`；其他值在启动副作用前拒绝 |
| RTSP path | `/PRR` |
| 端口映射 | CAM1..CAM4 依次对应软件 cam0..cam3 与 `554/555/556/557`，物理映射与 V1 不变。 |

`libsc132.so` callback 暴露 NV12 原始帧，RTSP 客户端接收 H.264/H.265 编码流。帧信息包含 `width`、`height`、`stride`、`vstride`、Y/UV 虚拟/物理地址及 size。旋转 `90/270` 会交换宽高；消费端须依每帧元数据与 stride/size 处理对齐，不要假设紧凑 `1280x1088`。

完整 C 结构声明、逐字段解释、NV12 行布局与引用有效期见 {ref}`API 图像输出结构参考 <camera-output-structures>`。

## Frame Set 字段

| 字段 | 含义 |
|---|---|
| `camera_count` | 当前帧组内的相机数量，完整四目为 `4`。 |
| `group_id` | 帧组序号。 |
| `group_timestamp_ns` | 帧组时间戳，单位 `ns`。 |
| `max_skew_ns` | 当前帧组实际观测到的触发捕获时间跨度，单位 `ns`；测试曝光中点偏移不改变此值。 |
| `items[i].camera_id` | 软件 ID `0..3`，依次对应物理 CAM1..CAM4，与 V1 不变。 |
| `items[i].frame_id` | 归一化后的帧 ID。 |
| `items[i].timestamp_ns` | 单路帧时间戳，单位 `ns`。 |

`sc132_frame_set_config_t.max_skew_ns` 才是配组放行上限；默认值为 `10000000 ns（10ms）`，限制触发捕获值差异，不代表曝光对齐精度。

## Trigger 模式

| 模式 | 当前状态 | 公开合同 |
|---|---|---|
| `vin_lpwm` | 所有相机应用及底层库唯一支持的 VIN 硬件触发 | 相机与 IMU FSYNC 共用 LPWM IO；相机时间基准来自随帧传播的 `trig_tv` 硬件捕获，缺失则停止采集，不回退到到帧时间。 |

所有对外传感器时间戳统一为 `CLOCK_REALTIME` 系统时间（Unix epoch，单位 ns）。默认相机表示 LPWM 硬件触发沿，而不是到帧、IRQ 或曝光中心；显式测试模式见 {ref}`曝光中点测试开关 <test-exposure-midpoint>`。底层以 RAW 读数包围 SIF VSYNC 捕获寄存器更新，再减去同一 24 MHz 计数器中的 `VSYNC − trigger`，通过随帧 `trig_tv` 精确匹配历史记录。后台线程继承进程允许的 CPU 集合，使用 `SCHED_FIFO/60`，每轮休眠 `50µs`；扫描内更新使用本次扫描窗口，重读 TRIG 并确认 VSYNC 稳定。无法设置实时调度时启动失败。寄存器读取窗口超过 `500µs`、捕获缺失或匹配失败时停止采集，不回退到到帧时间。该实现需要 X5 固定寄存器映射、`/dev/mem` 只读访问及实时调度权限；窗口上限不是已验证的同步精度。

配组在内部触发 RAW 域完成，再为整组使用同一次新采样的 RAW→realtime 桥接；组时间为各路交付时间戳的最小值，`max_skew_ns` 始终表示触发捕获时间差异，不代表曝光或相机/IMU 对齐精度。non-ROS 诊断、RTSP 输入时间、保存图像时间和 ROS2 图像 `header.stamp` 沿用该交付时间戳，默认是 realtime 触发时间，测试模式是估算曝光中点。桥接随运行中的系统校时更新，允许回拨，不使用启动时冻结 offset 或强制递增。内部超时和队列计时仍使用单调时钟；可显式开启下述 FSYNC 触发—样本关联。

### 逐帧曝光观测

采集每帧后、输出变换前查询一次最新 ISP 状态，将结果冻结到 `sc132_frame_info_t.exposure`；保留帧引用后再次读取不会被后续查询覆盖。`status=1`（ESTIMATED）仅是该交付帧附带的曝光估计，不是已证实的传感器逐帧生效参数；源帧号相等也不能证明非原子 getter 的曝光与帧标识同步锁存。没有误差上界，AE 启动/光照突变时相邻值可能明显变化。查询失败、非法时长或 RAW 读时失败时 `status=0`（UNAVAILABLE），其余字段全零，不沿用旧值；默认图像照常交付，开启曝光中点测试时则停止采集。

| 字段 | 语义 |
|---|---|
| `status` | `0` 不可用（其他曝光字段全零）；`1` 最新 ISP 估计，无精度或实际生效帧保证。 |
| `duration_ns` | SDK 返回的积分秒数转换为 ns，不是主机等待/到帧耗时。 |
| `source_frame_id` / `source_timestamp` | SDK 当前帧标识；timestamp 为 opaque 源值，不当作 RAW 或 realtime。可与 `raw_frame_id` 对照，但不等于已证明参数生效帧。 |
| `observed_raw_ns` | 查询完成时 `CLOCK_MONOTONIC_RAW`，不是曝光起点或终点。 |

默认公开 `timestamp_ns` 是触发沿；测试开关可改为“触发时间＋半曝光时长”，但不宣称真实曝光中点，因为触发到积分起点尚未校准。bag `/cameraN/frame_metadata` 和 tee `camN/frames.jsonl` 中的 `exposure` 保留这些字段。MP4 `exposure.jsonl` 记录输入帧的相机、原始/归一化帧号、组号、组/逐路交付时间及曝光；它可能包含未编码保存的输入帧，应按相机及 `group_timestamp_ns // 1000 * 1000` 对照该路 timestamp CSV，不直接把源帧号当文件帧索引。ROS2 `/robobaton/camN/exposure`（`std_msgs/msg/String`，Reliable KeepLast(8)）发布 `robobaton_exposure_v1` JSON，含 `camera_id/sequence/frame_id/raw_frame_id/timestamp_ns/exposure`；按相机与 `timestamp_ns` 对照 Image `header.stamp`。系统回拨可能重复 stamp，需保留序列与采集边界，不能承诺仅靠 stamp 全局唯一。整数 JSON 必须无损解析。

MP4 sidecar 的顶层键为 `camera_id/raw_frame_id/frame_id/group_id/group_timestamp_ns/camera_timestamp_ns/exposure`；逐路交付时间字段名是 `camera_timestamp_ns`，不同于 ROS2 JSON 的 `timestamp_ns`。读取时先判断 `exposure.status`，再取 `duration_ns`；`source_timestamp` 不用于对齐 Unix 时间。

(test-exposure-midpoint)=
### 曝光中点时间戳测试开关

仅当前源码重建的 `libsc132.so` 支持 `SC132_TEST_EXPOSURE_MIDPOINT`，已有交付二进制不自动更新。默认关闭；启动前设为 `1` 开启，设为 `0` 或取消变量恢复原逻辑，无 C ABI、SONAME 或软件版本变更。

```bash
SC132_TEST_EXPOSURE_MIDPOINT=1 ./cam_demo
SC132_TEST_EXPOSURE_MIDPOINT=0 ./cam_demo
```

每次 `sc132_start_frame_set()` 启动时读取一次，运行中不切换。未设置、空值、`0/false/FALSE/off/OFF/no/NO` 均关闭，其他非空值开启。改变环境后须停止并重新启动进程/采集；ROS2 需把该变量传入节点或 launch 进程。

non-ROS 联合入口 `sensor_demo` 也可在 `config/sensor_config.yaml` 中设置 `camera.test_exposure_midpoint: true|false`，随包及自动生成的配置默认 `false`。显式 YAML 值覆盖环境变量；省略该键才保留环境变量控制。需重建 `sensor_demo` 与支持此开关的库，改配置后重启；`cam_demo` 不读取该 YAML，ROS2 仍使用环境变量。见 {ref}`non-ROS YAML 配置 <non-ros-yaml>`。

开启时逐路 `timestamp_ns = realtime 触发时间 + floor(exposure.duration_ns / 2)`，使用该帧冻结的最新 ISP 观测，忽略触发到积分起点的延迟，不用主机当前时间、到帧时间或 opaque 源时间。frame info 与 frame-set item 一致；组时间取调整后各路时间的最小值。non-ROS 保存/RTSP、ROS2 Image/CameraInfo 和 exposure 消息沿用这些值，消费端不得再加一次半曝光。曝光不可用、时长为零或加法溢出时停止采集，不静默退回触发时间。

配组放行和 `max_skew_ns` 仍使用原触发 RAW，reserved RAW/generation/uncertainty 及 FSYNC 对应也不偏移；因此测试模式的组时间与 RAW 审计时间有意表示不同事件。此模式只是未补偿延迟的曝光中点估计，不保证实际生效曝光、误差上界或硬件同步精度。


## IMU

| 项目 | 合同 |
|---|---|
| 设备路径 | `/dev/spidev2.0` |
| SPI mode/speed | mode `0`，`10 MHz` |
| INT1 DRDY | `34120000.gpio` offset `8`；不用旧 GPIO395 |
| 读取模式 | sensor timestamp FIFO |
| FIFO watermark | `1` |
| 原生 ODR | `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；旧 `500/1000/2000Hz` 配置明确拒绝，不重采样 |
| FSYNC | V2 输入与相机公共触发网相连；显式开启上升沿捕获后关联触发与其后首个 IMU 样本，不改变连续采样相位。 |

字段语义：

| 字段 | 单位/语义 |
|---|---|
| `sample_sequence` / demo `sample_seq` | IMU 样本序号。 |
| `temperature_c` / demo `temp_c` | 摄氏度。 |
| `accel_mps2` | `m/s^2`。 |
| `gyro_rps` | `rad/s`。 |
| `host_timestamp_ns` | 配对 INT1 边沿映射到 `CLOCK_REALTIME` 的纳秒时间戳；不是样本时间戳。 |
| `sample_timestamp_ns` | FIFO TMST→RAW→`CLOCK_REALTIME` 的逐样本时间戳；每次发布刷新系统时钟桥接，允许系统校时回拨。 |
| demo `ts_ns` | 原样保留 producer 的 realtime sample 时间，单位 ns；`host_ts_ns` 同样为 realtime，不由 consumer 再加 offset。 |
| `reserved0` | 当前会话观测到的 FIFO timestamp 低 16 位回绕次数；不表示 V1 20 位 SPI 快照回绕。 |
| `timestamp_uncertainty_us` | 逐样本时间映射的不确定度，单位 us。 |
| `gpio_event_gap_count` / `fifo_overflow_count` / `mapper_failure_count` | 当前会话的边沿缺口、FIFO 溢出与时间映射失败累计计数。 |

IMU 独立连续采样；FSYNC 关联识别触发之后的首个硬件标记样本，不表示该样本与相机曝光同时发生。仍不提供曝光中心、TF 外参或标定。不能把主机 INT1 时间或 FSYNC delta 冒充样本时间。

### FSYNC 触发—样本关联

默认关闭。non-ROS 使用 `sensor_demo --fsync --sample-rate-hz 1600` 或 YAML `imu.fsync_enabled: true`；ROS2 设置 `imu.fsync_enabled:=true` 和 `imu.sample_rate_hz:=1600`。仅支持 `800/1600Hz`，不自动修改采样率。`800Hz` 时间预算较紧，可能有较多 timing drop；`1600Hz` 同样不保证每个触发均有可发布样本。

硬件 FSYNC FIFO 标记把该包的绝对 TMST 替换为触发至样本的 delay。实现等待相邻绝对 TMST，以合法 tick 步长区间约束缺失时间，使用中点并计入半区间不确定度，不按名义 ODR 合成时间。delay 按实测时钟斜率转为 ns，再从样本 RAW 时间减去。端点缺失、回绕歧义或超过 `200µs` 策略时不伪造关联。

只在相机组与 FSYNC 沿的 RAW 不确定度区间内存在唯一双向候选时匹配，不用最近邻或 realtime 时间相等来配对。缓存有界（128 组、256 事件），不混配重启 generation。JSON schema 为 `robobaton_fsync_v1`：

| 字段 | 语义 |
|---|---|
| `status` | `1` 唯一匹配；`2` 无对应事件或组；`3` 歧义。仅 `1` 可作为有效关联。 |
| `camera_generation` / `group_id` / `frame_ids` / `camera_mask` | 相机会话、组号、cam0..3 帧号及有效相机位图。 |
| `imu_generation` / `fsync_sequence` / `sample_sequence` | IMU 会话、硬件触发序号和已发布样本序号；允许缺口。 |
| `group_timestamp_ns` / `sample_timestamp_ns` / `fsync_timestamp_ns` | realtime 组交付、IMU 样本及 FSYNC 沿时间，单位 ns；组时间默认是触发时间，测试模式为各路估算曝光中点的最小值。 |
| `camera_timestamps_ns` | cam0..3 各帧的原始 realtime stamp；按 `camera_mask` 取有效项，可精确匹配各 ROS2 Image/CameraInfo 的 `header.stamp`。组时间是各项最小值，不能代替所有相机时间。 |
| `group_raw_ns` / `sample_raw_ns` / `fsync_raw_ns` | 仅供关联审计的内部 RAW 值，不是 UTC；组 RAW 始终是最早触发，曝光中点测试不偏移它。 |
| `fsync_to_sample_ns` | FSYNC 沿至其后硬件标记样本的实测 delay。 |
| `group_uncertainty_ns` / `uncertainty_ns` | 相机组与 IMU 事件各自的映射不确定度，不是曝光同步精度承诺。 |

无保存时 JSON 输出 stdout；ROS1 bag 写入 `/robobaton/fsync`（`std_msgs/String`）；MP4 写入 `fsync.jsonl`；ROS2 发布 `/robobaton/fsync`（`std_msgs/msg/String`，Reliable KeepLast(256)）。缺失侧字段为零，应先检查 `status` 和 generation。保存完整性与关联完整性不同：检查状态、序号缺口和 `SENSOR_FSYNC_RESULT` 的 captured/dropped，不能仅凭退出码或容器完整断言所有触发均匹配。

整数时间戳和序号必须用无损整数 JSON parser 读取（例如 Python `json.loads` 的 `int`）。epoch 纳秒超过 IEEE-754 安全整数范围；JavaScript 普通 `JSON.parse` 会舍入，须使用支持 BigInt 的无损解析器。关联只声明源帧与源样本身份，不保证它们已通过保存筛选、队列或 DDS 送达；按逐路 stamp、frame metadata 与 IMU 序号核对实际数据。`SENSOR_FSYNC_RESULT health_valid=no` 时 captured/dropped 为 `unknown`，不能当零；stdout 写入损失由 `stdout_dropped` 报告。

负载边界：采集 owner 使用 `SCHED_FIFO/20`，non-ROS IMU consumer 与 ROS2 IMU 发布线程使用 `SCHED_RR/3`；跨优先级队列锁使用优先级继承，避免普通负载饿死持锁线程。SPI 固定为 `10MHz`，INT1 保持 `100µs` 异步复位脉冲。运行需要实时调度权限，设置失败不静默降级。应用不会自动改动系统 IRQ 分布、INT1 IRQ 线程优先级或 SPI dynamic-debug 开关；饱和负载下这些系统设置及订阅端调度仍影响结果。绝对 TMST/INT1 相位检查、唯一双向匹配和 `200µs` 门限保持不变，超界仍拒绝或停止；`800Hz` 的 FSYNC 标记样本也可能大量被拒绝，不能据此宣称任意负载零丢失。

INT1 的内核沿时间属于 MONOTONIC，转换到内部 RAW 时使用沿附近的有界时钟观测，而非把出队时的 offset 直接套给积压沿。独立观测线程继承允许 CPU 集合、使用 `SCHED_FIFO/30`（低于板端默认 GPIO IRQ 的 FIFO/50），每轮休眠 `50µs`；启动时确认调度设置成功。4096 项固定容量历史以至少 `100µs` 间隔入队，避免排空 burst 挤掉旧沿证书；更低 ODR 下不保证覆盖整个256沿队列。采集线程也在等待 INT1 和轮询传感器时钟时补充观测，读取与入队由优先级继承锁串行化。证书选择同时考虑读取半窗口和时钟调速距离；调度延迟不会改变 GPIO 序号或把沿重新配给其他样本。此调速界针对当前 X5 Linux 6.1、未启用 `CONFIG_NTP_PPS` 且未设置 `ntp_tick_adj=` 启动覆盖的内核；更换内核/启动参数必须重新验证时钟界，不得据此降低报告的不确定度。

传感器 TMST→RAW 拟合要求同一条仿射线同时满足各有效读取区间，不把区间中点当精确观测；不兼容的窄观测不能留下矛盾的旧证书。过宽的 SPI 观测不推进计数器解绕状态；斜率、外推、INT1 相位及 FSYNC 重建误差仍计入发布预算。INT1 IRQ 延迟或 SPI 长时间阻塞引起的超界拒绝、身份失败和 FIFO overflow 仍显式报告，不通过扩大门限或缓存旧样本掩盖。

验收必须使用成功 stop 后的最终 `IMU_RUNTIME_HEALTH final=yes health_valid=yes`：generation 非零，并核对 `published_samples`、`invalid_packet_drop_count`、GPIO 缺口与 FIFO overflow。最终行同时报告 `mapper_failure_count`、`uncertainty_over_200_drop_count`、`max_consecutive_timing_drop_count`、`fsync_captured` 和 `fsync_dropped`，包含最后一个成功样本之后的损失；无效包即使同时被 timing 门限拒绝也计入无效包总数。不能只检查最后一个已发布样本，因为尾部错误未必再有样本承载。timing drop 和 FSYNC dropped 是显式计数，不等于完整关联。保存或 DDS 验收还须回读实际 IMU/四路图像，并按上面的时间戳规则核对关联覆盖率，不能仅凭健康摘要、topic 存在或容器完整判定通过。

`accel_mps2` 按 `[X, Y, Z]` 输出；V2 PCB 的安装方向与加速度符号尚待实板六面/旋转验证，不沿用 V1 顶视图的 `[0, 0, -9.8]` 和左右前后轴向结论。

## non-ROS 保存输出

| 输出 | 合同 |
|---|---|
| ROS bag | `sensor_demo --record-bag <absolute .bag>` 保存四路 JPEG 图像、相机参数和 IMU 数据；不完整压力/异常运行使用显式 `.partial.bag` recovery 文件。 |
| MP4 session | `sensor_demo --record-mp4-dir <absolute directory>` 保存四路 H.264 MP4、四路 timestamp CSV、`imu.csv`、输入帧 `exposure.jsonl`、`fsync.jsonl`、`camera_params.yaml`、`session_status.json` 和 `publication_receipt.json`；FSYNC 文件始终创建，仅启用关联后写入记录。 |
| MP4 路径冲突 | 配置的 final 目录或同名 `.partial` 已存在时，实际输出自动切到同级 `<name>-YYYYMMDDTHHMMSSZ[-NNNN]`；以 `SENSOR_MP4_RESULT path=` 为准。 |
| `.partial` | 保留 recovery namespace；`.partial` MP4 session 可提取排查，但不声明为 complete。 |

MP4 模式只支持 H.264 和完整四路 camera mask `0x0f`，不能与 bag 保存或 frame-skip 同时启用。MP4 文件的帧时序是容器名义 timing；同 session 的 `cameraN_timestamps.csv` 按 `frame_index` 对齐编码帧，保存 realtime 组触发时间，经编码器微秒精度量化后以 ns 表示，并非各路原始纳秒 stamp。开启 FSYNC 后，`fsync.jsonl` 的 `camera_timestamps_ns` 保留各路原始值；核对 CSV 时使用 `group_timestamp_ns // 1000 * 1000`，发生保存丢帧时不能把 producer `frame_ids` 直接当作文件 `frame_index`。`published_complete` 源必须带有匹配的 `publication_receipt.json`，并且四路 MP4/index inventory 完整。

bag 消息的 payload 与记录时刻分开：图像及首帧 CameraInfo 的 `header.stamp` 保留相机 realtime 捕获时间；IMU payload 保留 realtime sample stamp。bag record time 独立读取写入时的 `CLOCK_REALTIME`，不是采样时刻；系统回拨时保留真实回拨，不强制非递减。物理写入顺序保持不变，各 connection 的 chunk index 按时间排序，供 ROS bag reader 检索。session config 的 `camera_timestamp_domain`、`imu_timestamp_domain`、`record_timestamp_domain` 均为 `"realtime"`。

MP4 CSV 索引属于 realtime 系统时间轴，但其精度与逐路原始值的区别如上；容器播放时间仍是相对/名义时间，不是 Unix epoch。编码/容器不能接受的时间回拨会报错并保留不完整产物，不伪造递增时间；持续录制前应先完成系统校时。

保存完整性按 recorder 分别判定：bag complete 检查会话成功及 recorder 的队列/写入错误，不独立约束 producer timing drop 为零；MP4 complete 还要求成功 stop 后的有效 final health、published=observed=admitted=written>0、连续样本序号、无 GPIO/FIFO/timing/invalid-packet drop，且最大样本不确定度 ≤`200µs`。默认 `allow-counted` 下可证明身份的 timing 拒绝可能继续采集，因此不能用 bag complete 证明零丢样。曝光不可用和 FSYNC 缺失/歧义也各自检查，不由容器 complete 代替；验收步骤见[数据保存](../usage/save-data-guide.md)。

## ROS2 topics

| Topic | 消息类型 | 合同 |
|---|---|---|
| `/robobaton/cam0..3/image_raw` | `sensor_msgs/msg/Image` | 四路 raw NV12 图像，`encoding="nv12"`。 |
| `/robobaton/cam0..3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | 标准 compressed transport JPEG；当前插件使用 X5 media codec 硬件 JPEG 编码。 |
| `/robobaton/cam0..3/camera_info` | `sensor_msgs/msg/CameraInfo` | 只包含当前帧宽高；标定字段为空。 |
| `/robobaton/cam0..3/exposure` | `std_msgs/msg/String` | `robobaton_exposure_v1` 随帧冻结的 ISP 曝光观测；`status=1` 是估计，不保证实际生效帧。 |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42670-P gyro/accel；orientation 不可用。 |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42670-P 温度，复用 IMU sample stamp。 |
| `/robobaton/fsync` | `std_msgs/msg/String` | 显式开启后的 FSYNC 关联 JSON。 |

ROS2 QoS：

| 数据 | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | 跟随 raw publisher，同为 Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
| Exposure | Reliable + KeepLast(8) |
| FSYNC | Reliable + KeepLast(256)，默认关闭 |
| IMU | `SensorDataQoS`，keep last 100 |
| Temperature | `SensorDataQoS`，keep last 10 |

ROS2 raw `Image.step` 使用底层 DMA buffer 的 stride；`data.size()` 使用底层 Y/UV buffer size，可能大于紧凑 `width * height * 3 / 2`。订阅端不得按紧凑 NV12 假设直接索引 UV 平面。

ROS2 `header.stamp` 不是发布时刻：相机默认使用 realtime 触发沿时间，显式测试模式使用上述估算曝光中点；IMU/Temperature 使用 realtime `sample_timestamp_ns`，不以 `host_timestamp_ns` 代替。ROS2 只把纳秒值拆成 `sec`/`nanosec`，不再添加 offset。可与同一已校准系统时间轴比较，但同域不保证硬件采样或曝光对齐；跨设备仍依赖系统校时质量。`use_sim_time` 不会把这些传感器 stamp 改为仿真 `/clock`。NTP/PTP 调整系统时钟后后续 stamp 跟随变化；它们不会建立 FSYNC 样本关联。

ROS2 当前不发布 RTSP、TF 外参或标定；FSYNC 只提供触发—样本对应，不改变采样相位，也不保证曝光同步。通用可视化优先订阅 `/image_raw/compressed`，不要假设 raw NV12 可被普通 RGB/BGR 工具直接显示。

## UART

| 项目 | 合同 |
|---|---|
| 默认设备 | `/dev/ttyS1` |
| 可示例切换 | `/dev/ttyS7` 或其他现场设备 |
| 波特率 | `serial_port_demo` 默认 `115200`；DEBUG_UART `921600`。 |
| serial_port_demo 数据格式 | 8N1、raw、无 flow control |
| demo 模式 | `tx`、`rx`、`txrx`、`echo` |
| UART1/UART7 TX/RX 信号逻辑电平 | 保持 `3.3V`；DEBUG_UART 为 `1.8V`。 |
| UART1/UART7 供电脚 | V2 CN2/CN3 的供电用途、电平、额定负载和热插拔边界待确认，勿引用 V1 合计 `500 mA` 限制。 |
| V1 历史边界 | UART1/UART7 在 V1 板上曾验收；不构成 V2 电气或线束兼容证明。 |

V2 UART1/UART7 对应 CN2/CN3 5pin 接口与 `/dev/ttyS1`、`/dev/ttyS7`。CN3 有独立 IO 默认作为 PPS 输入，不需要复用或切换 RX/TX；PPS 设备节点按系统枚举识别。完整线序及供电脚用途以正式 V2 标识为准。DEBUG_UART 非用户串口；默认断电接线，核实 TX/RX/GND、对端电平及共地，不接适配器 VCC，不反灌。见[硬件连接与安全](../getting-started/hardware-and-safety.md#uart)。
