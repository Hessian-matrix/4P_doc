# 数据保存

## 1. 适用范围

本文说明如何使用 non-ROS `sensor_demo` 保存以下两类数据：

1. ROS1 bag v2.0：四路同步图像、相机信息、帧元数据和独立 IMU；
2. H.264 MP4 session：四路 MP4、编码帧时间戳索引、相机参数、含原生时钟/桥列的 IMU CSV、曝光 sidecar、session status 和 publication receipt。

本文适用于 `sensor_demo --help` 同时包含以下参数的运行包：

```text
--record-bag <absolute-path>
--record-mp4-dir <absolute-directory>
```

ROS1 bag 与 MP4 是两种互斥的保存模式，当前不能在同一个进程中同时开启。

### 网页动态会话

运行支持网页录制的完整包后，打开 `http://<设备IP>/`，直接使用首页常驻的“录制与保存”卡片。唯一表单默认显示格式、固定存储、开始/停止/查询、设备状态、时长和已写入量；图像隔帧与最小丢组间隔在默认折叠的“高级选项”中，可用空间、丢弃计数、会话、路径和最终完整性等在默认折叠的“录制详情与使用说明”中。实际错误、不确定命令和停止收尾提示不折叠。沿用实时状态/能力检查与命令锁定，状态缺失/过期或命令结果不确定时不执行控制。相机、IMU 和预览不随停录而停止，可连续录制多个互斥会话。CLI/YAML 启动自动录制仍可用，网页可停止该会话。详细操作及访问边界见[网页控制录制](non-ros-demo.md#网页控制录制)。

展开或收起高级选项与录制详情不发送停止、不重置选项或零偏，也不重建 WebRTC、SSE 或姿态 Worker。隐藏高级值无效时会先自动展开再显示校验提示。`Esc` 仅退出单路视频放大，不用于录制控制；刷新仍恢复浏览器本地选项默认值并清除预览零偏，不改变设备录制状态。

网页仅允许固定运行目录（标准包 `/root/demo/bin/recordings`）或已挂载 TF 的 `/mnt/sdcard/recordings`；设备生成会话名，不接受自定义路径。TF 缺失不会退回 eMMC。开始时至少需要 64 MiB 可用空间，此检查不是整个录制期间空间充足的保证。录制/存储故障报告 failed/partial 并清理本次会话，不伪装成功；源故障仍停止采集。

停止仅表示请求收尾；必须等待设备报告 `published_complete`、`data_complete=true`、`cleanup_complete=true`，并按实际载荷核对。网页最终结果和 `SENSOR_RECORDING_RESULT` 是会话结果，不必等采集进程退出。`partial`、`failed`、`aborted`、清理未完成都不能当作完整数据。收起详情、关闭浏览器和断网不会停录；超时后查询实际状态，不要盲目重发。未清理完成时禁止新会话。

动态 MP4 用 `imu_health_scope=callback_window` 检查本次窗口的原生样本、序号、计数差值与队列写入，等待首个有效 IDR，停止时有界等待共同编码组；这不证明窗口外或整个 producer 无丢失。进程退出后的 producer final health 仅用于仍活跃的启动自动会话。预览滤波、姿态零偏和遥测降频不改变保存值。无身份认证，能访问设备的人都能开始/停止写盘；仅用于可信隔离 LAN。

推荐优先使用 H.264 MP4 保存：四路 `cameraN.mp4` 可直接播放，并复用 RTSP 编码结果；ROS1 bag 保存 JPEG 消息，适合 ROS1 消息工具或后续解包分析。支持的帧率是参数范围，不是零丢失保证，负载边界见第 9 节。两种模式的启动与验收分别见第 5/7 节。

高压 bag 在严格丢组策略耗尽时合法结束为 partial，不是持续压力通过。应用退出的正常收尾保持 IMU 输入直到 producer STOP 排空、consumer 排空后再关闭 writer；动态停录以本次 callback window 为边界，不停止 producer。历史 DDS 发布/接收差额仍未精确归因，不能仅凭保存序列连续证明所有路径头尾无损。旧组成的 FSYNC/长录结果不认证V3/ABI5集成组成或当前V4/ABI6；此前non-ROS HO保存短窗证据仅认证原组成，不认证长录，见{ref}`能力与验证边界 <capability-verification-boundary>`。

| 模式 | 入口 | 主要输出 | 完整保存判据 |
|---|---|---|---|
| H.264 MP4 | `--record-mp4-dir` | 一个 session 目录 | `SENSOR_MP4_RESULT ... outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |
| ROS1 bag | `--record-bag` | 一个 `.bag` 文件 | `SENSOR_BAG_RESULT ... bag_outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |

启动命令行录制在进程退出时，还须检查退出码为 0 且对应 `SENSOR_*_RESULT` 明确完整。网页动态会话按上面的会话最终结果判断；`.partial`、`data_complete=no` 或相关错误只能作为恢复或诊断数据。

complete 首先是 recorder 发布结果，不证明所有物理样本或曝光观测均已保存。默认 `allow-counted` 只对无效六轴 payload 计数，strict 遇此失败。bag 检查会话/队列/写入错误；动态 MP4 按 `imu_health_scope=callback_window` 核对窗口内样本、序号、计数差值与队列写入，不等待 producer STOP 或认证窗口外完整性。仍活跃的启动自动会话使用 `imu_health_scope=producer_session`，应用退出后另要求有效最终 health、published=observed=admitted=written>0、scan=published、record=ACK、序号连续及零 fatal/overflow/invalid/push/evidence/quiesce 异常。旧 mapper-health 字段已移除；tmst 仍独立执行 `200µs` 计算 admission，不是物理精度。`transport_complete` 仅认证 STOP 集合，不覆盖 fence 外物理尾部；两种保存模式均须按实际健康范围与载荷核对。

相机图像/metadata 使用所选 observer/official realtime 触发估计或显式曝光中点估计。保存按启动 `imu_timestamp_mode` 每 burst 桥接 host MONOTONIC→REALTIME 或 tmst RAW→REALTIME；tmst 下也不覆盖原始 MONOTONIC 主机估计。bag `/imu/data` Header 与 MP4 `imu.csv` 的 `sample_realtime_ns` 是输出值。bag `/robobaton/imu/timing` JSON 和 CSV 保留模式、原始 FIFO low16 `fifo_tmst`、`sample_raw_ns`、`timestamp_uncertainty_ns`、原生 host/burst 证据、身份/来源，以及正确标注且独立的 MONOTONIC/RAW 桥基点与半宽。host 的 RAW sample 为零、样本不确定度 `UINT32_MAX`；桥不确定度与 tmst `200µs` 计算 admission 均不是物理精度。图像 CSV 仍为微秒量化组时间，exposure sidecar 保留逐路输入值。bag record time 独立读取 realtime 并保留回拨；MP4 播放仍相对/名义。共同 epoch 不代表物理同步，录制前先校时。

bag timing schema `robobaton_imu_timing_v3` 与 ROS2 `/robobaton/imu/timing` 一致；bag `/robobaton/session_config` 记录 `camera_timestamp_path`、`imu_timestamp_mode`、`imu_fsync_diagnostics`。通过 [non-ROS YAML/CLI](non-ros-demo.md) 选择任一四组合，停止/重启后切换，均使用相同二进制与 IIO 采集/owner。每种组合均要求匹配的内核 IIO V4 capture 模块，现有 V2/V3 模块不兼容，应用部署不升级模块。FSYNC 诊断默认开启，可显式关闭，无独立 topic/sidecar 或关联、spidev 或回退。official 绝不使用 SIF observer 时间，validity0/uncertainty `UINT32_MAX`。当前 non-ROS HO 短窗证据及未验收范围见{ref}`能力与验证边界 <capability-verification-boundary>`。不声明四组合保存验收；见[数据合同](../development/data-contracts.md#imu)。 独立诊断由YAML `imu.fsync_diagnostics: true`或CLI `--imu-fsync-diagnostics on|off`控制；JSON／CSV逐样本原样保存`fifo_header,fsync_flags,fsync_sequence,fsync_raw_ns,fsync_uncertainty_ns,fsync_delta_us`。无有效沿为RAW=0／uncertainty=`UINT32_MAX`，普通包sequence/delta=0；tagged `fifo_tmst`为delta微秒。不改相机帧/group诊断，不在线宣称匹配。

bag `/cameraN/frame_metadata`、tee `camN/frames.jsonl` 和 MP4 `exposure.jsonl` 原样保存逐帧冻结的 `exposure`。采集原始硬件帧 N 时取得的 getter 只估计相邻 N+1（允许 uint32 回绕），按已采集原始硬件帧 ID 而非归一化组号或 SDK 源帧号匹配；保存端不得再移一帧。`status=1` 是固定单硬件帧关联估计，没有已测物理误差上界或实际生效曝光证明；无前驱、硬件缺口或无效前驱 getter 时为 `0` 且全零，不跨缺口延用。N 查询失败影响 N+1，有效前驱仍可估计 N；来源字段保留更早 getter 的原值，不改成目标图像的身份或时间。关联在各 worker 的零初始化会话状态中于 warmup 预热，无额外图像缓冲或交付延迟；默认触发 stamp 不变，显式中点模式使用匹配估计并在不可用时停止。MP4 sidecar 描述输入帧，可能多于实际编码帧，按相机及微秒量化的组交付时间对照 timestamp CSV。字段、关联键与限制见[逐帧曝光观测](../development/data-contracts.md#逐帧曝光观测)。

固定 N→N+1 只是估计关联规则；真实 AE 的有效滞后可能不同，不保证任何一帧实际应用的曝光，也不构成 AE 验收。

## 2. 版本与运行包一致性

每次部署都必须复制完整 `demo/` 运行包，不能只替换 `sensor_demo` 或某一个 `.so`。

在开发机的公开 non-ROS 仓库中验证运行包：

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # 改成实际仓库目录
cd ${NON_ROS_ROOT}
python3 scripts/verify_runtime_package.py demo
```

在板端进入本次部署目录后验证：

```bash
DEMO_DIR=/root/demo  # 改成实际完整运行包目录
cd ${DEMO_DIR}
sha256sum -c manifest.sha256
cat VERSION
./sensor_demo --version
```

`VERSION`、程序 `--version`、实际加载的 `libsc132`、`libprrtsp`、`libicm42670` 产品版本及 ABI 信息必须属于同一份 V2 包。不要混用系统目录、旧部署或其他工程中的同名动态库。

运行包内的 AArch64 ELF、`runtime-provenance.json` 和 `manifest.sha256` 必须一致；使用时以部署包内实际 `VERSION` 为准，不以文档标题推断版本。

## 3. 板端运行前检查

### 3.1 硬件与进程

当前四路保存路径要求：

- 四颗相机全部连接；
- ICM-42670-P SPI/FIFO 采集链路可用；INT1 仅唤醒，无通知时仍有界检查 FIFO；
- `cam-service` 正常运行；
- 同一时刻没有另一个 `cam_demo` 或 `sensor_demo` 占用相机；
- trigger 模式仅为 `vin_lpwm`。

检查：

```bash
pgrep -a cam-service
pgrep -a -f '(^|/)(cam_demo|sensor_demo)( |$)' || true
```

不要用模糊 `killall` 或 `pkill -f` 清理未知进程。若发现另一个相机应用，应先确认其身份和用途，再按该应用自己的退出协议停止。

### 3.2 存储目录

保存路径必须是绝对路径。程序会尝试创建缺失的父目录，但最终路径及父目录必须可写；ROS1 bag 的父目录还不能通过符号链接绕过路径约束：

```bash
mkdir -p /root/data/robobaton
findmnt -T /root/data/robobaton
df -h /root/data/robobaton
df -i /root/data/robobaton
```

开始前应为视频、临时 staging、最终 publication 和故障保留空间预留足够容量。

保存到 TF 卡时，先按[TF 卡使用](../getting-started/tf-card.md)确认 SD 设备、分区与精确挂载身份；未挂载时不要创建保存目录或启动录制，避免误写 tmpfs 或系统盘。

**eMMC／TF 写入压力提醒：** 四目 bag／MP4 本身就是大数据量持续写入。录制期间尽量只保留一个大吞吐写盘任务，bag 与 MP4 二选一；避免同时运行其他录制、存储压测、大文件复制／下载、解压或数据解包／转换，尤其不要向同一目标介质并行写入。数据复制、解包和转换应在录制正常停止并完成 finalize 后进行。

减少并行写入可以降低带宽竞争和写盘停顿风险，但不保证单个录制任务永不积压：实际 JPEG 字节量、码率、介质持续写入能力、剩余空间与文件系统状态仍会影响结果。更换 eMMC／TF 或录制参数后仍须检查最终状态和实际载荷；保留既有整组丢弃、partial 与显式停止语义，不将此建议视为零丢失保证。

### 3.3 环境与外部工具

优先运行包顶层 launcher；它会设置 `LD_LIBRARY_PATH` 和 `PATH`：

```bash
DEMO_DIR=/root/demo  # 改成实际完整运行包目录
cd ${DEMO_DIR}
. ./env.sh
```

ROS1 bag 保存不依赖 ROS 安装。

MP4 保存要求板端 PATH 中有可执行的 `ffmpeg`。运行包带有用于录制链路 frame-count 校验的 `bin/ffprobe` helper，但它不是完整的离线 `ffprobe`：

```bash
command -v ffmpeg
command -v ffprobe
ffmpeg -version | sed -n '1p'
```

任一检查失败时，不要启动 MP4 正式录制。

板端还需可用的 `python3` 与匹配的 `libstdc++`。干净系统镜像与运行包对这些依赖的归属尚未完整确认，不能把工具可用或 manifest 通过推广为所有镜像运行依赖已验收。

## 4. 参数与 YAML 优先级

`sensor_demo` 先读取：

```text
${DEMO_DIR:-当前目录}/config/sensor_config.yaml
```

然后解析 CLI；CLI 只覆盖显式提供的字段。默认配置 `save_data.save: false`，不会自动保存。

保存配置结构：

```yaml
save_data:
  save: false
  format: mp4
  save_path: /root/demo/save_mp4/
  skip: false
```

约束：

- `format` 只能是 `rosbag` 或 `mp4`；
- `save_path` 必须是绝对路径；
- `rosbag` 使用 `.bag` 文件路径；
- `mp4` 使用 session 目录路径；
- `skip: true` 仅适用于 ROS1 bag；
- CLI `--record-bag` 与 `--record-mp4-dir` 互斥；
- MP4 只支持 H.264、完整四路 camera mask `0x0f`，不支持 frame skip；
- MP4 final 目录名不能以保留后缀 `.partial` 结尾。

如果长期使用 CLI 管理保存任务，建议保持 YAML 中：

```yaml
save_data:
  save: false
```

这样可避免忘记 YAML 已启用保存而产生意外数据。

## 5. 保存 H.264 MP4 session（推荐）

### 5.1 前台启动

```bash
DEMO_DIR=/root/demo  # 改成实际完整运行包目录
cd ${DEMO_DIR}
./sensor_demo \
  --fps 30 \
  --codec h264 \
  --sample-rate-hz 800 \
  --print-rate-hz 0 \
  --record-mp4-dir /root/data/robobaton/run_30fps_mp4
```

不要同时添加 `--record-bag` 或 `--record-frame-skip`。

若配置的 final 目录或对应 `.partial` 已存在，recorder 会选择同级的带 UTC 时间戳候选目录。必须以最终日志中的：

```text
SENSOR_MP4_RESULT path=<实际路径> configured_path=<配置路径>
```

为准。

### 5.2 YAML 启动（更推荐）

配置好yaml文件里面的参数，直接运行`sensor_demo`即可。

```yaml
camera:
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 800

  print_rate_hz: 0
  print_metrics: false
save_data:
  save: true
  format: mp4
  save_path: /root/data/robobaton/run_30fps_mp4
  skip: false
```

### 5.3 正常停止与验收

停止方式与 ROS1 bag 相同，优先一次 `Ctrl+C`/`SIGINT`，并等待 finalize。

完整 MP4 session 必须满足：

```text
process exit code = 0
SENSOR_MP4_RESULT ...
outcome=published_complete
data_complete=yes
cleanup_complete=yes
success=yes
```

同时检查：

- 四路 selected/admitted/written 各自相等且四路 written 数量一致、非零；
- `encoded_frames_dropped=0`；
- `imu_samples_admitted == imu_samples_written > 0`；
- producer final-health snapshot 有效，published samples 与 consumer observed samples 相同；
- 最终 `transport_complete=1`、record/ACK 相等，fatal/overflow/invalid/push/evidence/quiesce 为零，且样本序号连续；
- session 中存在匹配的 `publication_receipt.json`；
- session 目录中不存在 `.publication_incomplete` marker。

典型完整目录：

```text
run_30fps_mp4/
├── camera0.mp4 ... camera3.mp4
├── camera0_timestamps.csv ... camera3_timestamps.csv
├── imu.csv
├── exposure.jsonl
├── camera_params.yaml
├── session_status.json
└── publication_receipt.json
```

MP4 使用名义播放帧率，`cameraN_timestamps.csv` 按 `frame_index` 关联编码帧和微秒量化 realtime 组时间，不是各路原始纳秒 stamp。按相机与组时间对照 `exposure.jsonl` 输入观测，不能把源 frame_id 直接当文件索引。

`exposure.jsonl` 始终保存输入观测（包括 status=0），可能多于保存编码帧；没有 FSYNC sidecar。曝光不可用不单独令默认模式停止或 partial；业务需每帧曝光估计时另查状态与输入/编码对应。

退出码 2、`published_partial`、`.partial` 目录、marker 或 receipt 不匹配都不是完整 session。

## 6. MP4 转换为时间戳命名 JPEG

离线转换应在有完整 `ffmpeg` 和 `ffprobe` 的 Host 上执行。运行包内的 ffprobe helper 不能替代离线工具。

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # 改成实际仓库目录
cd ${NON_ROS_ROOT}
command -v ffmpeg
command -v ffprobe

python3 scripts/mp4_extract.py \
  /root/data/robobaton/run_30fps_mp4 \
  /root/data/robobaton/run_30fps_mp4_dataset
```

恢复数据也可转换：

```bash
python3 scripts/mp4_extract.py \
  /root/data/robobaton/run_30fps_mp4.partial \
  /root/data/robobaton/run_30fps_mp4_recovery_dataset
```

但 `conversion_summary.json` 会保留源 outcome，且 `source_data_complete=false`；转换成功不等于源数据完整。

默认要求四路 `0,1,2,3`。不得通过 `--expected-cameras` 只选子集来把不完整源伪装为完整；完整源必须与 status/receipt 中的四路 MP4 和 timestamp inventory 精确一致。

输出目录必须不存在。最终发布使用原子 no-replace，不覆盖并发创建的目录。

## 7. 保存 ROS1 bag

### 7.1 前台启动

以下为默认 `30fps` 的启动示例，不预先保证 complete；使用 `25/40/50/60fps` 时替换 `--fps`，并在实际目标环境检查完整性：

```bash
DEMO_DIR=/root/demo  # 改成实际完整运行包目录
cd ${DEMO_DIR}
./sensor_demo \
  --fps 30 \
  --sample-rate-hz 800 \
  --print-rate-hz 0 \
  --record-bag /root/data/robobaton/run_30fps.bag \
  --record-frame-skip 0
```

若业务明确允许每隔一个完整同步 frame-set 保存一次：

```bash
./sensor_demo \
  --fps 30 \
  --record-bag /root/data/robobaton/run_30fps_skip.bag \
  --record-frame-skip 1 --record-drop-min-interval 2
```

`record-frame-skip=1` 按 recorder 收到完整 frame-set 的连续序号保存一组、跳过一组，四颗相机共享同一个决策；它不会改变 RTSP 输出帧率。主动隔组保存必须显式配合 `--record-drop-min-interval 2`；默认间隔 10 与隔组保存不兼容，启动时会拒绝冲突配置。

### 7.2 YAML 启动（更推荐）

配置好yaml文件里面的参数，直接启动即可。

```yaml
camera:
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
rtsp:
  bps: 4000
  codec: h264
  url: /PRR
imu:
  sample_rate_hz: 800

  print_rate_hz: 0
  print_metrics: false
save_data:
  save: true
  format: rosbag
  save_path: /root/data/robobaton/run_30fps.bag
  skip: false
  drop_min_interval: 10
```

然后运行：

```bash
./sensor_demo
```

### 7.3 正常停止

在前台按一次 `Ctrl+C`，或从已确认的控制终端向准确 PID 发送 `SIGINT`/`SIGTERM`：

```bash
SENSOR_DEMO_PID="$(pgrep -xo sensor_demo)"
test -n "$SENSOR_DEMO_PID"
kill -INT "${SENSOR_DEMO_PID}"
```

发送信号后必须等待程序完成：相机 admission 关闭、consumer join、RTSP close、SC132 blocking stop、IMU stop/join、队列 drain、writer close、文件 fsync 和原子 publication。不要立即发送 `SIGKILL`，也不要在未看到最终结果前关闭电源。

### 7.4 结果验收

接受完整 bag 时应同时满足：

```text
process exit code = 0
SENSOR_BAG_RESULT ...
bag_outcome=published_complete
data_complete=yes
cleanup_complete=yes
success=yes
```

并检查：

- `image_frames_by_camera=cam0:N,cam1:N,cam2:N,cam3:N` 四路相等且 `N > 0`；
- stop后保留最终 `IMU_RUNTIME_HEALTH`（包括失败诊断），检查状态/非零generation，核对published、consumer observed、recorder admitted/written及实际消息数；
- 核对sequence、无效payload、overflow、fatal/push/evidence/quiesce、STOP transport及record/ACK，再比对producer/consumer/保存实际载荷；MONOTONIC与RAW不可直接相减，realtime桥允许校时回拨，不合成递增值。
- 最终路径来自 `SENSOR_BAG_RESULT path=`，不要只依赖配置路径猜测。

非零退出、`published_partial`、`.partial.bag` 或 quarantine 都不是正式完整数据，但应保留用于诊断，不要自动覆盖或删除。

### 7.5 队列与写盘诊断

`SENSOR_BAG_RESULT` 的 `frame_queue_*`、`encoded_queue_*`、`imu_queue_*` 给出各级容量、峰值、满队列停留时间及拒收；`encoded_queue_oldest_evicted_*` 统计为接收新帧组而淘汰的完整组。默认严格策略为 `--record-drop-min-interval 10`（YAML：`save_data.drop_min_interval`）：只在已编码、未被 writer 领取的完整组中，从旧到新选择与所有已丢组至少相距 10 组的合法候选；没有合法候选时，当前组也必须满足同一间隔才能丢弃。仍无法满足则显式停止并排空已接收数据，发布 `*.partial.bag`、记录原因并以非零退出，不放宽间隔继续丢。该保证只约束 recorder 丢组，不覆盖采集源、硬件或 IMU 丢样，也不保证高压下持续达到目标帧率。任何淘汰或拒收都不能按 complete 验收。

每路 `/cameraN/frame_metadata` 的 `source_group_order` 是从 0 开始的 recorder frame-set 到达序号，用于比较四路保留组和计算丢组间隔；producer `group_id` 保留原值，不能用其跳号扩大间隔。`/robobaton/session_config` 记录 `drop_policy_min_group_interval`；`/robobaton/session_status` 记录 `drop_policy_stopped`、`drop_policy_stop_group_order`、`drop_policy_dropped_groups`、`drop_policy_min_observed_interval`（少于两次丢组为 0）和 `error`。策略停止时，终止序号是已录制范围的排他上界，不计为合法丢组。

writer 在图像 burst 或 IMU 高水位服务点分批排空当时的 IMU backlog 快照，期间新到样本不会无限延长该轮服务。重排窗口按全部已提交顺序计界，包含尚未编码的帧；writer 已领取部分帧的组不得淘汰。

丢组必须是四路整组同一决策，并记录为 `data_complete=false`。候选间隔符合策略只证明策略正确，不能将提前停止、partial 或可读回放认定为持续高压或全传感器通过。

`chunk_*`、`record_*` 延迟包含 writer／缓冲写路径，不能直接等同于设备介质延迟。`dirty_kb`／`writeback_kb` 来自系统 `/proc/meminfo`；`diskstats_*_delta` 聚合 `/proc/diskstats` 全部行，可能同时包含整盘与分区重复统计，不是本次保存文件或单一挂载设备的 I/O。不要由聚合 `io_time` 推导磁盘 busy 百分比；结合实际挂载设备、最终 health 和回读载荷定位。


## 8. 查看和解包 ROS1 bag

运行包包含 `bin/rosbag_info.py`（Python 标准库实现，需要板端可用的 `/usr/bin/python3`；干净镜像依赖归属仍待确认）。保存完成后可直接在板端查看 bag 状态：

```bash
DEMO_DIR=/root/demo  # 改成实际完整运行包目录
cd ${DEMO_DIR}
python3 bin/rosbag_info.py /root/data/robobaton/run_30fps.bag
python3 bin/rosbag_info.py --yaml --freq /root/data/robobaton/run_30fps.bag
```

`--freq` 的 `frequency` 是 bag index **record time** 相邻间隔中位数的倒数，输出 `frequency_basis` 明示该基准。writer 批量写入时可远高于传感器采样率，不表示 IMU 超速或载荷损坏。当前源码新增 `--header-freq`（隐含 `--freq`）：扫描 `sensor_msgs/Imu`、`CompressedImage`、`CameraInfo` 的载荷，将 `Header.stamp` 频率另列为 `header_frequency`；同一 topic 的所有 connection 必须类型与 MD5 一致。其他类型、混合 schema 或不足两条／中位周期非正时无该数值。时间戳排序后计算相邻间隔，不能据此检查发布顺序、证明无丢样或硬件同步；扫描需要读取完整 bag，保留原 record-time 统计语义。

```bash
python3 bin/rosbag_info.py --yaml --header-freq /root/data/robobaton/run_30fps.bag
```

在 Host 使用开发机仓库脚本时：

```bash
NON_ROS_ROOT="$HOME/RoboBaton_4p_demo"  # 改成实际仓库目录
cd ${NON_ROS_ROOT}
python3 scripts/rosbag_info.py /root/data/robobaton/run_30fps.bag
```

解包为 IMU CSV、相机参数和四路 JPEG（在 Host 上执行，使用公开源码仓库脚本）：

```bash
python3 scripts/rosbag_extract.py \
  /root/data/robobaton/run_30fps.bag \
  /root/data/robobaton/run_30fps_dataset
```

输出目录必须不存在。当前工具支持未压缩、索引完整的 ROS1 bag v2.0；`.partial.bag` 可用于恢复分析，但不能因此升级为完整数据。

(persistence-fps-boundary)=

## 9. 帧率与压力边界

两种模式的参数集合均支持 `25/30/40/50/60fps`，但不能只按帧率承诺完整保存：

- H.264 MP4 复用 RTSP 编码 access unit，完整性同时受编码、存储和 IMU 最终健康约束；高负载或源端错误 可以得到 `published_partial`，即使四路 MP4 均可播放。
- ROS1 bag 使用独立 JPEG 编码和队列，CPU、编码吞吐、存储及 RTSP 预览负载均影响丢帧；不能承诺某个帧率以下必定 complete，或高帧率只有少量丢失。
- 改变 fps、IMU ODR、尺寸、介质或调度后，须分别核对持续四路速率、最终健康、IMU timing/桥证据及实际载荷；曝光覆盖率与容器完整性分别判断。

参数可配置或旧组成运行不认证新 IIO 组成的解码、DDS 或持续保存。原生 bag JPEG 去除私有 JPU APP9，不改变 ROS2 JPEG 插件；一种编码/保存路径不认证另一条路径。

## 10. 常见问题

### 同时配置 bag 和 MP4

程序会在启动硬件前拒绝：

```text
--record-bag and --record-mp4-dir are mutually exclusive
```

选择一种模式后重试。

### MP4 启动时报 ffmpeg/ffprobe 错误

确认从完整运行包顶层 launcher 启动，或先执行 `. ./env.sh`。板端必须有完整 `ffmpeg`；包内只提供录制所需的 ffprobe helper。

### 输出变成 `.partial` 或退出码为 2

表示 recorder 能够保留恢复数据，但完整性门未通过。保留日志、session status、receipt/marker 和数据，不要改名伪装成 complete。

### RTSP handle 三次 close 仍失败

程序会以 exit 1 立即终止，避免在 SC132 callback 尚未 quiescent 时析构 callback owner。该次数据仅作恢复数据；保留日志并检查 `cam-service` 与相机应用状态，确认服务恢复后再启动下一次任务。

### 存储空间或 inode 不足

停止新的保存任务，保留当前 partial/quarantine，扩容或清理经确认的历史数据。不要在 recorder 运行中删除 staging、marker 或目标路径。

### 退出后没有最终结果行

把该次运行视为失败或未证明完整。保存完整 stdout/stderr、退出码、进程和服务状态。
