# 四目相机保存数据应用说明

## 1. 适用范围

本文说明如何使用 non-ROS `sensor_demo` 保存以下两类数据：

1. ROS1 bag v2.0：四路同步图像、相机信息、帧元数据和独立 IMU；
2. H.264 MP4 session：四路 MP4、逐帧精确时间戳索引、相机参数、独立 IMU、session status 和 publication receipt。

本文适用于 `sensor_demo --help` 同时包含以下参数的运行包：

```text
--record-bag <absolute-path>
--record-mp4-dir <absolute-directory>
```

ROS1 bag 与 MP4 是两种互斥的保存模式，当前不能在同一个进程中同时开启。

| 模式 | 入口 | 主要输出 | 完整保存判据 |
|---|---|---|---|
| ROS1 bag | `--record-bag` | 一个 `.bag` 文件 | `SENSOR_BAG_RESULT ... bag_outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |
| H.264 MP4 | `--record-mp4-dir` | 一个 session 目录 | `SENSOR_MP4_RESULT ... outcome=published_complete data_complete=yes cleanup_complete=yes ... success=yes` |

只有进程退出码为 0 且对应 `SENSOR_*_RESULT` 明确报告完整，才可把数据作为正式完整数据使用。`.partial`、非零退出码或 `data_complete=no` 只能作为恢复或诊断数据。

## 2. 版本与运行包一致性

每次部署都必须复制完整 `demo/` 运行包，不能只替换 `sensor_demo` 或某一个 `.so`。

在开发机的公开 non-ROS 仓库中验证运行包：

```bash
cd <RoboBaton_4p_demo仓库>
python3 scripts/verify_runtime_package.py demo
```

在板端进入本次部署目录后验证：

```bash
cd <完整demo运行包目录>
sha256sum -c manifest.sha256
cat VERSION
./sensor_demo --version
```

`VERSION`、程序 `--version`、实际加载的 `libsc132`、`libprrtsp`、`libicm42688` 产品版本及 ABI 信息必须属于同一份包。不要混用系统目录、旧部署或其他工程中的同名动态库。

当前开发候选已统一使用产品版本`1.1.0`，公开changelog仍标记为“未发布”。正式创建`v1.1.0` tag前，必须使用同一组AArch64 ELF、`runtime-provenance.json`和`manifest.sha256`重新通过Host与目标板门禁。使用时以部署包内实际`VERSION`为准，不以文档标题推断版本。

## 3. 板端运行前检查

### 3.1 硬件与进程

当前稳定路径要求：

- 四颗相机全部连接；
- ICM-42688 INT1 采集链路可用；
- `cam-service` 正常运行；
- 同一时刻没有另一个 `cam_demo` 或 `sensor_demo` 占用相机；
- 默认稳定 trigger 模式为 `software_gpio`。

检查：

```bash
pgrep -a cam-service
pgrep -a -f '(^|/)(cam_demo|sensor_demo)( |$)' || true
```

不要用模糊 `killall` 或 `pkill -f` 清理未知进程。若发现另一个相机应用，应先确认其身份和用途，再按该应用自己的退出协议停止。

### 3.2 存储目录

保存路径必须是绝对路径，且父目录必须存在并可写：

```bash
mkdir -p /data/robobaton
findmnt -T /data/robobaton
df -h /data/robobaton
df -i /data/robobaton
```

不要把正式输出写入运行包目录。开始前应为视频、临时 staging、最终 publication 和故障保留空间预留足够容量。

### 3.3 环境与外部工具

优先运行包顶层 launcher；它会设置 `LD_LIBRARY_PATH` 和 `PATH`：

```bash
cd <完整demo运行包目录>
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
  format: rosbag
  save_path: /data/robobaton/session.bag
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

## 5. 保存 ROS1 bag

### 5.1 前台启动

30fps 完整保存基线：

```bash
cd <完整demo运行包目录>
./sensor_demo \
  --fps 30 \
  --sample-rate-hz 1000 \
  --print-rate-hz 0 \
  --record-bag /data/robobaton/run_30fps.bag \
  --record-frame-skip 0
```

若业务明确允许每隔一个完整同步 frame-set 保存一次：

```bash
./sensor_demo \
  --fps 30 \
  --record-bag /data/robobaton/run_30fps_skip.bag \
  --record-frame-skip 1
```

`record-frame-skip=1` 以完整 `group_id` 为单位保存一组、跳过一组，四颗相机共享同一个决策；它不会改变 RTSP 输出帧率。

### 5.2 YAML 启动

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
  sample_rate_hz: 1000
  print_rate_hz: 0
  print_metrics: false
save_data:
  save: true
  format: rosbag
  save_path: /data/robobaton/run_30fps.bag
  skip: false
```

然后运行：

```bash
./sensor_demo
```

### 5.3 正常停止

在前台按一次 `Ctrl+C`，或从已确认的控制终端向准确 PID 发送 `SIGINT`/`SIGTERM`：

```bash
kill -INT <sensor_demo-pid>
```

发送信号后必须等待程序完成：相机 admission 关闭、consumer join、RTSP close、SC132 blocking stop、IMU stop/join、队列 drain、writer close、文件 fsync 和原子 publication。不要立即发送 `SIGKILL`，也不要在未看到最终结果前关闭电源。

### 5.4 结果验收

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
- `SENSOR_IMU_RESULT` 中 samples 非零；
- timestamp/sequence gap、duplicate、regression 和 producer drop 均符合完整性要求；
- 最终路径来自 `SENSOR_BAG_RESULT path=`，不要只依赖配置路径猜测。

非零退出、`published_partial`、`.partial.bag` 或 quarantine 都不是正式完整数据，但应保留用于诊断，不要自动覆盖或删除。

## 6. 查看和解包 ROS1 bag

运行包不包含离线 Python 工具。将 bag 拷回含有公开源码的 Host，在 `RoboBaton_4p_demo` 仓库中执行：

```bash
python3 scripts/rosbag_info.py /data/robobaton/run_30fps.bag
python3 scripts/rosbag_info.py --yaml --freq /data/robobaton/run_30fps.bag
```

解包为 IMU CSV、相机参数和四路 JPEG：

```bash
python3 scripts/rosbag_extract.py \
  /data/robobaton/run_30fps.bag \
  /data/robobaton/run_30fps_dataset
