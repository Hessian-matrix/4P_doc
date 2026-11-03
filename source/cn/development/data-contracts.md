# 数据合同

本页记录用户可以依赖的数据格式、字段和时间语义。未公开的物理方位、坐标系、外参和硬同步能力均明确列为限制，不在文档中伪造。

参数与字段描述是当前实现合同，不是完整模式/负载/时长的验收声明；当前结果与限制见{ref}`能力与验证边界 <capability-verification-boundary>`。

## 相机图像与 RTSP

| 项目 | 合同 |
|---|---|
| `libsc132.so` / camera callback 原始帧 | NV12；native `1280x1088` 或 VSE 缩放 `640x480`/`720x480`/`1280x720`；旋转 `0/180` 宽高不变，`90/270` 宽高交换 |
| RTSP 对外流 | H.264 默认；支持 H.265 |
| FOV | 相机 A/B 保持水平 `148.4°`/`115.6°`、垂直 `126.6°`/`96.8°`、对角 `193.8°`/`157.2°`。 |
| camera FPS | 默认`30fps`，支持`25fps`、`30fps`、`40fps`、`50fps`和`60fps`；其他值在启动副作用前拒绝 |
| RTSP path | `/PRR` |
| 端口映射 | CAM1..CAM4 依次对应软件 cam0..cam3 与 `554/555/556/557`。 |

`libsc132.so` callback 暴露 NV12 原始帧，RTSP 客户端接收 H.264/H.265 编码流。帧信息包含 `width`、`height`、`stride`、`vstride`、Y/UV 虚拟/物理地址及 size。旋转 `90/270` 会交换宽高；消费端须依每帧元数据与 stride/size 处理对齐，不要假设紧凑 `1280x1088`。

完整 C 结构声明、逐字段解释、NV12 行布局与引用有效期见 {ref}`API 图像输出结构参考 <camera-output-structures>`。

仅支持完整四路或单颗相机诊断，不支持 2/3 路组合；旋转 `180` 仅允许 `30fps`。VSE 尺寸是上表的离散集合，不是任意缩放能力。

## Frame Set 字段

| 字段 | 含义 |
|---|---|
| `camera_count` | 当前帧组内的相机数量，完整四目为 `4`。 |
| `group_id` | 帧组序号。 |
| `group_timestamp_ns` | 帧组时间戳，单位 `ns`。 |
| `max_skew_ns` | 当前帧组实际观测到的触发捕获时间跨度，单位 `ns`；测试曝光中点偏移不改变此值。 |
| `items[i].camera_id` | 软件 ID `0..3`，依次对应物理 CAM1..CAM4。 |
| `items[i].frame_id` | 归一化后的帧 ID。 |
| `items[i].timestamp_ns` | 单路帧时间戳，单位 `ns`。 |

`sc132_frame_set_config_t.max_skew_ns` 才是配组放行上限；默认值为 `10000000 ns（10ms）`，限制触发捕获值差异，不代表曝光对齐精度。

## Trigger 模式

| 模式 | 当前状态 | 公开合同 |
|---|---|---|
| `vin_lpwm` | 所有相机应用及底层库唯一支持的 VIN 硬件触发 | 相机与 IMU FSYNC 共用 LPWM IO；相机时间基准来自随帧传播的 `trig_tv` 硬件捕获，缺失则停止采集，不回退到到帧时间。 |

所有对外传感器时间戳统一为 `CLOCK_REALTIME` 系统时间（Unix epoch，单位 ns）。默认相机表示 LPWM 硬件触发沿，而不是到帧、IRQ 或曝光中心；显式测试模式见 {ref}`曝光中点测试开关 <test-exposure-midpoint>`。底层以 RAW 读数包围 SIF VSYNC 捕获寄存器更新，再减去同一 24 MHz 计数器中的 `VSYNC − trigger`，通过随帧 `trig_tv` 精确匹配历史记录。后台线程继承进程允许的 CPU 集合，使用 `SCHED_FIFO/60`，每轮休眠 `50µs`；扫描内更新使用本次扫描窗口，重读 TRIG 并确认 VSYNC 稳定。无法设置实时调度时启动失败。寄存器读取窗口超过 `500µs`、捕获缺失或匹配失败时停止采集，不回退到到帧时间。该实现需要 X5 固定寄存器映射、`/dev/mem` 只读访问及实时调度权限；窗口上限不是已验证的同步精度。

