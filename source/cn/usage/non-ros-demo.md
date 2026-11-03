# non-ROS Demo 使用

[`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo) 是面向用户的 V2 non-ROS 公开源码仓库。联合入口 `sensor_demo` 提供四路 SC132 相机网页预览、ICM-42670-P 六轴/温度、惯性姿态预览，以及 ROS1 bag / H.264 MP4 录制；另有独立相机 RTSP、四路拼接 RTSP、IMU、UART 和 SocketCAN CAN 示例。

当前参数支持范围与实际验证范围分别定义，见{ref}`能力与验证边界 <capability-verification-boundary>`。控制台关联成功不证明保存图像可解码或全部样本已保存，不承诺所有路径持续高帧率或当前组成已完成长录。

## 1. 目录和运行包

常用入口：

```text
<non-ros-demo-root>/
├── demo/                    # 可直接部署到 X5 /root/demo 的运行包
│   ├── cam_demo
│   ├── sensor_demo
│   ├── mosaic_rtsp_demo
│   ├── imu_reader_demo
│   ├── serial_port_demo
│   ├── can_demo
│   ├── start_sensor_demo.sh     # sensor_demo 启停、重启与开机自启动管理
│   ├── env.sh
│   ├── config/sensor_config.yaml
│   ├── bin/
│   └── lib/
├── config/sensor_config.yaml
├── include/
├── lib/
├── scripts/
└── src/
```

部署时完整复制 `demo/` 目录内容。顶层 `cam_demo`、`sensor_demo`、`mosaic_rtsp_demo`、`imu_reader_demo`、`serial_port_demo` 和 `can_demo` 是启动脚本，会设置运行所需的 `LD_LIBRARY_PATH`；真实 ELF 位于 `bin/`。

网页服务 `bin/sensor_web` 及内嵌页面由 `sensor_demo` 统一启动和回收，不是单独运行的 Demo。使用网页功能须部署包含它的完整匹配运行包，不只复制网页、单个 ELF 或动态库。

## 2. 运行联合入口 `sensor_demo`

### 开机网页入口

随板预烧录的发布版系统已配置开机自动启动 `sensor_demo`。正常预览和录包不需要先 SSH 登录，也不要重复启动另一份程序：

1. 按{ref}`首次上电 <first-boot-web>`完成供电与网络连接，在同一可信局域网浏览器打开 `http://192.168.1.12/`；已修改地址时使用 `http://<设备IP>/`。
2. 等待设备连接，确认 CAM1～CAM4 画面持续更新、六轴遥测有效，再查看姿态或开始录制。页面连接成功不等于保存完整或硬件同步通过。
3. 需要录包时使用同一首页的“录制与保存”；停止录制后相机、IMU 与网页继续运行。切换应用或修改启动参数时，才按{ref}`启停与开机自启动 <non-ros-autostart>`正常停止整个应用。

```{figure} ../../image/4P_overview.png
:alt: RoboBaton 4P non-ROS 网页，包含四路相机、惯性姿态、六轴遥测和录制控制
:width: 100%
:align: center

non-ROS 联合入口的网页工作台（中文界面示例）。画面、数值、源参数与录制状态以当前设备为准。
```

网页资源离线内嵌，不需要互联网、插件或摄像头/麦克风权限。默认开启 Web、关闭 RTSP；四路视频和启用后的 RTSP 共用每路一次硬件编码，原生 IMU 采集独立于网页预览。

**移动端效果预览**：手机或平板接入与板卡互通的同一局域网后，可直接用浏览器打开上述设备地址，无需安装 App 或 SSH 登录。窄屏面板纵向排列，可滚动查看四路相机、姿态与六轴数据；自动播放受限时点击“点击播放”。网络、WebRTC/H.264 解码支持和移动设备性能会影响流畅度，不保证任意手机四路同时流畅。连接步骤见{ref}`首次上电 <first-boot-web>`。网页录制仍保存到板端，不是手机本机录像。

右上角语言按钮用 `CH` / `EN` 表示切换目标：中文页面显示 `EN`，英文页面显示 `CH`；默认中文，本浏览器允许本地存储时记住选择，存储被禁用时仍可在当前页面切换。切换更新静态文案、动态状态和无障碍提示，不刷新页面、不重建 WebRTC、SSE 或姿态 Worker，不重置录制选项、设备录制或已接受的陀螺零偏。刷新仍按下文恢复选项默认值并清除校准，但会保留可存储的语言选择。“在线文档 / Online Docs”随当前语言在新标签页打开[中文文档](https://4p-docs.readthedocs.io/zh-cn/latest/index.html)或[英文文档](https://4p-doc-en.readthedocs.io/en/latest/index.html)；访问在线文档需要互联网，设备页面和切换不依赖互联网。会话 ID、输出路径、API 状态码和设备原始错误保留原值。

### 首页功能与操作

所有功能集中在**同一首页**，无需在相机、IMU、诊断和录制页面之间切换。

| 首页区域 | 功能与操作 |
| --- | --- |
| 顶部实时摘要 | 查看相机连接数、源采集状态、原生/预览采样率和传感器温度；连接与采集状态分别判断。 |
| 相机 | CAM1～CAM4 以 2×2 网格显示，标题旁显示源分辨率、帧率和编码；双击画面放大/还原。 |
| 惯性姿态 | 查看板体坐标示意、Roll/Pitch/相对 Yaw、自动静置零偏估计状态；可手动“静置校准零偏”或“重置相对航向”。只影响浏览器预览。 |
| 六轴原始遥测 | 查看 X/Y/Z 加速度（`m/s²`）、角速度（`rad/s`）与最近 1 秒趋势，底部显示原生/预览采样率、样本序号、温度和通知缺口。 |
| 录制与保存 | 选择 ROS bag 或 MP4、运行目录/eMMC 或 TF，开始/停止录制、查询状态，查看设备计时时长和已写入量；展开详情查看输出路径和最终结果。 |
| 运行诊断 | 在工作区下方展开源状态、各路浏览器接收/解码、帧率与丢包信息；浏览器未报告的字段显示 `unknown`。 |

宽屏 **≥1440px**（CSS 像素）时，相机、姿态、六轴、录制四列等高并排；**1100–1439px** 时录制位于前三列下方，**768–1099px** 时相机/录制各占整行、姿态/六轴并排，小于 **768px** 时全部堆叠。宽度 **≥1440px** 且高度 **≥680px** 时工作区紧凑铺满视口、面板内部滚动；其余窗口正常页面滚动。

相机网格和单路放大按源比例完整显示，不裁剪或拉伸，源画面黑边保留。键盘聚焦画面后按 Enter/空格也可放大或还原；`Esc` 只返回网格，不停止录制。若浏览器阻止自动播放，点击画面中的“点击播放”。界面 CAM1～CAM4 对应内部 `camera_id` 0～3，API、录制文件名和索引仍使用内部 ID；并排画面不证明显示同步或 FSYNC 精度。

切换语言、放大画面、展开/折叠高级选项、详情或诊断都不重建 WebRTC、SSE 或姿态 Worker，不改变设备录制，也不清除当前页面已接受的零偏。**刷新恢复浏览器本地录制选项默认值并清除姿态零偏，但不会停止设备录制**；重新打开后查询真实状态。网页不提供相机分辨率、帧率、曝光、IMU 原生采样率或 FSYNC 硬件参数控制；分辨率、帧率、原生采样率、FSYNC 等启动参数在 YAML/CLI 配置后重启应用生效。

### 网页控制录制

使用首页常驻的“录制与保存”卡片，无需重启应用即可连续录制多个会话：

1. **选择格式和存储**：ROS bag 保存 JPEG 图像消息、相机信息及原生 IMU；MP4 保存四路 H.264 视频、时间戳索引、原生 IMU CSV 和 sidecar，不是网页屏幕录像。运行目录/eMMC 和 TF 均写在设备端，不是浏览器下载目录。
2. **按需调整高级选项**：普通录制可保持默认值。bag 可设置图像隔帧和最小丢组间隔，MP4 不支持隔帧；约束见下文。
3. **开始并观察**：点击“开始录制”，等待设备确认，查看实际录制状态、设备计时时长和已写入量。表单会检查实时状态与设备能力；状态缺失/过期、命令待确认或结果不确定、设备不允许开始时，不可开始录制。
4. **停止并核对**：点击“停止录制”后等待排空和封装，展开“录制详情与使用说明”核对输出路径、最终结果及完整性。停止请求被接受不等于文件完成，不要在收尾期间断电。

“已写入”使用十进制 MB 显示，达到 1 GB 后自动切换为 GB，保留两位小数（1 MB = 1,000,000 B，1 GB = 1,000,000,000 B）。仅显示单位换算；设备统计和 API 的原始字节计数不变。

原生 `<details>` “高级选项”默认折叠，内含图像隔帧与最小丢组间隔（默认分别为 0 和 10）；需要修改时再展开。另一默认折叠的“录制详情与使用说明”包含可用空间、丢弃组数/编码帧数、最终结果、会话 ID、实际格式/存储、设备输出路径、完整性/清理、健康范围及使用边界。**实际错误、命令结果不确定和停止排空/封装提示始终位于折叠区外**，不需要展开才能看到。隐藏的高级值无效时，先展开“高级选项”，再调用浏览器 `reportValidity()` 显示校验提示。折叠不重置选项；选择仅保留在当前页面，**刷新后恢复页面默认值，不会持久化**。

要停止录制，在常驻卡片中点击“停止录制”，随后等待设备排空和封装；只有设备最终返回 `published_complete`、`data_complete=true` 和 `cleanup_complete=true` 才表示本次会话完整发布，可展开“录制详情与使用说明”查看最终结果及完整性字段。录制停止后相机、IMU 与预览继续，可再次开始另一会话。

网页不能指定任意路径：运行目录固定为真实可执行文件目录下的 `recordings`（标准包为 `/root/demo/bin/recordings`），TF 固定为已挂载的 `/mnt/sdcard/recordings`；文件名由设备分配。MP4 要求四路 H.264 编码且不支持隔帧；bag 保留严格丢组间隔，隔帧为 1 时间隔必须为 2。同一时间只能运行一个 bag 或 MP4 会话。

TF 必须实际挂载在 `/mnt/sdcard`，缺卡或未挂载会明确失败，**不会退回 eMMC**。开始时要求至少 64 MiB 可用空间，不保证整个录制期间空间充足；先在详情中检查空间。网页固定路径不受 YAML `save_data.save_path` 改写；需要自定义路径时使用命令行或 YAML 启动录制。

关闭网页或断网不会停止录制；重新打开页面并查询实际状态。命令超时不代表设备未执行，不要盲目重发。录制/存储故障结束本次会话并报告失败或 partial，源故障仍按失败路径停止。保存读取原生 IMU，不使用网页降频/姿态滤波数据；动态 MP4 的健康范围为 `callback_window`，不等同于整个 producer 停止后的最终健康认证。启动参数 `--record-bag`、`--record-mp4-dir` 和 YAML `save_data` 自动录制保留，也可由网页停止；详见[数据保存](save-data-guide.md)。

**此页面没有身份认证。** 能访问设备的局域网用户可以开始写盘或停止会话；同源校验不是用户认证。仅用于可信隔离 LAN，不要暴露到公网或不可信网络。更新需成套重建运行包并正常重启应用；不能只替换网页或单个 ELF。

### 六轴预览与运行诊断

相机、IMU 遥测和保存分别观察：网页能打开但无视频时，检查是否使用 H.264、TCP `80` 与 UDP/TCP `8189` 是否可达，以及每路播放/连接状态；页面报连接或遥测过期时先查设备状态。不要通过停止 `cam-service` 或重复启动应用来恢复网页。需要维护时按{ref}`启停与开机自启动 <non-ros-autostart>`检查本包状态和日志。

- 六轴为设备坐标系 X/Y/Z，单位 `m/s²` 和 `rad/s`，不是姿态角。预览最多 `50Hz`，不改变原生采样或保存；主动抽取不是源丢样。超过 `500ms` 无新遥测标记失效；通知缺口不等于样本丢失。页面并排播放不证明四路显示或相机/IMU 同步，趋势图不用于频谱/标定。
- 趋势固定显示最近 **1 秒**，无时间窗下拉选项。加速度与角速度分别成图，每张图的 X/Y/Z 共用时间轴和纵坐标；纵轴上下限随当前窗口的三轴数据统一自动调整，标注数值刻度，保留原始绝对值，单位见加速度 `m/s²` / 角速度 `rad/s` 标题；横轴为距浏览器当前时刻的秒数。没有均值平滑、扣重力或扣零偏；接收间隔超过 `250ms` 时断线，不外推缺口。只改变有界预览，不改变采样、保存、姿态或连接。紧凑桌面空间不足时在遥测面板内滚动。
- 遥测标题下不显示趋势说明行；图表收紧面板左侧空白，按实际刻度文字宽度预留纵坐标边距，保留完整刻度，不裁剪视频或曲线。
- 姿态卡片在浏览器 Web Worker 中用 ≤50Hz 的姿态专用六轴输入融合四元数，动画板体显示 Roll/Pitch/相对 Yaw 与设备正轴。设备端只做降频前低通，不计算姿态或零偏；SSE 新增 `attitude_accel_mps2` / `attitude_gyro_rps`，原始六轴字段、原生采样、遥测速率、保存与公共 ABI 不变。Worker 不可用时显示明确状态，六轴和视频继续；静置零偏校准与精度边界见下文。
- 硬解由浏览器、OS、驱动和并发解码资源决定；没有诊断字段显示 `unknown`，不以“有 GPU”或能力提示代替实际 Video Decode 证据。当前功能未作为新软件版本发布；目标浏览器、双电脑稳态和 GPU 验收不能从 host 烟测外推。
- 页面无身份认证，所有可达用户可能看到视频/IMU；仅用于可信隔离 LAN。HTTP 页面、信令与遥测无传输真实性保护，SRTP 不保护 HTTP 信令；公网或不可信网络须另行配置 HTTPS、认证与访问控制。

### 姿态预览与静置零偏校准

设备在降频前逐个处理原生样本，对六轴执行四级一阶低通；单级极点为 `min(10Hz, 遥测上限×0.2, 原生采样率×0.2)`。默认 800→50Hz 时低频群延迟约 64ms，用于减少高频振动抽样混叠，不是角速度死区。姿态积分与零偏均值使用滤波值，静置质量检查仍使用原始六轴，不能通过滤波掩盖强振动。原始数值和趋势不变。时间不递增、序号重置或超过 100ms 原生样本缺口会重新播种滤波器；无效输入使姿态字段不可用，不外推缺失样本。字段合同见[数据合同](../development/data-contracts.md#web-姿态预览输入)。

世界 +Z 向上，姿态按当前重力初始化；原始和滤波加速度均在重力带内才修正倾角，带外仅陀螺积分。首次使用、进入新数据源会话或刷新页面后，将**实际设备保持完全静止**，Worker 会在约 **3 秒**低运动、重力一致的连续遥测窗口后自动初始化三轴陀螺零偏，无需先点击按钮。它检查最小样本数、连续时间戳、重力/角速度幅值、加速度与陀螺方差，以及窗口前后段的加速度与陀螺均值变化；检测到运动、强振动、数据稀疏或时间缺口会重置候选窗口，检测到运动期间不学习。

已有零偏后，自动更新要求完整约 3 秒静置窗口的**平均残余角速度向量模长 ≤0.002 rad/s（约 0.11°/s）**，并继续通过上述质量检查。更新采用 **6 秒时间常数**的指数跟踪以跟随缓慢零偏变化；接受自动估计不重置航向、不使姿态跳变。温度变化后可先让设备静置等待跟踪，也可手动重估。

已知零偏后还检查原始角速度在约 1 秒子窗口和末尾未满窗口的平均残余，避免低通延迟掩盖窗口末尾开始的转动；噪声过大时延后跟踪更新，不冻结航向。无效六轴、姿态输入或时间字段会丢弃未完成的自动窗口并中断手动校准，同一会话已接受的零偏保留。

姿态状态区提示自动静置估计的等待/采集进度及已估计/跟踪状态；这些状态只表示检查结果，不证明设备确实静止或绝对航向准确。Yaw 始终只是相对航向，精度边界见下文。

“静置校准零偏”按钮仍可显式手动重估：

1. 将**实际设备保持完全静止**，不要旋转或移动设备；仅让网页模型看起来静止不够。
2. 点击“静置校准零偏”，继续保持设备静止约 **3 秒**，直到页面报告成功或拒绝。
3. 若因运动、不稳定或数据稀疏被拒绝，保持静止、等待遥测稳定后重试。强振动也可能导致拒绝；失败不会覆盖此前已接受的零偏。

手动校准同样检查重力/角速度幅值、最小样本数、连续时间戳、加速度/陀螺方差及窗口前后段的均值变化；不合格的手动重估保留此前已知零偏。**所有四元数积分都先扣除已接受的三轴零偏；没有 Yaw 静止冻结、硬角速度死区或仅作用于显示的阻尼。** 自动跟踪只在完整合格窗口后调整零偏，不是把低角速度直接置零。

“重置相对航向”按当前重力重新初始化姿态，不把倾斜归零，在同一应用会话内保留已接受的零偏。超过 `500ms` 无有效姿态时冻结模型；重连或时间戳不递增/间隔超过 `250ms` 后重新对齐。时间不连续会取消尚未完成的候选窗口/手动校准并重新初始化姿态，但同一数据源会话内已接受的零偏保留；新数据源会话或刷新页面会清除零偏，之后静置约 3 秒可自动重新估计。

六轴数据无法完全区分零偏与匀速慢转：自动跟踪可能吸收低于上述门限的缓慢残余转动；首次估计或手动校准同样必须确保设备真实静止，不能仅靠质量检查判断静止，也不保证完美运动检测或保留任意慢转。校准后 ≥0.005 rad/s（约 0.29°/s）的真实转动仍应可测，不应被当作零偏消除。没有磁力计等外部航向参考，Yaw 不可观测且仍会漂移；不提供绝对或无漂移航向，不用于导航，也不代替完整传感器标定。运动加速度、振动、剩余偏置与遥测抽取均影响精度；此功能仅供预览。

部署此更新须重新构建 `sensor_demo`、包含内嵌页面/Worker 的 `sensor_web` helper 和完整运行包，成套替换后正常重启应用；仅刷新浏览器不会更新正在运行的内嵌代码。以上说明不代表已完成板端部署或验收，也不构成新软件版本发布。

这里的部署仅指经授权在用户设备上更新本地运行包，不是新软件版本发布，也不扩大现有验收范围。


### 手动运行与网络输出

以下为 SSH 维护和参数覆盖用法，不是开机网页使用的前置步骤。手动启动前正常停止本包后台实例，保持 `cam-service` 运行：

```bash
cd /root/demo
./start_sensor_demo.sh stop
./sensor_demo
```

下列命令是互相独立的启动示例；每次先在前台按 Ctrl-C 正常退出上一实例，或按上述脚本停止后台实例：

```bash
./sensor_demo --sample-rate-hz 1600
./sensor_demo --print-rate-hz 50 --print-metrics
./sensor_demo --diagnostics
```

```bash
./sensor_demo --no-web --rtsp    # 仅 RTSP，端口/路径保持原合同
./sensor_demo --web --rtsp       # Web 与 RTSP 同开，每路仍只有一次编码
./sensor_demo --no-web --no-rtsp  # 关闭两种网络输出，保存仍独立生效
./sensor_demo --web-port 8080    # 显式备用 HTTP 端口，访问 IP:8080
```

- 默认 HTTP 为 TCP `80`，WebRTC 媒体为 UDP/TCP `8189`；仅放通 HTTP 不能保证视频可达。RTSP 关闭时不创建内部或回环 RTSP 服务；开启后使用原端口与路径。`cam_demo`、拼接 demo 和 ROS2 默认不受此切换影响。
- `rtsp.bps/codec` 是所有消费者共用的编码参数；Web 视频仅支持 H.264。H.265 显示 unsupported、不静默转码，HTTP/IMU 可继续。MP4、bag 与 tee 不受网络开关控制；双关且没有编码保存消费者时不启 VENC，仍采集相机与 IMU。
- 端口冲突、Web 退出或慢客户端只使 Web 降级，不抢占服务、不把 RTSP 当隐藏兜底、不降低原有保存完整性要求。源采集故障仍执行原失败策略。网络恢复自动建立新会话，等待真实关键帧；仅停止的画面不能证明源已停止。
- UDP 发送队列短时拥塞按丢包处理；仅受影响的视频会话等待下一真实 IDR。关闭一个会话不修改共享 UDP socket 的发送期限，不因此关闭其他会话；持续网络不可达仍可能触发各自重连。

退出时会输出 IMU 摘要：

```text
SENSOR_IMU_RESULT samples=... invalid=... timestamp_duplicates=... timestamp_regressions=... effective_hz=...
```
未发生系统校时的窗口应检查 `timestamp_duplicates=0`、`timestamp_regressions=0`；对外 realtime stamp 允许随系统校时回拨，不能把跨校时窗口的回退单独当作硬件时序错误。还须检查序号、timing drop、最终健康计数和实际载荷。

`--imu-sample-drop-policy allow-counted` 为默认策略：身份可证明但 timing 预算不满足的样本计数丢弃，继续采集；`strict` 遇 timing/无效包拒绝即失败。身份无法唯一证明、时钟证书失效或硬件错误在两种策略下都停止。`--imu-start-order camera-first|imu-first` 控制启动顺序，默认 `camera-first`，不改变时间戳或关联合同。

(non-ros-yaml)=
## 3. YAML 配置

`sensor_demo` 启动时读取 `DEMO_DIR` 目录下的 `config/sensor_config.yaml`；未设置该环境变量时以当前目录为基准。命令行参数优先于 YAML。

默认配置结构：

```yaml
camera:
  # width/height: 1280x1088（默认）、640x480、720x480 或 1280x720，任一轴向
  width: 1280
  height: 1088
  fps: 30
  rotate: 0
  test_exposure_midpoint: false
rtsp:
  enabled: false
  bps: 4000
  codec: h264
  url: /PRR
web:
  enabled: true
  listen_address: 0.0.0.0
  port: 80
  imu_push_hz: 50
  max_video_sessions: 8
  max_imu_clients: 2
imu:
  sample_rate_hz: 800
  print_rate_hz: 10
  print_metrics: false
  fsync_enabled: false
save_data:
  save: false
  format: mp4
  save_path: /root/demo/save_mp4/
  skip: false
  drop_min_interval: 10
```

边界：

- `camera.width` / `camera.height` 支持 `1280x1088`（默认）、`640x480`、`720x480`、`1280x720`，两种轴向写法均合法，其余值在启动相机前拒绝。
- 完整四目路径固定为四路；单颗 sensor 诊断使用 `cam_demo --camera-id`。
- non-ROS公开帧率集合为25/30/40/50/60fps；默认`30`，其他值在启动相机前拒绝。
- `camera.test_exposure_midpoint` 默认 `false`；改为 `true` 并重启 `sensor_demo`，图像时间戳使用“触发时间＋半曝光时长”的估算曝光中点。显式 YAML 值优先于 `SC132_TEST_EXPOSURE_MIDPOINT`；旧配置省略此字段时沿用环境变量（未设置则关闭）。需要同时重建应用和支持该开关的 `libsc132.so`；不影响 IMU 时间戳或 bag record time。ROS1 bag 对齐读取图像 `header.stamp`，不要再加半曝光。曝光不可用时停止采集，不宣称已校准的真实曝光中点，详见 {ref}`数据合同 <test-exposure-midpoint>`。
- `rtsp.codec` 支持 `h264` 和 `h265`。
- `web.enabled`、`rtsp.enabled` 独立，CLI `--web/--no-web`、`--rtsp/--no-rtsp` 优先。Web 限额为每 camera 最多 2、全局最多 8 视频会话与最多 2 SSE 订阅；`imu_push_hz` 为 `1..50`，低 ODR 不补点；配置在重启应用后生效，不提供网页硬件控制。
- IMU 原生采样率支持 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；其他值明确拒绝，不会重采样。
- `save_data.format` 默认是 `mp4`，同时支持 `rosbag`；保存路径必须是绝对路径。

`save_data.save: false` 表示启动时不自动录制，不会禁用网页录制。改为 `true` 时按 YAML 指定的格式与绝对路径开始会话；网页可停止它。YAML 的自动录制设置与网页固定存储选择是两套入口，网页选择不会写回 YAML。

(non-ros-save)=

## 4. 保存四路图像与 IMU

正常开机使用优先按上面的[网页控制录制](#网页控制录制)操作。完整整包校验、ROS1 bag/MP4 互斥配置、优雅退出、结果验收、离线转换和恢复流程见[保存数据](save-data-guide.md)。下面是需要自定义路径或无人值守启动时的命令行用法，执行前先正常停止已有 `sensor_demo`。

ROS bag 保存适合保留 JPEG 图像帧、相机参数和 IMU 数据：

```bash
cd /root/demo
./start_sensor_demo.sh stop
./sensor_demo --record-bag /root/save_demo/record.bag
```

MP4 保存复用每路硬件编码的 H.264 访问单元，无需开启 RTSP 网络输出，保存四路视频和 IMU CSV：

```bash
cd /root/demo
./start_sensor_demo.sh stop
./sensor_demo --record-mp4-dir /root/save_demo/mp4_session
```

MP4 模式要求 `rtsp.codec: h264`、完整四路 camera mask `0x0f`，且不能同时启用 `--record-bag` 或 `record-frame-skip`。配置的 final 输出目录不得以 `.partial` 结尾；如果目标目录或同名 `.partial` 已存在，程序会自动写入同级 `<目录名>-YYYYMMDDTHHMMSSZ[-NNNN]`，退出摘要 `SENSOR_MP4_RESULT path=` 给出真实目录。

当前 MP4 session 包含 `camera0.mp4`～`camera3.mp4`、四路 `cameraN_timestamps.csv`、`imu.csv`、`exposure.jsonl`、`fsync.jsonl`、`camera_params.yaml`、`session_status.json` 和 `publication_receipt.json`。`fsync.jsonl` 始终创建，仅启用 FSYNC 后写入关联记录。MP4 使用名义 H.264 帧时间；timestamp CSV 保存微秒量化、以 ns 表示的 realtime 组触发时间，逐路原始值可见输入曝光 sidecar，开启 FSYNC 后也在关联记录中。曝光 `status=1` 是估计，不能当实际生效曝光；输入 sidecar 可能多于已编码帧。关联方式见[数据合同](../development/data-contracts.md)。`.partial` 仅用于恢复，不能当完整数据源。

离线转换 JPEG 数据集时，在开发机使用公开 demo 仓中的脚本：

```bash
python3 scripts/rosbag_extract.py /root/save_demo/record.bag /data/record_dataset
python3 scripts/mp4_extract.py /root/save_demo/mp4_session /data/mp4_dataset
```

## 5. 单独运行相机 RTSP

自启系统上先执行 `./start_sensor_demo.sh stop` 正常停止联合入口，再运行独立相机 Demo；不要停止 `cam-service`。

```bash
cd /root/demo
pgrep -a cam-service
./cam_demo
```

默认行为：四路、`1280x1088`、`30fps`、H.264、RTSP path `/PRR`。

常用参数：

```text
--fps <25|30|40|50|60>
--codec <h264|h265>
--rotate <0|90|180|270>
--bps <kbps>
--url <path>
--trigger-mode vin_lpwm
--diagnostics
--max-skew-ns <ns>
--frame-timeout-ms <ms>
```

Trigger 模式状态：

| 模式 | 当前状态 |
|---|---|
| `vin_lpwm` | 唯一支持的模式，VIN LPWM 硬件触发；其他值拒绝。 |

限制：`--width/--height` 接受 `1280x1088`（默认）、`640x480`、`720x480`、`1280x720`，两种轴向写法均合法，其余组合拒绝；缩放由 `libsc132` VSE 硬件整幅拉伸完成，不改变 FOV。`--rotate 180`只支持`30fps`，不支持`25fps`、`40fps`、`50fps`和`60fps`。对外 NV12/RTSP 画布在旋转 `0/180` 时宽高不变（如 `1280x1088`、`640x480`），旋转 `90/270` 时宽高交换（如 `1088x1280`、`480x640`）。相机、RTSP、ROS1 bag和H.264 MP4使用同一`25/30/40/50/60fps`公开帧率集合。

默认四路 RTSP：

```text
CAM1 / cam0 -> rtsp://192.168.1.12:554/PRR
CAM2 / cam1 -> rtsp://192.168.1.12:555/PRR
CAM3 / cam2 -> rtsp://192.168.1.12:556/PRR
CAM4 / cam3 -> rtsp://192.168.1.12:557/PRR
```

其中 CAM1/CAM2/CAM3/CAM4 是板上物理丝印，cam0/cam1/cam2/cam3 是软件相机 ID。
以上使用出厂默认 IP；板卡地址已修改时替换 URL 中的地址。

单颗 sensor 诊断：

```bash
./cam_demo --camera-id 0 --diagnostics
./cam_demo --camera-id 1 --diagnostics
./cam_demo --camera-id 2 --diagnostics
./cam_demo --camera-id 3 --diagnostics
```

每次只运行一个 `cam_demo`。该模式用于排查单颗 sensor、FPC、供电、I2C 和 MIPI/VIN 链路，不代表 2 路或 3 路组合能力。

`cam-service` 是相机运行依赖，保持其运行。切换 `sensor_demo`、`cam_demo` 或用户自研相机应用前，先正常退出旧相机应用，避免 camera/VIO/编码资源冲突。

(non-ros-mosaic)=

## 6. 四路拼接 RTSP（mosaic_rtsp_demo）

`mosaic_rtsp_demo` 把四路 SC132 `1280x1088` NV12 frame-set 在 CPU 内合成为一张 `2560x2176` 的 hbmem NV12 DMA 输出缓冲，并通过 `libprrtsp.so` 的 external NV12 输入输出固定 H.264 RTSP，避免 PRRTSP 再复制整帧。

```bash
cd /root/demo
./mosaic_rtsp_demo
./mosaic_rtsp_demo --fps 40
./mosaic_rtsp_demo --fps 50
```

固定 RTSP 地址：

```text
rtsp://<x5-ip>:558/PRR
```

该程序为固定形态，不提供相机分辨率、码率、编码或 RTSP 端口/路径配置：

- 固定四路、H.264、8000kbps、正装方向，输出 `2560x2176`，RTSP 端口 `558`、path `/PRR`。
- `--fps` 支持 `25|30|40|50|60`，默认 `30`。

退出时输出运行统计：

```text
queue_full_drop=... invalid_group=... copy_failure=... send_failure=...
retain_release_balance=... copy_duration_avg_ms=... send_duration_avg_ms=...
```

- `retain_release_balance=0` 表示跨线程保留的 SC132 frame 已全部归还，无帧泄漏。
- `queue_full_drop`、`invalid_group`、`copy_failure`、`send_failure` 为 `0` 表示运行期间无队列丢弃、无无效帧组、无合成或发送失败。
- `copy_duration_avg_ms`、`send_duration_avg_ms` 为合成与 RTSP 发送的帧耗时均值，用于判断档位余量。

与 `cam_demo`/`sensor_demo` 一样，`mosaic_rtsp_demo` 独占四路相机资源，运行前先退出其他相机应用，并保持 `cam-service` 运行。

## 7. 单独运行 IMU

先正常停止 `sensor_demo` 等已占用 IMU 的应用，再运行独立 IMU Demo；停止网页录制不会释放 IMU 设备。

```bash
cd /root/demo
./imu_reader_demo
./imu_reader_demo --sample-rate-hz 1600 --count 10000
```

默认按 `10Hz` 打印抽样记录；程序仍消费全部 IMU 样本。需要看指标时使用：

```bash
./imu_reader_demo --print-metrics
```

正常停止后，`imu_reader_demo` 输出一条 `IMU_RUNTIME_HEALTH final=yes`，包含会话有效性、producer/consumer 样本数、输出丢弃和最终采集诊断计数。样本及最终摘要均为非阻塞尽力输出；缺失摘要不能判定健康通过。`--print-rate-hz 0` 只关闭样本打印，不关闭最终摘要；字段判读见[数据合同](../development/data-contracts.md#imu)。

关键字段：

- `ts_ns`：`CLOCK_REALTIME` 域的 IMU sample 时间戳，单位 `ns`，由 FIFO TMST→RAW→realtime 实测映射提供；`host_ts_ns` 为该包 SPI FIFO burst 成功完成时的 RAW 观测，经当次系统时钟桥接转换为 realtime，同 burst 可重复、FSYNC 延迟发布保留转换后的原值，不是 IRQ 沿、样本或曝光时间。两类时间均随系统校时回拨；按 `sample_seq` 判断顺序。`TIME_BASE domain=realtime realtime_start_ns=...` 仅声明启动参考，不冻结 offset。
- `accel_mps2`：加速度，单位 `m/s^2`。
- `gyro_rps`：角速度，单位 `rad/s`。
- `uncertainty_us`、`gpio_gap_count`、`fifo_overflow_count`、`mapper_failure_count`：时间戳映射和采集链路诊断。

V2 `accel_mps2` 按 `[X, Y, Z]` 输出；PCB 安装方向和符号尚待实板六面/旋转验证，当前不声明相对于主板或相机的正负轴及坐标变换。

IMU INT1 使用 `34120000.gpio` offset `8`，FIFO TMST 为逐样本时间；相机使用 LPWM，输出时间来自 VIN 随帧传播的触发捕获，不是到帧时间。相机和 IMU FSYNC 共用同一物理 IO；这不自动提供 FIFO 样本与曝光的一一对应。

显式关联使用 `sensor_demo --fsync --sample-rate-hz 1600` 或 YAML `imu.fsync_enabled: true`（默认关闭，仅支持 `800/1600Hz`）。不保存时 stdout 输出 `robobaton_fsync_v1` JSON；保存时进入 bag `/robobaton/fsync` 或 MP4 `fsync.jsonl`。仅 `status=1` 表示唯一匹配；检查 timing drop、序号缺口和 `SENSOR_FSYNC_RESULT`，不把样本对应误称为曝光同步，详见[数据合同](../development/data-contracts.md)。

运行需要实时调度权限：相机捕获 `SCHED_FIFO/60`、IMU owner `SCHED_FIFO/20`、联合应用 IMU consumer `SCHED_RR/3`；相机 observer 继承允许 CPU 集合，每轮休眠 `50µs`。IMU 不再使用独立 INT1 时钟 observer，INT1 仅唤醒；GPIO 通知序号缺口仅诊断、不单独失败。调度设置失败拒绝启动。应用不自动修改 IRQ/debug 或实时配额，重构不修复 GPIO/kernel 根因，高负载仍可能显式丢样或失败；验收须读取成功 stop 后的 `IMU_RUNTIME_HEALTH final=yes health_valid=yes` 并核对实际载荷，不只观察终端输出。

## 8. 串口 Demo


UART1/UART7 逻辑电平为 `3.3V`，设备节点为 `/dev/ttyS1`、`/dev/ttyS7`；DEBUG_UART 为 `1.8V`，不适用于 `serial_port_demo`。UART1 为 CN1 GH1.25 4pin，UART7 为 CN2 GH1.25 5pin；UART7 的 4 号针为独立 PPS 输入，无需切换 RX/TX。针号与线序见{ref}`接口接线示意图 <wiring-diagram>`。供电脚额定负载和热插拔条件仍待确认，默认断电接线，不接适配器 VCC，不反灌；见[硬件连接与安全](../getting-started/hardware-and-safety.md#uart)。

```bash
cd /root/demo
./serial_port_demo
```

默认配置是 `/dev/ttyS1`、`115200`、`txrx`。常用示例：

```bash
./serial_port_demo --port /dev/ttyS1 --mode tx --baud 115200 --text "hello-x5"
./serial_port_demo --port /dev/ttyS7 --mode rx --baud 115200
./serial_port_demo --port /dev/ttyS1 --mode txrx --baud 115200 --count 10 --text "ping"
./serial_port_demo --port /dev/ttyS7 --mode echo --baud 115200
```

UART 信号退出修复仅覆盖 RX 等待：收到 `SIGINT`/`SIGTERM` 正常退出并恢复串口设置，其他信号不延长 RX deadline，真实 I/O 错误仍失败；不扩展为所有串口模式或硬件可靠性验收。

## 9. 验证建议


- 网页：确认四路实际画面持续更新、六轴有效、姿态状态可用；展开运行诊断检查接收与解码信息。显示 `unknown` 不代表软件或硬件解码已经通过。
- RTSP：仅在显式开启 RTSP 或运行 `cam_demo` 时用 `ffprobe`/播放器检查四路 codec、分辨率和帧率；默认网页模式不要求 RTSP 端口存在。
- 录制：按设备最终结果、完整性/清理字段与实际文件检查，不用开始/停止按钮确认或已写入量代替完整性判据，详见[数据保存](save-data-guide.md)。
- IMU：正常停止应用后检查最终健康计数、样本序号和实际载荷；跨系统校时的 realtime 回拨不能单独判为硬件时序错误。
- 运行包与资源：始终整包部署，不混用同名 `.so`；切换相机/IMU 应用前正常退出旧实例，保持 `cam-service` 运行。

(non-ros-autostart)=

## 10. 启停与开机自启动

运行包顶层脚本 `start_sensor_demo.sh` 管理 `sensor_demo` 的启停、重启和开机自启动：

随板预烧录的发布版系统已启用自启动，正常开机使用不需要再执行 `enable`。下面命令用于按需维护；手动前台启动前须先正常停止后台实例。

```bash
cd /root/demo
./start_sensor_demo.sh            # 前台启动 sensor_demo（等效 ./sensor_demo）
./start_sensor_demo.sh stop       # 正常停止本包的主进程并等待录制/Web 收尾
./start_sensor_demo.sh restart    # 停止成功后按包内配置后台启动
./start_sensor_demo.sh enable     # 安装开机自启动（需要 root）
./start_sensor_demo.sh disable    # 取消开机自启动（需要 root）
./start_sensor_demo.sh status     # 查看自启动与运行状态
```

开机自启动通过板端 `/userdata/startup.sh` 实现：系统 `S99auto_startup` 在 `/userdata` 挂载后执行该文件。脚本只追加/删除自己带 `SENSOR_DEMO_AUTOSTART_MANAGED` 标记的块，不会覆盖其它应用写入的内容；取消自启动时若文件只剩余注释/空行残留会整体删除。镜像内 `wifi_setup` 使用独立启动入口，不占用该文件。开机自启动使用运行包内默认配置，直接修改 `config/sensor_config.yaml` 即可调整，无需重新执行 `enable`。`enable`/`disable` 需要 root 权限。

`stop`/`restart` 通过 `/proc/<pid>/exe` 识别本包 `bin/sensor_demo` 和 `bin/sensor_web`，使用 Linux pidfd 绑定进程身份；同名但来自其他目录的进程不属于管理对象。`stop` 仅向主进程发送 `SIGINT`，由主进程完成录制保存、资源释放与 Web 子进程回收；重复停止已退出的程序也成功。默认最多等待 1800 秒，可通过 `SENSOR_DEMO_STOP_TIMEOUT_S` 设置正数秒；超时返回非零，不强杀，`restart` 也不会启动新实例。正常运行板端需要支持 pidfd 的 Linux/Python 3.10 或更新版本。

`restart` 使用包内 `config/sensor_config.yaml`，不保留上次命令行参数；后台日志默认写入 `/userdata/sensor_demo_autostart.log`，可用 `SENSOR_DEMO_LOG_FILE` 指定。返回成功仅表示新进程启动后 2 秒内未退出，不是相机/IMU/Web 就绪保证；仍需检查日志和实际页面。`stop`/`restart` 不改变自启动注册、不停止或重启 `cam-service`；不要与手动启动相机应用并发执行。

(non-ros-can)=

## 11. CAN Demo

`can_demo` 使用 Linux SocketCAN `CAN_RAW` 接口操作 TCAN4550 驱动注册的网络设备。默认使用经典 CAN（载荷 `0..8` 字节）；`--fd` 显式开启 CAN FD 发送（最长 `64` 字节）或经典/FD 混合接收。两种格式均支持 11-bit 标准和 29-bit 扩展 ID；经典 CAN 可接收远程帧，FD 没有远程帧。不支持错误帧订阅或自动回包。程序不直接访问 SPI、不修改设备树、GPIO、bitrate 或接口状态，也不依赖相机/IMU 运行库或 `cam-service`。

### 前置条件与接口配置

- BSP 已启用 CAN、CAN_RAW、M_CAN/TCAN4550 驱动，并正确配置 SPI、IRQ、时钟、供电与 pinmux。没有 `can0` 时先修复 BSP，不靠应用自动创建接口。
- 按正式 V2 标识断电连接 CAN_H、CAN_L 与参考地；不要按 UART/TTL 接线。总线两端按规范配置 `120Ω` 终端，确认既有终端后再接入，不猜测连接器针序或板载终端状态。
- 对端必须使用相同 bitrate，并处于可接收/ACK 的工作状态。下面的 `500000` 仅为示例，不是板卡固定默认值。接口名以现场枚举为准。

以下配置需 root 或网络管理权限，且会中断该 CAN 接口；先确认没有其他 CAN 应用或控制业务正在使用，再手动执行：

```bash
ip -details -statistics link show can0
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 fd off
ip link set dev can0 up
ip -details -statistics link show can0
```

使用 CAN FD 时，两端均须支持 FD，并匹配仲裁段和数据段速率、ISO/non-ISO 模式；下面 `500000` / `2000000` 只是示例。确认接口没有其他业务使用后，手动将其配置为 FD，再运行带 `--fd` 的 demo：

```bash
ip link set dev can0 down
ip link set dev can0 type can bitrate 500000 dbitrate 2000000 fd on
ip link set dev can0 up
ip -details -statistics link show can0
```

FD 接口的 MTU 应为 `72`；`--fd` 遇到经典接口 MTU `16` 会失败，不自动重配置。`--brs` 决定发送帧是否在数据段切换速率，对端需能接收对应帧。经典 CAN 默认模式也可以在 FD 接口上发送/接收经典帧，但不会接收 FD 帧。

若命令不支持 CAN 参数，需安装支持 CAN 的 iproute2；若驱动探测失败、接口未注册或处于 BUS-OFF，先检查 BSP、接线、终端、对端和 bitrate，不停止或重配 `cam-service`。程序遇到接口不存在、非 CAN 设备或未 UP 会明确失败。

### 收发示例

终端 A 接收；默认持续等待，按 Ctrl-C 正常退出：

```bash
cd /root/demo
./can_demo --interface can0 --mode rx
# 有限接收：10 帧，每次等待的空闲超时为 5 秒
./can_demo --interface can0 --mode rx --count 10 --timeout-ms 5000
```

发送示例（外部节点先准备好接收）：

```bash
cd /root/demo
./can_demo --interface can0 --mode tx --id 123 --data 0102030405060708 --count 10 --interval-ms 100
./can_demo --interface can0 --mode tx --extended --id 1ABCDE --data AABB
./can_demo --interface can0 --mode tx --id 123 --data ''
```

CAN FD 示例（先完成 FD 接口配置，外部节点先准备好接收）：

```bash
# 混合接收经典数据/远程帧与 FD 数据帧；不是只接收 FD 的过滤器
./can_demo --interface can0 --mode rx --fd --count 10 --timeout-ms 5000
# 12 字节 FD，不切换数据段速率
./can_demo --interface can0 --mode tx --fd --id 123 --data 000102030405060708090A0B
# 16 字节扩展 ID FD，开启 BRS
./can_demo --interface can0 --mode tx --fd --brs --extended --id 1ABCDE --data 000102030405060708090A0B0C0D0E0F
```

| 参数 | 语义 |
|---|---|
| `--interface <name>` | 默认 `can0`；仅操作已注册且 UP 的 CAN 设备 |
| `--mode <rx\|tx>` | 默认 `rx`；不会默认发帧 |
| `--id <hex>` | TX ID，默认 `123`；可带 `0x`，标准范围 `0..7FF`，扩展范围 `0..1FFFFFFF` |
| `--extended` | 显式选择 TX 29-bit ID；数值大小不会自动切换格式 |
| `--fd` | TX 使用 FD 帧；RX 接收经典与 FD 混合帧；要求接口启用 FD、MTU `72` |
| `--brs` | TX 数据段速率切换，必须同时使用 `--mode tx --fd`；不是 RX 过滤器 |
| `--data <hexbytes>` | TX 默认 `0102030405060708`；经典 `0..8` 字节；FD 接受 `0..8,12,16,20,24,32,48,64` 字节，其他长度拒绝且不隐式补零；偶数个 hex 字符，无分隔符，空字符串表示零载荷 |
| `--count <n>` | RX 默认 `0`（持续）；TX 默认 `1`；显式 `0` 持续运行至 Ctrl-C |
| `--interval-ms <n>` | TX 帧间等待，默认 `1000`，范围 `1..3600000` ms；不是实时发送周期保证 |
| `--timeout-ms <n>` | RX 每次等待的空闲超时，默认 `0`（无限），范围 `0..3600000` ms；不是整个会话超时 |
| `--help` / `--version` | 单独使用，不打开 CAN 硬件 |

发送专用参数要求 `--mode tx`；`--fd` 可用于收发，`--brs` 还要求 `--fd`。非法参数退出 `2`，接口/I/O/接收超时失败退出 `1`，计数完成或 SIGINT/SIGTERM 正常中断退出 `0`。经典输出不变，形如 `rx 123#0102030405060708`，扩展 ID 固定 8 位，远程帧如 `rx 123#R8`。FD 输出为 `ID##<flags><data>`，flags 是一个十六进制数字，bit 0 为 BRS、bit 1 为 ESI；例如 `rx 123##1000102030405060708090A0B` 表示 BRS 置位的 12 字节 FD 帧。ESI 由发送控制器报告，demo 不提供设置 ESI 的参数；`--extended` 只改变 ID 格式，不开启 FD。

### 验证与限制

`tx_queued=N` 只表示 N 帧被内核接受，不表示对端收到或每帧已在总线上完成。默认 SocketCAN 本地回环可能让同机另一个接收进程看到发帧；这不能证明外部接线、收发器或 ACK 正常。外部验收须在第二个物理节点核对 ID、格式、载荷和计数，再反向发帧确认本板接收，同时检查 `ip -details -statistics link show can0` 的错误、丢帧和 BUS-OFF 状态。host 数据报逻辑测试、vcan 或 `--help` 不代替这一步。

应用支持 FD 不等于当前 BSP 已通过实板完整性或持续吞吐验收。受影响 BSP 的长 FD 载荷可能损坏，不能仅凭收齐帧数、没有总线错误或短帧通过认定可靠；须先使用匹配的已修复 BSP，并在第二个物理节点逐字节核对长载荷、FD/BRS 标志及双向计数。组合负载、延迟和错误恢复仍未完整闭环，不对当前整机组合承诺吞吐；见{ref}`能力与验证边界 <capability-verification-boundary>`。

单独编译使用 `scripts/build_can_demo.sh`，完整打包使用 `scripts/package_runtime.sh`，详见[公开 Demo 源码编译](../development/open-source-build.md)。