```

输出目录必须不存在。当前工具支持未压缩、索引完整的 ROS1 bag v2.0；`.partial.bag` 可用于恢复分析，但不能因此升级为完整数据。

## 7. 保存 H.264 MP4 session

### 7.1 前台启动

```bash
cd <完整demo运行包目录>
./sensor_demo \
  --fps 30 \
  --codec h264 \
  --sample-rate-hz 1000 \
  --print-rate-hz 0 \
  --record-mp4-dir /data/robobaton/run_30fps_mp4
```

不要同时添加 `--record-bag` 或 `--record-frame-skip`。

若配置的 final 目录或对应 `.partial` 已存在，recorder 会选择同级的带 UTC 时间戳候选目录。必须以最终日志中的：

```text
SENSOR_MP4_RESULT path=<实际路径> configured_path=<配置路径>
```

为准。

### 7.2 YAML 启动

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
  sample_rate_hz: 1000
  print_rate_hz: 0
  print_metrics: false
save_data:
  save: true
  format: mp4
  save_path: /data/robobaton/run_30fps_mp4
  skip: false
```

### 7.3 正常停止与验收

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
- IMU final GPIO/FIFO/mapper/uncertainty-drop 为零；
- session 中存在匹配的 `publication_receipt.json`；
- session 目录中不存在 `.publication_incomplete` marker。

典型完整目录：

```text
run_30fps_mp4/
├── camera0.mp4 ... camera3.mp4
├── camera0_timestamps.csv ... camera3_timestamps.csv
├── imu.csv
├── camera_params.yaml
├── session_status.json
└── publication_receipt.json
```

MP4 的播放时间轴使用名义帧率；`cameraN_timestamps.csv` 中的纳秒时间戳才是每帧权威相机时间，按 `frame_index` 对齐。

退出码 2、`published_partial`、`.partial` 目录、marker 或 receipt 不匹配都不是完整 session。

## 8. MP4 转换为时间戳命名 JPEG

离线转换应在有完整 `ffmpeg` 和 `ffprobe` 的 Host 上执行。运行包内的 ffprobe helper 不能替代离线工具。

```bash
cd <RoboBaton_4p_demo仓库>
command -v ffmpeg
command -v ffprobe

python3 scripts/mp4_extract.py \
  /data/robobaton/run_30fps_mp4 \
  /data/robobaton/run_30fps_mp4_dataset
```

恢复数据也可转换：

```bash
python3 scripts/mp4_extract.py \
  /data/robobaton/run_30fps_mp4.partial \
  /data/robobaton/run_30fps_mp4_recovery_dataset
```

但 `conversion_summary.json` 会保留源 outcome，且 `source_data_complete=false`；转换成功不等于源数据完整。

默认要求四路 `0,1,2,3`。不得通过 `--expected-cameras` 只选子集来把不完整源伪装为完整；完整源必须与 status/receipt 中的四路 MP4 和 timestamp inventory 精确一致。

输出目录必须不存在。最终发布使用原子 no-replace，不覆盖并发创建的目录。

## 9. 帧率与压力边界

当前产品目标：

保存模式必须分开判定：

- ROS1 bag：30fps是完整保存硬门，40fps是扩展目标；50/60fps在高CPU或存储压力下允许明确、可计数、整组的partial，其中60fps是bag的stress档。
- H.264 MP4：25/30/40/50/60fps均属于稳定发布矩阵；正常运行必须exit 0、`published_complete`、零recorder drop并通过四路MP4/CSV/JPEG/IMU readback，不能把partial计为发布PASS。
- 两种模式在任何帧率都不允许崩溃、死锁、UAF、静默丢失后仍报告complete。显式故障注入可产生受控partial用于验证恢复，但不改变MP4稳定发布门。

Host/package GO不能替代板端验收。正式宣称某一帧率完整前，必须完成目标板持续运行、CPU压力、存储压力、SIGINT/SIGTERM、真实输出readback和服务恢复检查。

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

把该次运行视为失败或未证明完整。保存完整 stdout/stderr、退出码、进程和服务状态；不要仅凭 MP4 可播放或 bag 文件存在就认定成功。

## 11. 应用验收清单

- [ ] 整包 manifest 校验通过；
- [ ] `VERSION` 与程序/动态库版本来自同一包；
- [ ] `cam-service` 正常，未并发运行其他相机应用；
- [ ] 保存路径绝对、父目录可写、空间与 inode 足够；
- [ ] MP4 模式的 `ffmpeg`/`ffprobe` 检查通过；
- [ ] 只开启 ROS1 bag 或 MP4 中的一种；
- [ ] 通过一次 `SIGINT`/`SIGTERM` 正常停止并等待 finalize；
- [ ] 进程退出码为 0；
- [ ] 对应 `SENSOR_*_RESULT` 为 `published_complete`、`data_complete=yes`、`cleanup_complete=yes`、`success=yes`；
- [ ] 四路数量相等、非零，IMU final health 完整；
- [ ] 离线 readback/提取成功；
- [ ] `.partial`、quarantine 和 recovery 数据未被误标为正式完整数据。
