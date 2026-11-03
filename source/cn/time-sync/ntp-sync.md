# NTP 同步

NTP 校准 X5 的 `CLOCK_REALTIME`。可选择开机持续授时，或使用手动恢复脚本；两者不是同一个入口。没有 RTC 电池时，断电不能保持 UTC；保存配置不等于保存当前时间。

NTP 不要求互联网，但要求板卡能通过网络访问时间服务器。公网源、局域网自建源和完全无网络的边界见下表。PPS 只提供边沿，不自动给出日期或校准系统时间；PTP master 的时间方向仍是系统时间经 PHC 向外提供，见[时间同步](system-time-sync.md)。

## 选择授时方式

| 方式 | 板卡需要什么 | 时间可信度 |
|---|---|---|
| 公网 NTP | 到配置源的路由、域名解析和 UDP `123` | 取决于上游及网络；默认公共源未认证，不保证精密同步 |
| 自建局域网 NTP | 到指定服务器的网络及 UDP `123`；数字 IP 不需 DNS，同网段不必有互联网网关 | 取决于服务器；可由可信上游或 GNSS 等参考提供 UTC |
| 隔离局域网、本机时钟作源 | 一台指定的时间服务器及局域网 | 只能统一设备时间；无可信参考就不能声明准确 UTC |
| 完全无网络、无外部时间源 | 人工校时或另行集成授时硬件 | 无电池时每次断电后都需重新授时；不能用保存配置恢复真实 UTC |

## 开机自动授时

本节适用于已提供开机 NTP 功能的系统。正常使用时只需连接可访问时间服务器的网络，无需逐板安装配置脚本，也无需每次开机执行手动校时命令。

