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
| `vin_lpwm` | 所有相机入口唯一支持的触发 | 使用随帧传播的 `trig_tv` 捕获；缺少捕获即停止，不以到帧时间兜底。 |

相机时间戳统一为 `CLOCK_REALTIME` 系统时间（Unix epoch，单位 ns）。关闭曝光中点测试时，表示所选路径的 LPWM 触发时间估计，不是到帧或曝光中心。启动配置 `camera_timestamp_path` 选择 `observer`（默认）或 `official`；直接使用库时在启动前设置 `SC132_TIMESTAMP_PATH`。切换必须停止后重启；非法值启动失败，两路径均不向另一条回退。

- `observer`：以 RAW 读数包围 SIF VSYNC 捕获寄存器更新，再减去同一 24 MHz 计数器中的 `VSYNC − trigger`，通过随帧 `trig_tv` 精确匹配历史。后台线程继承允许的 CPU 集合，使用 `SCHED_FIFO/60`，每轮休眠 `50µs`；扫描内更新使用本次扫描窗口，重读 TRIG 并确认 VSYNC 稳定。缺少实时调度权限时启动失败。寄存器读取窗口超过不变的 `500µs` admission 上限、捕获缺失或匹配失败即停止。此路径需要 X5 固定寄存器映射和 `/dev/mem` 只读权限；窗口不代表已验证的物理同步精度。
- `official`：使用同一帧的 `out_img.info.timestamps`（`CLOCK_MONOTONIC_RAW` IRQ 时间），减去 `(tv − trig_tv) × 1000`；`tv` 与 `trig_tv` 是 AON 微秒值，不是 RAW/realtime epoch。此路径绝不启动或使用 SIF MMIO observer。元数据非法、算术溢出或下溢即停止。这是物理误差上界未知的 IRQ 派生触发估计：`reserved[SC132_GROUP_TIMING_VALID]=0`，`reserved[SC132_GROUP_UNCERTAINTY_NS]=UINT32_MAX`，不授予 observer 的有界有效标记。

frame-set 模式默认先丢弃每路 30 帧 warmup；所有启用相机完成 warmup 前立即归还缓冲，不查询曝光、不做图像变换，也不校验这些非交付帧的时间戳。每个交付帧必须满足所选路径：observer 为 `500µs` 窗口内的精确捕获匹配，official 为合法同帧元数据与算术；关闭 warmup 不豁免首帧。

配组使用所选触发 RAW 估计，再为整组使用同一次新采样的 RAW→realtime 桥接。组时间是各路交付时间的最小值；`max_skew_ns` 表示所选触发估计的差异，不代表曝光或相机/IMU 对齐精度。non-ROS 诊断、RTSP 输入、保存图像和 ROS2 图像时间戳沿用交付值，默认是 realtime 触发估计，测试模式是估算曝光中点。桥随运行中校时更新，允许回拨，不冻结 offset 或强制递增。内部超时仍使用单调时钟；IMU selector 与时钟独立于相机路径。

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

(manual-exposure)=
### 启动时手动曝光配置

non-ROS `sensor_demo` 的 `camera.auto_exposure` 为布尔值、默认 `true`；`camera.exposure_time_us` 为整数微秒值、默认 `2000`，合法输入为 `1..4294967295`。零、负数、小数、溢出、尾随文本或非法布尔值在启动前拒绝。自动模式忽略时长，不改写 SDK tuning 的自动曝光策略；手动模式为每路启用相机选择 ISP `HBN_ISP_MODE_MANUAL`，以 `exposure_time_us / 1000000` 设置 SDK 秒数，并将模拟、sensor digital 和 ISP 增益均固定为 `1x`，用于可重复标定。实际可用范围受 SDK/profile 限制，SDK 拒绝即启动失败，不静默回退自动曝光。

库每次 `sc132_start_frame_set()` 启动读取一次 `SC132_AUTO_EXPOSURE=1|0` 和十进制 `SC132_EXPOSURE_TIME_US`，未设置时默认为 `1` / `2000`。`sensor_demo` 始终将 YAML 显式值或默认值写入环境，覆盖继承环境；省略 YAML 键也不会保留环境控制。配置仅在启动时生效，改变后须停止并重启；需重建应用与支持此配置的库。YAML 示例见 {ref}`non-ROS 配置 <non-ros-yaml>`。

