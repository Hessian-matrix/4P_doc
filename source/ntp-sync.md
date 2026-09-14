# NTP 同步

本页说明如何通过 NTP 校准 X5 系统时间。该方法适用于板卡能够访问目标 NTP server 的场景；建议在启动 demo、ROS2 节点或任何时间戳敏感采集前执行。

本页脚本用 NTP 校准系统的 `CLOCK_REALTIME`。当前 PTP master 示例则把 `CLOCK_REALTIME` 经 `phc2sys` 同步到 `eth0` PHC，再由 `ptp4l` 提供给外部 slave。两者在架构上可以分层，但当前 NTP 脚本会停止 `phc2sys`；执行 NTP 后如需继续提供 PTP master，必须重新建立并验证 PHC/PTP 链路。PPS 是单独的边沿输入机制，不会自动替代 NTP。三种方法见[时间同步](system-time-sync.md)。

## 前提条件

- 板卡网络和网关可用，能访问目标 NTP server；
- UDP `123` 可达；
- 以 `root` 执行；
- 先用 `Ctrl+C` 退出前台 demo、ROS2 节点或其他时间戳敏感任务；
- 保持 `cam-service` 运行；
- 脚本会检查所需依赖，缺依赖时按错误输出处理。

## 获取脚本

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

## 板端执行

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh root@${X5_IP}
chmod +x /root/x5_sync_time.sh
/root/x5_sync_time.sh
```

## 默认行为

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

## 验证

```bash
date
date -u
ntpq -pn
command -v hwclock >/dev/null 2>&1 && hwclock -r -u
```

`date` 和 `date -u` 应反映新的系统时间；`ntpq -pn` 应出现被选中的 `*` peer。`*` 只证明 `ntpd` 选中了一个 peer，不是同步精度、offset 或 jitter 的保证。`hwclock` 只在系统存在该工具时执行。

## 自定义 server

```bash
NTP_SERVER=0.pool.ntp.org  # 改成实际主 NTP server
NTP_FALLBACK_SERVER=202.118.1.81  # 改成实际备用 NTP server
/root/x5_sync_time.sh \
  --server ${NTP_SERVER} \
  --fallback-server ${NTP_FALLBACK_SERVER}
```

以上两个 server 参数只用于一次性的 `ntpdate`。持续运行的 `ntpd` 仍读取板端已有配置；需要固定持续 peer 时，应先按目标系统的 NTP 配置流程确认并修改其配置，而不是仅依赖这两个参数。`--dns` 可修改运行时 DNS，`--ntpq-timeout` 可修改等待时间，`--no-rtc` 可跳过 RTC 写入。完整参数：

```bash
/root/x5_sync_time.sh --help
```

`--allow-unverified` 只表示在 `ntpq` 不可用时，允许一次已成功的单次同步返回 `0`；它不证明持续 `ntpd` peer lock。`--stop-ptp4l` 只用于明确选择停止 PTP 的场景，不建议默认使用。

## 返回码

| 码值 | 含义 |
|---:|---|
| `0` | 单次同步成功并验证到 `ntpq` 选星；或显式使用 `--allow-unverified` 时，单次同步成功但 `ntpq` 不可用 |
| `1` | 依赖、服务、网络、NTP 或 RTC 操作失败 |
| `2` | 单次同步已成功，但 `ntpq` 不可用，持续守护验证未完成；此前的系统时间、RTC、时区、resolver 和服务变更可能已经生效 |
| `3` | `ntpq` 可用，但在超时内没有出现已选中的 `*` peer；此前的系统时间、RTC、时区、resolver 和服务变更可能已经生效 |

## 排障

| 现象 | 先检查 | 处理 |
|---|---|---|
| 网络、DNS 或 UDP 123 不通 | 网关、路由、解析和 NTP server 可达性 | 恢复网络后重试 |
| 缺少 `ntpdate` 或 init 脚本 | 脚本依赖检查输出 | 补齐目标系统所需运行环境 |
| 返回码 `2` | `ntpq` 是否存在 | 只完成一次同步；不要当作持续锁定 |
| 返回码 `3` | `ntpq -pn` | 检查 server、网络和超时设置 |
| 执行时系统时间跳变 | 是否仍有采集/ROS2 任务运行 | 停止时间敏感任务，NTP 完成后重新启动 |

脚本只在一次性校时完成前的失败路径尝试恢复先前服务。一次性校时完成后进入持续守护验证阶段时，系统时间 step、RTC/时区/resolver 修改以及服务切换可能已经生效；因此返回码 `2` 或 `3` 不表示已恢复到执行前状态。成功或进入上述验证失败状态后，`phc2sys` 均可能保持停止；如需继续 PTP master，按[PTP 同步](ptp-sync.md)重新确认并启动 PHC/PTP 链路。