- `ntpd` 开机启动，使用 `/etc/ntp.conf` 中的服务器持续校准系统时间；默认源为 `0.pool.ntp.org` 至 `3.pool.ntp.org`，不是自动扫描局域网寻找任意服务器。
- 使用域名源时需要可用 DNS，所有源均需网络路由和 UDP `123` 可达；数字 IP 不需要 DNS。同网段自建源不要求互联网。
- 开机未联网时仍可进入系统，联网后按守护进程的轮询／解析重试节奏授时，不保证立即完成。
- 无 RTC 电池时，断电后不能保持 UTC；每次开机都要重新确认授时状态。没有可用时间源时，不应把系统显示的日期当作准确 UTC。
- 采集不自动等待授时，首次校正可能使系统时间跳变。开始时间敏感录制前，先按[检查同步状态](#检查同步状态)确认同步；不要在采集中执行手动校时或重启授时服务。

可在板端检查服务和同步工具：

```bash
pidof ntpd
command -v ntpq
```

进程存在不等于已同步。若系统没有这些工具或开机服务，先联系技术支持确认该系统是否提供此功能；不要把复制 Demo 当作启用 NTP 的步骤。

## 更换 NTP 服务器

以下操作均在板端以 `root` 执行。先退出 demo、ROS2 节点和其他时间戳敏感任务，保持 `cam-service` 运行。不要同时运行另一个校准 `CLOCK_REALTIME` 的服务；PTP 的使用方向见[时间同步](system-time-sync.md)。

先备份当前配置，再编辑 `/etc/ntp.conf`：

```bash
cp -p /etc/ntp.conf "/root/ntp.conf.$(date +%s).bak"
vi /etc/ntp.conf
```

保留访问限制、drift 等其他配置，将原有 `server`／`pool` 时间源替换为实际服务器。以下 `192.0.2.10` 是文档示例，必须换成现场固定可达地址：

```text
server 192.0.2.10 iburst
```

可增加多行 `server` 使用多个一致的可信源。完全不访问公网时，移除全部公网 `server`／`pool`，并检查 include 或动态来源配置没有继续加载公网源。不要只增加一行内部源而保留公网 fallback。

保存后重启 NTP 服务，再检查同步状态：

```bash
/etc/init.d/S49ntp restart
ntpq -pn
ntpq -c rv
```

选星可能需要等待，并不保证重启后立即出现。配置保存在 `/etc/ntp.conf`，后续开机继续使用；如果编辑提示只读或无法保存，停止操作并联系技术支持确认配置入口，不要强制改挂载或启动文件。重启 NTP 可能使系统时间跳变，完成同步后再恢复采集。


## 自建 NTP 服务器

推荐选局域网内一台有稳定时钟、固定地址的 Linux 主机提供时间，X5 仍作为客户端，不必把板卡改成服务器。以下为独立 Ubuntu 服务器上的 chrony 示例；它不是在 X5 上安装另一套时钟 owner。主机应只有一个系统时钟授时服务，服务切换在维护窗口执行。客户端子网 `192.0.2.0/24` 也是示例，按现场修改，不对整个互联网开放 UDP `123`。

### 有可信上游或参考时钟

服务器安装 chrony，在 `/etc/chrony/chrony.conf` 保留实际可信上游或参考时钟配置，并增加客户端访问许可：

```bash
sudo apt install chrony
```

```text
allow 192.0.2.0/24
```

GNSS／参考时钟需独立配置并验证，不能只接一个 PPS 就认定 UTC 正确。按服务器防火墙／交换机策略仅放行允许客户端到 UDP `123` 的请求及回包，然后使服务生效、检查上游和监听状态：

```bash
sudo systemctl enable --now chrony
sudo systemctl restart chrony
chronyc tracking
chronyc sources -v
sudo ss -lunp 'sport = :123'
```

服务器自身同步正常后，再按前述“更换 NTP 服务器”配置 X5。不要把“UDP 已监听”当作服务器已有可信 UTC。

### 无互联网、只统一局域网时间

没有 GNSS 等可信参考而只需各设备跟随同一个本机时钟时，可在专用隔离服务器明确选择 chrony 的 local 模式。先备份旧配置、停止冲突 owner，校准服务器时间，再采用以下最小 `/etc/chrony/chrony.conf`；不要同时保留其他 `pool`／`server` 或通过 include／动态来源加载的公网配置：

```text
driftfile /var/lib/chrony/chrony.drift
local stratum 10
allow 192.0.2.0/24
```

随后按上一节启用／重启并检查服务。`local stratum 10` 会使客户端在服务器没有真实上游时也接受它，**不代表该时间准确或可追溯 UTC**；不要用它掩盖本应有上游却失锁的问题。服务器断电／漂移同样影响所有客户端，应有电池、持续供电或重新校时安排。官方说明：[chrony 访问许可](https://chrony-project.org/doc/4.6/chrony.conf.html#allow)、[隔离网络 local 模式](https://chrony-project.org/doc/4.6/chrony.conf.html#local)。

## 暂时停止或恢复授时

如需暂时停止自动授时，先退出时间戳敏感任务，以 `root` 执行：

```bash
/etc/init.d/S49ntp stop
```

停止不清空当前系统时间，但系统会自由漂移；这只停止当前服务，不取消下次开机自动启动。恢复时执行：

```bash
/etc/init.d/S49ntp start
```

恢复后重新检查同步，再开始采集。完全无网络时 NTP 无法工作；若改用其他授时方式，应确认只有一个服务校准系统时钟。单独 PPS 不提供日期，本页 PTP master 也不会反向校准系统。无电池且无外部可信源时，不能自动恢复断电期间的真实 UTC。

## 检查同步状态

在板端执行：

```bash
cat /etc/ntp.conf
cat /etc/default/ntpd
pidof ntpd
date -u
ntpq -pn
ntpq -c rv
```

确认选中了预期服务器（`*`）、系统不再处于未同步状态，并持续观察 offset、jitter、reach；具体精度需按应用目标独立测量。开机未联网、断网或重新联网后均应重新检查；没有可用时间源时，不把日期显示或进程存在当作 UTC 已就绪。

## 手动恢复校时

自动授时正常时无需运行此脚本。以下仅描述 `x5_sync_time.sh` 的手动恢复用法；它会即时改时钟，并处理 resolver／时区／RTC 和服务切换。不要把它循环挂到开机任务。

### 前提条件

- 板卡能访问目标 NTP server；同网段数字 IP 不要求互联网或 DNS，跨网段需路由；
- UDP `123` 可达；
- 以 `root` 执行；
- 先用 `Ctrl+C` 退出前台 demo、ROS2 节点或其他时间戳敏感任务；
- 保持 `cam-service` 运行；
- 脚本会检查所需依赖，缺依赖时按错误输出处理。

### 获取脚本

脚本位于公开 non-ROS Demo 仓库：

```text
scripts/env_setup/x5_sync_time.sh
```

开发机上传：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
scp scripts/env_setup/x5_sync_time.sh root@${X5_IP}:/root/x5_sync_time.sh
```

### 板端执行

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh root@${X5_IP}
chmod +x /root/x5_sync_time.sh
/root/x5_sync_time.sh
```

### 默认行为

| 项目 | 默认值 |
|---|---|
| 主 NTP server | `0.pool.ntp.org` |
| 备用 NTP server | `202.118.1.81` |
| 运行时 DNS | `223.5.5.5, 223.6.6.6`，默认写到 `/tmp/resolv.conf` |
| `ntpq` 选星验证超时 | `90 s` |
| 时区 | `Asia/Shanghai` |
| RTC | 若存在 `hwclock`，写入并按 UTC 复核；可用 `--no-rtc` 关闭 |
| 服务行为 | 保持 `cam-service`；停止 `phc2sys` 和当前 `ntpd`；除非显式使用 `--stop-ptp4l`，否则不停止 `ptp4l` |

脚本先用主 server 执行一次 `ntpdate -u -b`，失败后尝试备用 server；之后启动板端现有配置对应的 `ntpd`，等待 `ntpq -pn` 出现已选中的 `*` peer。`--server` 和 `--fallback-server` 只选择本次 `ntpdate` 的一次性校时源，不会改写 `ntpd` 的持续运行配置；`ntpq` 选中的 peer 以板端现有 `ntpd` 配置为准。

### 验证

```bash
date
date -u
ntpq -pn
command -v hwclock >/dev/null 2>&1 && hwclock -r -u
```

`date` 和 `date -u` 应反映新的系统时间；`ntpq -pn` 应出现被选中的 `*` peer。`*` 只证明 `ntpd` 选中了一个 peer，不是同步精度、offset 或 jitter 的保证。`hwclock` 只在系统存在该工具时执行。

### 自定义 server

```bash
NTP_SERVER=0.pool.ntp.org  # 改成实际主 NTP server
NTP_FALLBACK_SERVER=202.118.1.81  # 改成实际备用 NTP server
/root/x5_sync_time.sh \
  --server ${NTP_SERVER} \
  --fallback-server ${NTP_FALLBACK_SERVER}
```

以上两个 server 参数只用于一次性的 `ntpdate`。固定持续 peer 应按“更换 NTP 服务器”编辑 `/etc/ntp.conf`。隔离环境下两个一次性参数都应指向实际内部源，避免默认备用源访问公网。手动脚本仍会处理运行时 DNS，必要时用 `--dns` 与 `--resolv-file` 指向现场允许的 resolver；数字 IP 校时不依赖 DNS，但不代表手动脚本完全不改 resolver。`--ntpq-timeout` 修改等待时间，`--no-rtc` 跳过 RTC 写入；无电池时写 RTC 不提供断电保持。完整参数：

```bash
/root/x5_sync_time.sh --help
```

`--allow-unverified` 只表示在 `ntpq` 不可用时，允许一次已成功的单次同步返回 `0`；它不证明持续 `ntpd` peer lock。`--stop-ptp4l` 只用于明确选择停止 PTP 的场景，不建议默认使用。

### 返回码

| 码值 | 含义 |
|---:|---|
| `0` | 单次同步成功并验证到 `ntpq` 选星；或显式使用 `--allow-unverified` 时，单次同步成功但 `ntpq` 不可用 |
| `1` | 依赖、服务、网络、NTP 或 RTC 操作失败 |
| `2` | 单次同步已成功，但 `ntpq` 不可用，持续守护验证未完成；此前的系统时间、RTC、时区、resolver 和服务变更可能已经生效 |
| `3` | `ntpq` 可用，但在超时内没有出现已选中的 `*` peer；此前的系统时间、RTC、时区、resolver 和服务变更可能已经生效 |

### 排障

| 现象 | 先检查 | 处理 |
|---|---|---|
| 网络、DNS 或 UDP 123 不通 | 网关、路由、解析和 NTP server 可达性 | 恢复网络后重试 |
| 缺少 `ntpdate` 或 init 脚本 | 脚本依赖检查输出 | 补齐目标系统所需运行环境 |
| 返回码 `2` | `ntpq` 是否存在 | 只完成一次同步；不要当作持续锁定 |
| 返回码 `3` | `ntpq -pn` | 检查 server、网络和超时设置 |
| 执行时系统时间跳变 | 是否仍有采集/ROS2 任务运行 | 停止时间敏感任务，NTP 完成后重新启动 |

脚本只在一次性校时完成前的失败路径尝试恢复先前服务。一次性校时完成后进入持续守护验证阶段时，系统时间 step、RTC/时区/resolver 修改以及服务切换可能已经生效；因此返回码 `2` 或 `3` 不表示已恢复到执行前状态。成功或进入上述验证失败状态后，`phc2sys` 均可能保持停止；如需继续 PTP master，按[PTP 同步](ptp-sync.md)重新确认并启动 PHC/PTP 链路。