手动参数在相机 flow 启动成功后、worker 就绪前设置；每路先丢弃 `3` 帧过渡帧，即使普通 warmup 关闭也如此。这不证明后续每帧参数的实际生效身份，逐帧 `exposure` 仍遵守上文估计值合同。bag `/robobaton/session_config` 的 `auto_exposure` / `exposure_time_us` 记录请求值，不是实测曝光。该功能与 `camera.test_exposure_midpoint` 独立，不修改时间戳公式、C ABI 或 SONAME，不宣称真实曝光中点；尚未实板部署或验证。

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

配组放行和 `max_skew_ns` 仍使用原触发 RAW，reserved RAW/generation/uncertainty 也不偏移；因此测试模式的组时间与 RAW 审计时间有意表示不同事件。此模式只是未补偿延迟的曝光中点估计，不保证实际生效曝光、误差上界或硬件同步精度。


## IMU

当前公开库要求设备已绑定匹配的 **内核 IIO V3 capture 模块**。已有 V2 capture 模块不兼容，host 模式也不例外；仅重建/部署应用不会升级模块。按 name `icm42670-capture` 枚举唯一实例，核验 scan 布局并通过 BIND 核对控制节点，不假定 `iio:deviceN` 编号。两种时间戳模式在同一二进制中使用同一 IIO 读取与内核 SPI/INT1 owner。库不装载模块、不修改设备树，也没有用户态 SPI/spidev 或自动回退路径。

