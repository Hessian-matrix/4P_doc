# 数据保存

## 1. 使用网页录制与保存（推荐）

日常录制直接在网页完成：**打开设备首页 → 选择格式和存储 → 开始录制 → 停止并等待收尾 → 核对结果和路径 → 取回数据**。随板预烧录系统已配置 `sensor_demo` 开机自启，不需要先 SSH 登录或重复启动程序。网页与手动启动说明见 [non-ROS Demo 使用](non-ros-demo.md)。

保存的是设备采集的四路相机与同一 IMU 数据，**不是网页屏幕录像，也不会自动下载到电脑**。同一时间只能运行一个 ROS1 bag 或 H.264 MP4 会话。

### 1.1 打开录制卡片

1. 按[首次上电](../getting-started/first-boot.md)连接设备，在电脑浏览器打开 `http://<设备IP>/`。
2. 找到首页的 **“录制与保存”** 卡片。宽屏在四路相机、姿态和遥测旁；窄屏向下滚动即可看到，不需要切换页面。
3. 等待设备实时状态可用。首次录制应为空闲；若已经在录制，先确认当前会话用途，不要直接停止他人的会话。

```{figure} ../_static/images/recording-card.png
:alt: 网页录制与保存卡片：格式、固定保存位置、开始停止查询按钮、时长与已写入量，以及默认折叠的详情入口
:width: 325px
:align: center

录制卡片局部。先设置格式与存储；停止后展开底部“录制详情与使用说明”查看结果和设备路径。
```

仅在可信隔离局域网使用：此页面没有身份认证，能访问设备的人都可以开始或停止录制，不要暴露到公网或不可信网络。录制前先按[系统时间同步](../time-sync/system-time-sync.md)确认系统时间；共同时间轴不等于已证明物理同步。

### 1.2 选择格式和保存位置

在 **“保存格式”** 中按用途选择：

| 格式 | 保存内容 | 适合用途 |
|---|---|---|
| ROS bag | 一个 ROS1 bag v2.0 文件，包含四路 JPEG 图像消息、相机信息、帧元数据和原生 IMU | ROS1 消息工具、后续解包分析；录制本身不依赖安装 ROS |
| MP4 · 四路 H.264 | 一个 session 目录，包含四路 `cameraN.mp4`、时间戳索引、相机参数、原生 IMU CSV、曝光及状态/发布 sidecar | 直接播放四路视频，同时保留配套传感器数据；要求四路 H.264 编码 |

需要直接播放视频时优先选 MP4；选项不可用时先检查页面能力提示，不要把预览正常当成 MP4 条件已满足。MP4 不支持图像隔帧。

在 **“固定保存位置”** 中选择设备端存储：

| 选项 | 固定保存根目录 | 注意事项 |
|---|---|---|
| 运行目录 / eMMC | `/root/demo/save_data` | 固定绝对路径，不随可执行文件位置变化；不是电脑下载目录 |
| TF 卡 | `/mnt/sdcard/recordings` | 必须先按 [TF 卡使用](../getting-started/tf-card.md)确认实际挂载；缺卡或未挂载会失败，不会退回 eMMC |

选择“运行目录 / eMMC”时，设备分配 bag 文件 `/root/demo/save_data/session-<id>.bag` 或 MP4 会话目录 `/root/demo/save_data/session-<id>`，其中 `<id>` 由设备生成，以详情中的实际输出路径为准。已有数据仍在原目录，不会自动移动或删除。固定目录沿用既有符号链接安全检查，不能用符号链接绕过路径约束。

开始时设备会检查目标存储至少有 `64 MiB` 可用空间，但这不保证整个会话空间充足。详情中的“可用空间”关联已分配的会话路径，首次录制前可能仍为初始 `0 B`，切换存储选项也不会立即查询目标盘；具体见{ref}`录制详情逐项说明 <web-recording-details>`。网页不接受自定义路径，YAML `save_data.save_path` 不改写网页固定路径；CLI/YAML 保存路径语义及默认 `/root/demo/save_mp4/` 不变，自定义路径用下文进阶的 CLI/YAML 启动方式。

### 1.3 开始录制并观察