frame-set 模式默认先丢弃每路 30 帧 warmup；所有启用相机完成 warmup 前立即归还缓冲，不查询曝光、不做图像变换，也不校验这些非交付帧的捕获映射。warmup 结束后的每个交付帧仍须具有有效精确匹配，保留 `500µs` 窗口上限；关闭 warmup 不会豁免首帧校验。

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
| 原生 ODR | `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；其他值明确拒绝，不重采样 |
| FSYNC | V2 输入与相机公共触发网相连；显式开启上升沿捕获后关联触发与其后首个 IMU 样本，不改变连续采样相位。 |

字段语义：

| 字段 | 单位/语义 |
|---|---|
| `sample_sequence` / demo `sample_seq` | FIFO 顺序定义的 IMU 样本序号；不由 INT1 通知或 realtime 递增定义。 |
| `temperature_c` / demo `temp_c` | 摄氏度。 |
| `accel_mps2` | `m/s^2`。 |
| `gyro_rps` | `rad/s`。 |
| `host_timestamp_ns` / CLI `fifo_observation_ns` | 包所在 SPI FIFO burst 成功完成时的 RAW 观测，经当次系统时钟桥接转换为 `CLOCK_REALTIME` ns；同 burst 可重复，FSYNC 延迟发布保留转换后的原值、可能早于发布，不在发布时重新桥接旧 RAW；随墙钟回拨，不是 IRQ 沿、样本或曝光时间。 |
| `sample_timestamp_ns` | FIFO TMST→RAW→`CLOCK_REALTIME` 的逐样本时间戳；每次发布刷新系统时钟桥接，允许系统校时回拨。 |
| demo `ts_ns` | 原样保留 producer 的 realtime sample 时间，单位 ns；`host_ts_ns` 同样为 realtime，不由 consumer 再加 offset。 |
| `reserved0` | 当前会话观测到的 FIFO timestamp 低 16 位回绕次数。 |
| `timestamp_uncertainty_us` | 逐样本时间映射的不确定度，单位 us。 |
| `gpio_event_gap_count` / `fifo_overflow_count` / `mapper_failure_count` | 会话累计可检测缺失 GPIO 通知序号值、FIFO 溢出、时间映射失败。GPIO 缺口仅诊断、不证明物理沿/样本丢失，不单独失败。 |

IMU 独立连续采样；FIFO 顺序与实测芯片 TMST 定义序列和时间，INT1 仅用于唤醒排空 FIFO，不与包逐项配对。FSYNC 使用芯片标记/delta 与实测端点，识别触发后的首个标记样本，不表示与曝光同时发生。仍不提供曝光中心、TF 外参或标定。不能把 host 观测或 FSYNC delta 冒充样本时间；两类 realtime stamp 均随系统校时，不能以唯一 host 或递增墙钟判断采集顺序。

### Web 姿态预览输入

`sensor_demo` 的 IMU SSE 保持 `schema_version: 1`，增加 `attitude_accel_mps2`（`m/s²`）和 `attitude_gyro_rps`（`rad/s`）三个元素数组；只供浏览器姿态预览。原始 `accel_mps2` / `gyro_rps`、数值/趋势、原生采样、保存数据与 C ABI 不变。纳秒时间戳、序号与会话 ID 仍用十进制字符串保持精度。

设备在每个原生样本上对六轴执行四级一阶低通后再抽取遥测；单级极点为 `min(10Hz, 遥测上限×0.2, 原生采样率×0.2)`，默认 800→50Hz 的低频群延迟约 64ms。时间戳表示当前输入样本，不补偿为无延迟测量，也不代表单次原始样本。无效输入的姿态数组元素为 JSON `null`；时间不递增、序号重置或大于 100ms 原生样本缺口后重新播种，不合成缺失样本。滤波不估计姿态或零偏；浏览器仍独立融合并用原始六轴执行静置质量检查。无绝对航向或振动整流误差消除保证。

### FSYNC 触发—样本关联

默认关闭。non-ROS 使用 `sensor_demo --fsync --sample-rate-hz 1600` 或 YAML `imu.fsync_enabled: true`；ROS2 设置 `imu.fsync_enabled:=true` 和 `imu.sample_rate_hz:=1600`。仅支持 `800/1600Hz`，不自动修改采样率。`800Hz` 时间预算较紧，可能有较多 timing drop；`1600Hz` 同样不保证每个触发均有可发布样本。

硬件 FSYNC FIFO 标记把该包的绝对 TMST 替换为触发至样本的 delay。实现等待相邻绝对 TMST，以合法 tick 步长区间约束缺失时间，使用中点并计入半区间不确定度，不按名义 ODR 合成时间。delay 按实测时钟斜率转为 ns，再从样本 RAW 时间减去。端点缺失、回绕歧义或超过 `200µs` 策略时不伪造关联。

首个 FIFO 包若为 FSYNC 标记，保留该包及其原始 burst 完成观测，等后续绝对 TMST 后再重建，不等待或消费对应 GPIO 身份。启动前实测 Arm 时钟沿不是前一个 FIFO 样本：分别检查首包同次转换或晚一个完整合法 ODR 区间，由后续实测端点收窄，仅接受唯一可行假设，不接受分数相位。两次 FIFO 使能写入必须在从 Arm 观测区间起点计算的最短合法 ODR 之前完成，使用实测时钟斜率下界换算；超过即拒绝启动，避免完整 TMST 回绕别名。回绕唯一性、实测时钟和 `200µs` admission 保持不变；无法证明时钟/epoch 时失败，超预算按 strict／allow-counted 策略并保留健康计数。

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

负载边界：采集 owner 使用 `SCHED_FIFO/20`，non-ROS IMU consumer 与 ROS2 IMU 发布线程使用 `SCHED_RR/3`；跨优先级队列锁使用优先级继承。SPI 为 `10MHz`，INT1 保持 `100µs` 异步复位唤醒脉冲。实时调度设置失败不静默降级。应用不会自动修改 IRQ、SPI dynamic-debug、实时配额、LPWM 或内核；高负载仍受 SPI/调度与订阅端影响。实测 TMST、FSYNC 唯一双向匹配及 `200µs` admission 不变，不承诺任意负载零丢失。

INT1 是通知而不是样本时钟或逐包身份来源；GPIO 软件 IRQ 时间戳不代表物理沿硬件锁存，采集不消费该时间戳。可检测通知序号缺口只计入 `gpio_event_gap_count`，连续序号也不能排除事件生成前的丢失/合并。FIFO/TMST 主导设计移除了逐沿配包依赖，**没有修复或证明底层 GPIO/内核原因**；定位该原因仍需匹配 BSP 的 IRQ 捕获或同步物理波形证据。没有 IRQ 时仍以有界超时检查 FIFO 存活，通知缺口不等于样本丢失；须核对 FIFO/序号/最终健康和实际载荷。

传感器 TMST→RAW 拟合要求同一仿射线满足有效读取区间，不把中点当精确观测；矛盾窄观测使旧证书失效，过宽 SPI 观测不推进解绕。斜率、外推与 FSYNC 重建误差计入发布预算。FIFO overflow、坏包、回绕/时钟歧义及无效 epoch 仍失败；长 SPI 阻塞仍可能拒绝或停止，不扩大门限、不按名义 ODR 合成时间或缓存旧样本掩盖。

验收必须使用成功 stop 后的最终 `IMU_RUNTIME_HEALTH final=yes health_valid=yes`：generation 非零，并核对 `published_samples`、`invalid_packet_drop_count`、GPIO 缺口与 FIFO overflow。最终行同时报告 `mapper_failure_count`、`uncertainty_over_200_drop_count`、`max_consecutive_timing_drop_count`、`fsync_captured` 和 `fsync_dropped`，包含最后一个成功样本之后的损失；无效包即使同时被 timing 门限拒绝也计入无效包总数。不能只检查最后一个已发布样本，因为尾部错误未必再有样本承载。timing drop 和 FSYNC dropped 是显式计数，不等于完整关联。保存或 DDS 验收还须回读实际 IMU/四路图像，并按上面的时间戳规则核对关联覆盖率，不能仅凭健康摘要、topic 存在或容器完整判定通过。

`accel_mps2` 按 `[X, Y, Z]` 输出；V2 PCB 的安装方向与加速度符号尚待实板六面/旋转验证，当前不声明相对于主板或相机的正负轴及坐标变换。

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

保存完整性按 recorder 分别判定：bag complete 检查会话与 recorder 队列/写入错误，不独立要求 producer timing drop 为零；MP4 complete 还要求成功 stop 后有效 final health、published=observed=admitted=written>0、序号连续、无 FIFO/timing/invalid-packet drop、最大不确定度 ≤`200µs`。GPIO 通知缺口仅诊断，不单独使保存不完整。默认 `allow-counted` 可继续处理时钟身份可证明的 timing 拒绝，bag complete 不证明零丢样。曝光与 FSYNC 完整性另行检查，见[数据保存](../usage/save-data-guide.md)。

bag 过载只对完整四路组统一保留/丢弃。默认最小间隔 `10` 使用连续 `source_group_order` 而不是 producer `group_id`；候选必须已编码、完整且未被 writer 领取，已领取组受保护。没有合法旧组或当前组可丢时停止并排空为可读 partial，非零退出；任何丢组均为 `data_complete=false`，策略合规不表示持续压力或全传感器通过。主动隔组保存要求显式最小间隔 `2`，详见[保存队列说明](../usage/save-data-guide.md)。

原生 bag JPEG 仅去除 SOI 后长度为 `4`、只含私有 frameIdx 的 JPU APP9，保留其他 APP 与编码载荷，不改变 ROS2 JPEG 插件输出。`rosbag_info.py --freq` 统计 record time，`--header-freq` 单列已保存消息的 `Header.stamp`；都不能单独证明采集无丢失。producer、consumer、recorder 与回读计数必须分别核对；保存序列连续仍可能遗漏源数据头尾。

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
| UART1/UART7 TX/RX 信号逻辑电平 | `3.3V`；DEBUG_UART 为 `1.8V`。 |
| UART1/UART7 供电脚 | 1 号针为 3V3 供电脚，默认不接；额定负载和热插拔边界待确认。断电接线，不接适配器 VCC，不反灌。 |

UART1 对应 CN1 GH1.25 4pin 与 `/dev/ttyS1`，UART7 对应 CN2 GH1.25 5pin 与 `/dev/ttyS7`。UART7 的 4 号针为独立 PPS 输入，系统默认启用，不需要复用或切换 RX/TX；PPS 设备节点按系统枚举识别。针号与线序见{ref}`接口接线示意图 <wiring-diagram>`，压接前按实物标识核对方向。DEBUG_UART 非用户串口；默认断电接线，核实 TX/RX/GND、对端电平及共地，不接适配器 VCC，不反灌。见[硬件连接与安全](../getting-started/hardware-and-safety.md#uart)。