| 项目 | 合同 |
|---|---|
| ABI | `5.0`；实体 `libicm42670.so.5.0.0`，SONAME `libicm42670.so.5`，九个导出均使用 `ICM42670_X5_5.0`；全部 consumer 与匹配头文件/库成套重建 |
| 原生 ODR | `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；其他值拒绝，不重采样 |
| FIFO watermark | 固定 `1` |
| 缓冲容量 | `buffer_capacity=4096` 默认；只接受 `256..8192` 的 2 次幂 |
| 无效六轴载荷策略 | `allow-counted` 默认计数后继续；`strict` 遇无效载荷失败；不是时间精度策略 |
| 时间戳模式 | 启动配置 `timestamp_mode`：`ICM42670_TIMESTAMP_MODE_HOST=0`（默认）或 `ICM42670_TIMESTAMP_MODE_TMST=1`；应用 `imu_timestamp_mode` 接受 `host` 或 `tmst` |

| 字段 | 单位与语义 |
|---|---|
| `session_generation` / `sample_sequence` | 会话身份及 FIFO 包序号；按序号核对顺序，跨会话不得混用 |
| `sample_monotonic_ns` | 内核赋予的 `CLOCK_MONOTONIC` 主机估计，两模式均原样保留；非 Unix 时间、非物理采样沿实测 |
| `observation_monotonic_ns` | 同一 MONOTONIC 域的主机观测；可与 sample 作差，但不等于实际采样延迟 |
| `estimated_period_ns` | 主机估计周期，不是芯片实测时间戳 |
| `evidence_id` / `burst_flags` | 会话内 burst 身份；位 `1` 为普通成功 burst，位 `2` 为 STOP 尾部 |
| `burst_complete_raw_ns` | 独立 `CLOCK_MONOTONIC_RAW` burst 完成观测；同 burst 可重复，禁止直接与 MONOTONIC 相减 |
| `timestamp_source` | `1=IRQ`、`2=SERVICE`；SERVICE 表示无 IRQ 时的服务观测估计，不伪装为硬件采样沿 |
| `packet_flags` | 低三位分别为 accel/gyro/temperature valid（`1/2/4`） |
| `temperature_c` / `accel_mps2[3]` / `gyro_rps[3]` | 摄氏度、`m/s^2`、`rad/s`；`raw` 保存原始六轴/温度值 |
| `timestamp_mode` | C sample 中数值 `0=HOST`、`1=TMST`；输出 JSON/CSV 使用 `host`/`tmst` |
| `fifo_tmst` | 原始 FIFO TMST 低 16 位，零扩展存于公开 u32 字段；不是解绕值或 Unix 时间 |
| `sample_raw_ns` | host 为 `0`；tmst 为用户态解绕的 FIFO TMST，依据内核拥有的 FIFO/UI 跳变证据映射到 `CLOCK_MONOTONIC_RAW` |
| `timestamp_uncertainty_ns` | host 为 `UINT32_MAX`（未知）；tmst 为计算映射 admission 上界，单位 ns，不是物理采样精度证书 |

host 模式保留内核 MONOTONIC 估计，不提供物理误差上界。tmst 模式使用内核拥有的 FIFO TMST 与有界 UI 跳变观测，由用户态解绕并进行有界仿射 RAW 映射。时间证据缺失、矛盾、过期、歧义或超预算时失败，不回退到 host 或名义 ODR 补造时间。`200µs` 样本映射 admission 是计算边界，不是实测物理精度；不恢复 FSYNC、触发—样本关联或用户态 SPI。

### Web 姿态预览输入

`GET /api/v1/info` 保留软件 `version` 和应用会话身份；当前 Web 服务报告 `web_implementation: "rust"`、`webrtc_stack: "str0m"` 和 `webrtc_version: "0.24.1"`。WebRTC 版本由 `webrtc_version` 读取，不再提供旧 Go/Pion 的 `pion_version` 字段；这些实现信息不改变软件版本或 SO ABI。

`sensor_demo` 的 IMU SSE 使用 **`schema_version: 2`**，不保留旧 `sample_timestamp_ns` / `host_timestamp_ns` 别名。SSE `session_id` 与 `/api/v1/info.application_session_id` 标识同一应用会话，`source_generation` 标识 producer 会话，`sample_sequence` 为原生样本序号；没有名为 `sequence` 的 SSE 字段。所有 u64 字段用十进制字符串传输，避免 JavaScript 精度损失。

时间字段显式区分 `sample_realtime_ns`、`sample_monotonic_ns`、`sample_raw_ns`、`observation_monotonic_ns`、`burst_complete_raw_ns` 和 `estimated_period_ns`。`timestamp_mode` 为 `host` 或 `tmst`；host 的 `timestamp_uncertainty_ns` 为 JSON `null`（没有误差上界），tmst 为计算映射 admission。保留 `source_generation`、`evidence_id`、`burst_flags`、`packet_flags`、`timestamp_source`、`fifo_tmst` 及 `bridge_monotonic_ns`、`bridge_raw_ns`、`bridge_realtime_ns`、`bridge_uncertainty_ns`。不能跨 RAW/MONOTONIC 直接作差。ABI5 不提供逐样本 GPIO/mapper 计数，SSE 不伪造零值或继续输出这些字段。

`attitude_accel_mps2`（`m/s²`）和 `attitude_gyro_rps`（`rad/s`）仍为三个元素数组，只供浏览器姿态预览；原始 `accel_mps2` / `gyro_rps`、数值/趋势、原生采样与保存不变。姿态积分和连续性使用所选原生时钟：host 的 MONOTONIC sample 或 tmst 的 RAW sample，不使用 realtime，避免墙钟调整污染积分。

设备在每个原生样本上对六轴执行四级一阶低通后再抽取遥测；单级极点为 `min(10Hz, 遥测上限×0.2, 原生采样率×0.2)`，默认 800→50Hz 的低频群延迟约 64ms。时间戳表示当前输入样本，不补偿为无延迟测量，也不代表单次原始样本。无效输入的姿态数组元素为 JSON `null`；时间不递增、序号重置或大于 100ms 原生样本缺口后重新播种，不合成缺失样本。滤波不估计姿态或零偏；浏览器仍独立融合并用原始六轴执行静置质量检查。无绝对航向或振动整流误差消除保证。

公共库与独立 `icm42670_reader`、`imu_reader_demo` 均不转 Unix 时间。两模式都保留原生 MONOTONIC，tmst 另提供 RAW sample 与不确定度。`IMU_TIMING_SUMMARY` 分开报告 `timestamp_hz`（即使 tmst 模式仍为主机赋予的 MONOTONIC 跨度）与 `acquisition_hz`（普通非 STOP burst 的独立 RAW 端点及端点末包序号）；后者须 `acquisition_valid=yes` 且至少两个普通 burst。任一频率均不能单独证明物理采样精度或完整性。

### 输出侧 realtime 桥接与时间元数据

`sensor_demo` 保存和 ROS2 输出适配层按模式选原生 sample：host 使用 `sample_monotonic_ns`，桥接 MONOTONIC→REALTIME；tmst 使用 `sample_raw_ns`，桥接 RAW→REALTIME。每个新 `(session_generation,evidence_id,timestamp_mode)` 观测一次桥，同 burst 复用；原生 MONOTONIC 主机字段和 RAW burst 观测均不改写。桥最多尝试三次，所选原生时钟的前后括号宽度超过 `200000ns` 时拒绝，全部失败则输出失败。`bridge_uncertainty_ns` 为括号半宽向上取整，独立于 tmst 样本映射 admission，不是物理采样精度或相机/IMU 同步误差上界。后续 burst 照实保留墙钟回拨，不强制递增。

bag `/imu/data` 与 ROS2 IMU/Temperature 的 `Header.stamp` 使用显式转换的 realtime。bag `/robobaton/imu/timing`（`std_msgs/String`）及 ROS2 同名 topic（`std_msgs/msg/String`，Reliable KeepLast(256)）逐样本保存 `robobaton_imu_timing_v2` JSON：

- 时钟声明：host 的 `sample_clock` 与 `bridge_clock` 为 `CLOCK_MONOTONIC`，tmst 为 `CLOCK_MONOTONIC_RAW`；`output_clock=CLOCK_REALTIME`，`burst_complete_clock=CLOCK_MONOTONIC_RAW`；
- 身份：`generation`、`sample_sequence`、`evidence_id`、`burst_flags`；
- 时间与来源：`sample_monotonic_ns`、`sample_realtime_ns`、`burst_complete_raw_ns`、`observation_monotonic_ns`、`estimated_period_ns`、`timestamp_source`、`packet_flags`，以及 `timestamp_mode`（`host`/`tmst`）、`fifo_tmst`、`sample_raw_ns`、`timestamp_uncertainty_ns`；
- 桥观测：`bridge_monotonic_ns`（仅 host；tmst 为零）、`bridge_raw_ns`（仅 tmst；host 为零）、`bridge_realtime_ns`、`bridge_uncertainty_ns`。不得把 RAW 桥基点标为 MONOTONIC，也不得跨时钟作差。

MP4 `imu.csv` 的 `sample_realtime_ns` 是输出 realtime；保留原生时间、身份、burst、来源、桥基点/半宽、温度和 raw 六轴列（generation 列名为 `session_generation`）。新增 selector 列为 `timestamp_mode,fifo_tmst,sample_raw_ns,timestamp_uncertainty_ns,bridge_clock,bridge_raw_ns`。host 的 RAW sample 为零、样本不确定度未知；tmst 独立保留原始 MONOTONIC 估计。没有 FSYNC topic、sidecar、callback、启用选项、触发—样本关联或 `200µs` 物理精度保证。曝光观测与曝光中点测试开关可用于两种相机路径，official 不确定度仍未知。共同 Unix epoch 不代表物理同步。

JSON 时间戳和序号必须无损读取为整数；epoch 纳秒超过 IEEE-754 安全整数范围，普通 JavaScript `JSON.parse` 会舍入，应使用无损整数解析器。

### STOP、ACK 与最终健康

回调由串行采集 worker 调用，sample 借用至返回；不得抛异常或在回调调用 stop/destroy，`user_data` 须存活到 stop 返回。STOP 保持回调接纳并排空完整停止集合，然后 join；异步 consumer 必须同时排空，不能先关闭接纳。`--count N` 只是请求 STOP 的阈值，最终样本数可以超过 N，不截断停止集合。record 仅在其覆盖样本均交付 callback 后 ACK；重复 stop 保留终态。

`icm42670_get_runtime_health` 在 stop 返回错误后仍可查询已取得的终态诊断，不能把失败 stop 的字段清零当健康。最终健康包含 `session_generation`、`published_samples`、`consumed_scans`、`records_consumed`、`records_acked`、`last_packet_sequence`、`irq_wakeup_count`、`timer_service_count`，以及 `fatal_reason/fatal_errno`、`fifo_overflow_count`、`invalid_payload_count`、`scan_push_failure_count`、`evidence_full_count`、`timestamp_service_burst_count`、`tail_packet_count`、`unknown_hardware_tail`、`quiesce_errno`、`transport_complete`。

健康判断需结合 stop/health 返回值、非零 generation、最终错误、计数和序号，以及 producer/consumer/实际载荷数量。`transport_complete=1` 只认证停止集合被消费并 ACK，不能消除 fatal；`unknown_hardware_tail` 表明 STOP fence 外的物理尾部不在认证范围，不能宣称所有物理采样均交付。`allow-counted` 不等于零丢样，strict 不等于物理精度保证。CLI 最终输出为非阻塞尽力日志，缺失摘要不是健康通过。

`accel_mps2` 为 `[X,Y,Z]`。PCB 安装方向及符号尚未公开确认，不声明相对主板/相机坐标的变换、TF 或外参。采集 owner 使用 `SCHED_FIFO/20`，non-ROS consumer/ROS2 IMU 发布使用 `SCHED_RR/3`；调度失败拒绝启动，不自动修改系统 IRQ/debug/实时配额。

## non-ROS 保存输出

| 输出 | 合同 |
|---|---|
| ROS bag | `sensor_demo --record-bag <absolute .bag>` 保存四路 JPEG 图像、相机参数和 IMU 数据；不完整压力/异常运行使用显式 `.partial.bag` recovery 文件。 |
| MP4 session | 四路 H.264 MP4、四路 timestamp CSV、扩展 `imu.csv`、输入 `exposure.jsonl`、`camera_params.yaml`、`session_status.json`、`publication_receipt.json`；无 FSYNC 文件。 |
| MP4 路径冲突 | 配置的 final 目录或同名 `.partial` 已存在时，实际输出自动切到同级 `<name>-YYYYMMDDTHHMMSSZ[-NNNN]`；以 `SENSOR_MP4_RESULT path=` 为准。 |
| `.partial` | 保留 recovery namespace；`.partial` MP4 session 可提取排查，但不声明为 complete。 |

MP4只支持H.264与完整四路mask0x0f，不与bag/frame-skip同时启用。cameraN_timestamps.csv按 `frame_index` 关联编码帧，保存微秒量化realtime组时间；按相机与组时间对照exposure输入观测，不把源frame_id当编码索引。完整源还须匹配publication receipt和四路MP4/CSV。

bag 消息的 payload 与记录时刻分开：图像及首帧 CameraInfo 的 `header.stamp` 保留相机 realtime 捕获时间；IMU payload 保留 realtime sample stamp。bag record time 独立读取写入时的 `CLOCK_REALTIME`，不是采样时刻；系统回拨时保留真实回拨，不强制非递减。物理写入顺序保持不变，各 connection 的 chunk index 按时间排序，供 ROS bag reader 检索。session config 的 `camera_timestamp_domain`、`imu_timestamp_domain`、`record_timestamp_domain` 均为 `"realtime"`。

bag `/robobaton/session_config` 另记录启动 `camera_timestamp_path` 与 `imu_timestamp_mode`。四种组合使用同一二进制与同一 IIO 采集/owner，只改变两个时间戳轴。启动前选择方式见 [non-ROS 使用](../usage/non-ros-demo.md) 与 [ROS2 使用](../usage/ros2-demo.md)。

MP4 CSV 索引属于 realtime 系统时间轴，但其精度与逐路原始值的区别如上；容器播放时间仍是相对/名义时间，不是 Unix epoch。编码/容器不能接受的时间回拨会报错并保留不完整产物，不伪造递增时间；持续录制前应先完成系统校时。

保存完整性按 recorder 分别判断；bag complete 不单独证明零 producer 无效 payload。动态 MP4 使用 `imu_health_scope=callback_window`，核对本次回调窗口的原生样本、序号连续性、计数差值与队列写入，不要求停止共享 producer，也不认证窗口外完整性。仍活跃的启动自动会话使用 `imu_health_scope=producer_session`，在应用退出后检查有效最终 health、published=observed=admitted=written>0、scan=published、record=ACK、连续序号及零 fatal/overflow/invalid/push/evidence/quiesce 异常。不再使用旧 mapper/精度字段。STOP 集合完整不代表所有物理样本完整，曝光覆盖率另查；见[数据保存](../usage/save-data-guide.md)。

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
| `/robobaton/imu/timing` | `std_msgs/msg/String` | 逐样本 `robobaton_imu_timing_v2` 原生时钟及桥证据。 |

ROS2 QoS：

| 数据 | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | 跟随 raw publisher，同为 Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
| Exposure | Reliable + KeepLast(8) |
| IMU timing | Reliable + KeepLast(256)，随 IMU 开启 |
| IMU | `SensorDataQoS`，keep last 100 |
| Temperature | `SensorDataQoS`，keep last 10 |

ROS2 raw `Image.step` 使用底层 DMA buffer 的 stride；`data.size()` 使用底层 Y/UV buffer size，可能大于紧凑 `width * height * 3 / 2`。订阅端不得按紧凑 NV12 假设直接索引 UV 平面。

ROS2 Header 不是发布时刻。相机使用所选 realtime 触发估计（或显式曝光中点估计）；IMU/Temperature 使用所选的逐 burst MONOTONIC→REALTIME 或 RAW→REALTIME 桥。timing JSON 保留原生 MONOTONIC、独立 RAW、模式、身份及正确标注的桥观测。照实保留墙钟回拨，不转换为仿真 `/clock`；共同 epoch 不提供物理同步。

ROS2不发布RTSP、TF外参、标定或触发—样本关联。一般可视化优先compressed，普通RGB/BGR工具未必直接支持NV12。

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