1. 普通录制保持“高级选项”默认值，点击一次 **“开始录制”**，等待设备确认。
2. 确认设备状态进入录制中，观察 **“时长（设备计时）”** 和 **“已写入”**。命令被接受、计时增加或字节增加都不等于最终数据完整。
3. 需要查实际会话、格式/存储、输出路径或丢弃计数时，展开底部详情。录制期间避免同时进行存储压测、大文件复制/下载、解压或数据转换，尽量只保留这一项大吞吐写盘任务。

“已写入”按十进制 MB 显示，达到 `1 GB` 后自动切换为 GB，保留两位小数（`1 MB = 1,000,000 B`，`1 GB = 1,000,000,000 B`）；仅换算显示单位，不改变设备原始字节统计。

状态缺失/过期、命令待确认、结果不确定或设备不允许开始时，控制会禁用。点击 **“查询状态”** 查看实际状态；超时不表示命令未执行，不要盲目重复发送。录制/存储故障报告失败或 partial，源故障仍可能停止采集。

### 1.4 停止、等待收尾并核对结果

1. 点击一次 **“停止录制”**。设备需要排空写入队列、关闭文件，并在 MP4 模式下完成封装；**不要在收尾期间断电、拔卡或删除输出文件**。
2. 等待停止/封装提示结束，展开 **“录制详情与使用说明”**。
3. 核对 **“最终结果”** 为 `published_complete`，且 **“完整性 / 清理”** 同时显示 **“数据完整：是 · 清理完成：是”**（API 为 `data_complete=true`、`cleanup_complete=true`）。随后还应按下文对应格式的验收要求核对实际载荷。
4. 记下本次 **“会话 ID”** 和 **“输出路径（设备端）”**。路径由设备分配，以最终显示值为准，不要猜测会话名。完整 MP4 是一个目录，bag 是一个 `.bag` 文件。

停止请求被接受、界面不再计时、MP4 可播放或 bag 可读取，均不能单独证明完整。`partial`、`failed`、`aborted`、`.partial` 或清理未完成不能当作完整数据；保留输出与错误信息用于恢复/诊断，未清理完成时不能开始新会话。

网页创建的动态会话无需退出采集进程即可判断最终结果，也会记录 `SENSOR_RECORDING_RESULT`。停录后相机、IMU 和网页预览继续运行，可再开始另一会话。**收起详情、关闭网页、刷新或断网不会停止录制**；重新打开后查询设备状态。刷新会恢复浏览器本地选项默认值并清除姿态预览零偏，不改变设备录制状态。`Esc` 仅退出单路视频放大，不用于停录。

(web-recording-details)=
### 1.5 展开“录制详情与使用说明”后怎么看

点击录制卡片底部的 **“录制详情与使用说明”** 展开；再次点击可收起。这只改变显示，不会开始或停止录制。以下为设备真实网页的空闲界面，仅会话 ID 已遮盖；没有为截图启动录制，也不是一次录制成功的示例。

```{figure} ../_static/images/recording-details.png
:alt: 设备网页展开后的录制详情，包含八项状态字段和底部四条使用说明；会话 ID 已遮盖
:width: 574px
:align: center

录制详情展开后的真实空闲状态。`0 B`、格式与结果为空、尚未分配路径，以及“数据完整：否”均需结合当前状态理解，不能当作录制失败或磁盘已满的结论。
```

#### 状态字段逐项说明

| 界面字段 | 含义与读法 | 判断边界 |
|---|---|---|
| 可用空间 | 设备返回的可用字节数，单位 `B`；按当前/上一次会话路径所在文件系统查询 | 首次分配路径前可显示初始 `0 B`；不是电脑剩余空间，也不是当前下拉框所选存储的预检结果。切换到 TF 后不能拿上一会话的 eMMC 数值判断 TF 容量 |
| 已丢弃组数 | bag 会话的 recorder 丢弃图像组计数；按组而非单路帧计 | 不是浏览器预览丢帧或 IMU 丢样计数；`0` 不证明整个采集链路无损，仍须核对最终结果与载荷 |
| 已丢弃编码帧数 | MP4 会话时，上一个字段改用此名称，显示四路 H.264 编码帧的合计丢弃数 | 不是四路共同组数，也不是 IMU 计数；不要与 bag 的“组”直接比较。空闲截图尚无 MP4 会话，因此显示“已丢弃组数” |
| 最终结果 | 停录收尾后返回的发布结果；空闲且无结果时为 `—`，活动会话未结束时为“尚未产生最终结果” | 完整发布应为 `published_complete`；`published_partial`、`aborted`、`cleanup_incomplete` 或 bag 的 `published_durability_unproven` 均不能当作完整成功。还须同时检查下方完整性/清理与实际载荷 |
| 会话 ID | 设备录制控制使用的标识，用于区分会话并关联状态与 `SENSOR_RECORDING_RESULT` | 控制器初始化时也已有 ID，单有数字不表示录制已创建；它不是时间戳，也不是 bag 内部的 session UUID。按本次实际值记录，不照抄截图或猜路径 |
| 格式 / 存储 | 设备报告的当前/上一次会话格式与存储；格式值为 `rosbag` 或 `mp4`，无会话时可为 `—` | 不是上方下拉框中准备下一次录制的选项；改下拉框不会迁移已有文件。首次空闲显示“运行目录 / eMMC”不表示已创建输出 |
| 输出路径（设备端） | 设备分配并返回的 bag 文件或 MP4 会话目录；尚无路径时显示“设备尚未分配路径” | 不是电脑路径或下载链接；结束后记下最终值。异常路径/产物只用于恢复诊断，路径存在不证明完整，不要在录制或收尾时删除 |
| 完整性 / 清理 | “数据完整”是 recorder 的完整性结果；“清理完成”表示内部收尾/资源清理状态 | “清理完成：是”不是文件已删除，也不等于数据完整。首次空闲的“否 / 是”表示还没有完整录制结果；录制中也不能据此提前判失败。最终应同时为“是”，清理未完成会阻止新会话 |
| 健康状态范围 | `callback_window` 表示动态录制回调窗口的健康检查口径，不是一个“健康通过”指示灯 | 不证明窗口外、整个 producer 或物理同步无损。当前网页/API 固定显示此值，不能识别启动自动 MP4 接管后的真实范围；该场景须按{ref}`启动自动 MP4 的既有边界 <startup-mp4-web-stop>`检查 sidecar 的 `imu_health_scope` 与最终结果 |

#### 底部四条使用说明

1. **可信局域网与权限**：页面没有登录鉴权，能访问设备的人可控制录制。仅在可信隔离局域网使用，不做公网端口映射或暴露到不可信网络。
2. **固定路径由设备分配**：“运行目录 / eMMC”使用固定绝对目录 `/root/demo/save_data`，不从可执行文件位置推导；TF 仍使用 `/mnt/sdcard/recordings`。网页不能输入自定义路径，也不提供下载按钮；TF 不可用不会退回 eMMC。已有数据不自动迁移或删除，符号链接安全约束不变。
3. **单会话与原生数据**：同一时刻只能录制一个 bag 或 MP4。保存的是原生 IMU 和对应相机数据；网页预览降频、滤波及姿态零偏校准只影响预览，不改变保存数据。MP4 是四路 H.264 文件，不是网页屏幕录像。
4. **断网不停录，停止还需收尾**：关闭网页或断网不会发出停录命令。命令超时先点“查询状态”，不要盲目重发；点击停止后继续等待设备的最终结果，期间不要断电或拔卡。最终完成后再按下一节复制数据。

### 1.6 取回保存的数据

确认会话已停止并完成收尾后，再使用 SSH/SCP 文件传输从设备复制数据；**当前网页没有文件下载按钮**。在文件传输工具中连接设备，打开刚才记录的最终输出路径，将 bag 文件或完整 MP4 session 目录复制到电脑。不要只复制四个 MP4 而丢掉时间戳、IMU、相机参数及其他 sidecar。

也可以在**电脑终端**执行以下示例。先把 `DEVICE_IP` 改为设备地址，并把 `REMOTE_PATH` 改为网页显示的真实最终路径；示例 `session-123` 不是固定会话名：

```bash
DEVICE_IP='<设备IP>'
mkdir -p ./recordings

# ROS bag：复制一个文件
REMOTE_PATH='/root/demo/save_data/session-123.bag'
scp "root@${DEVICE_IP}:${REMOTE_PATH}" ./recordings/

# MP4：复制整个 session 目录（按实际格式二选一）
REMOTE_PATH='/root/demo/save_data/session-123'
scp -r "root@${DEVICE_IP}:${REMOTE_PATH}" ./recordings/
```

TF 录制同样使用详情中的 `/mnt/sdcard/recordings/...` 实际路径。仅在复制并核对数据后再清理已确认的历史会话；录制中不要删除 staging、marker 或目标路径。MP4 离线转 JPEG 见第 6 节，bag 查看与解包见第 8 节。

### 1.7 高级选项与完整性边界

“高级选项”默认折叠，普通录制无需修改。bag 的图像隔帧默认 `0`（保存每组），最小丢组间隔默认 `10`；显式选择隔帧 `1`（交替保存）时，间隔必须为 `2`。MP4 不支持隔帧。间隔是丢组策略约束，不是持续无丢失保证。隐藏值无效时会自动展开并提示校验错误。

展开或收起高级选项/详情不会停止录制、重置当前选项或零偏，也不重建 WebRTC、SSE 或姿态 Worker。保存使用原生 IMU，网页预览降频、滤波和姿态校准不改变保存值。

下面第 2–5、7 节是**部署检查、自定义参数/路径和 CLI/YAML 启动录制的进阶用法**，不是日常网页录制的前置步骤。适用于 `sensor_demo --help` 同时提供 `--record-bag <absolute-path>` 和 `--record-mp4-dir <absolute-directory>` 的完整包。已有开机自启实例时，不要重复启动另一份 `sensor_demo`；需要手动运行时按{ref}`启停与开机自启动 <non-ros-autostart>`正常停止本包实例，保持 `cam-service` 运行。

(startup-mp4-web-stop)=
```{warning} 启动自动 MP4 的网页提前停录限制
[INFERENCE] 根据当前实现，CLI `--record-mp4-dir` 或 YAML `save_data.save: true` 创建的 MP4 会话由网页接管后，提前点击停止时既不采用有效的动态 callback window，也尚未取得应用退出时的 producer final health。因此即使封装成功，也不能满足 complete 判据，会发布为 partial；本项未在新烧录设备上复现验证，也未在本轮修复。

需要独立起停的完整会话时，从网页创建动态 MP4；需要自定义路径的启动自动 MP4 时，保留会话直到应用正常退出，再核对最终 health、结果及载荷。网页/API 当前固定显示的 `health_scope=callback_window` 不能用于判断接管会话的真实健康范围，以 MP4 sidecar 的 `imu_health_scope` 和最终结果为准。正常退出也不保证完整，其他错误仍按 failed/partial 处理。
```

动态 MP4 用 `imu_health_scope=callback_window` 检查本次窗口的原生样本、序号、计数差值与队列写入，等待首个有效 IDR，停止时有界等待共同编码组；这不证明窗口外或整个 producer 无丢失。进程退出后的 producer final health 仅用于仍活跃的启动自动会话。支持的帧率是参数范围，不是零丢失保证，负载边界见第 9 节。

高压 bag 在严格丢组策略耗尽时合法结束为 partial，不是持续压力通过。应用退出的正常收尾保持 IMU 输入直到 producer STOP 排空、consumer 排空后再关闭 writer；动态停录以本次 callback window 为边界，不停止 producer。历史 DDS 发布/接收差额仍未精确归因，不能仅凭保存序列连续证明所有路径头尾无损。旧组成的 FSYNC/长录结果不认证当前 IIO V3/ABI5 集成组成；本轮仅新增 non-ROS HO 保存短窗验证，不认证长录，见{ref}`能力与验证边界 <capability-verification-boundary>`。

| 模式 | 入口 | 主要输出 | 完整保存判据 |
|---|---|---|---|
| H.264 MP4 | `--record-mp4-dir` | 一个 session 目录 | `SENSOR_MP4_RESULT ... outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |
| ROS1 bag | `--record-bag` | 一个 `.bag` 文件 | `SENSOR_BAG_RESULT ... bag_outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |

启动命令行录制在进程退出时，还须检查退出码为 0 且对应 `SENSOR_*_RESULT` 明确完整。网页动态会话按上面的会话最终结果判断；`.partial`、`data_complete=no` 或相关错误只能作为恢复或诊断数据。

complete 首先是 recorder 发布结果，不证明所有物理样本或曝光观测均已保存。默认 `allow-counted` 只对无效六轴 payload 计数，strict 遇此失败。bag 检查会话/队列/写入错误；动态 MP4 按 `imu_health_scope=callback_window` 核对窗口内样本、序号、计数差值与队列写入，不等待 producer STOP 或认证窗口外完整性。仍活跃的启动自动会话使用 `imu_health_scope=producer_session`，应用退出后另要求有效最终 health、published=observed=admitted=written>0、scan=published、record=ACK、序号连续及零 fatal/overflow/invalid/push/evidence/quiesce 异常。旧 mapper-health 字段已移除；tmst 仍独立执行 `200µs` 计算 admission，不是物理精度。`transport_complete` 仅认证 STOP 集合，不覆盖 fence 外物理尾部；两种保存模式均须按实际健康范围与载荷核对。

相机图像/metadata 使用所选 observer/official realtime 触发估计或显式曝光中点估计。保存按启动 `imu_timestamp_mode` 每 burst 桥接 host MONOTONIC→REALTIME 或 tmst RAW→REALTIME；tmst 下也不覆盖原始 MONOTONIC 主机估计。bag `/imu/data` Header 与 MP4 `imu.csv` 的 `sample_realtime_ns` 是输出值。bag `/robobaton/imu/timing` JSON 和 CSV 保留模式、原始 FIFO low16 `fifo_tmst`、`sample_raw_ns`、`timestamp_uncertainty_ns`、原生 host/burst 证据、身份/来源，以及正确标注且独立的 MONOTONIC/RAW 桥基点与半宽。host 的 RAW sample 为零、样本不确定度 `UINT32_MAX`；桥不确定度与 tmst `200µs` 计算 admission 均不是物理精度。图像 CSV 仍为微秒量化组时间，exposure sidecar 保留逐路输入值。bag record time 独立读取 realtime 并保留回拨；MP4 播放仍相对/名义。共同 epoch 不代表物理同步，录制前先校时。

bag timing schema `robobaton_imu_timing_v2` 与 ROS2 `/robobaton/imu/timing` 一致；bag `/robobaton/session_config` 记录 `camera_timestamp_path`、`imu_timestamp_mode`。通过 [non-ROS YAML/CLI](non-ros-demo.md) 选择任一四组合，停止/重启后切换，均使用相同二进制与 IIO 采集/owner。每种组合均要求匹配的内核 IIO V3 capture 模块，现有 V2 模块不兼容，应用部署不升级模块。无 FSYNC 选项/topic/sidecar、spidev 或回退。official 绝不使用 SIF observer 时间，validity0/uncertainty `UINT32_MAX`。当前 non-ROS HO 短窗证据及未验收范围见{ref}`能力与验证边界 <capability-verification-boundary>`。不声明四组合保存验收；见[数据合同](../development/data-contracts.md#imu)。

bag `/cameraN/frame_metadata`、tee `camN/frames.jsonl` 和 MP4 `exposure.jsonl` 保存逐帧冻结的 `exposure`。`status=1` 是最新 ISP 观测估计，不是已证实的该帧实际曝光；`0` 是不可用，不沿用上一帧。MP4 sidecar 描述输入帧，可能多于实际编码帧，按相机及微秒量化的组触发时间对照 timestamp CSV。字段、关联键与误差边界见[逐帧曝光观测](../development/data-contracts.md#逐帧曝光观测)。

## 2. 进阶：版本与运行包一致性

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

板端还需可用的 `python3` 与匹配的 `libstdc++`。当前匹配的 Buildroot 镜像提供 Python `3.10.12` 和 C++/SDK 运行库，应用包不替代系统依赖。工具可用或 manifest 通过不等于所有保存路径已验收，见[当前镜像组成](../ops/system-flashing.md)。

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

## 5. 进阶：CLI/YAML 保存 H.264 MP4 session

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

### 5.2 YAML 配置启动

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

## 7. 进阶：CLI/YAML 保存 ROS1 bag

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

### 7.2 YAML 配置启动

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

运行包包含 `bin/rosbag_info.py`（Python 标准库实现，需要板端可用的 `/usr/bin/python3`；当前匹配镜像已提供 Python `3.10.12`）。保存完成后可直接在板端查看 bag 状态：

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
