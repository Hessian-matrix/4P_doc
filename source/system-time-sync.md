# 系统时间同步

本页说明 X5 的系统时间同步。默认方法是 NTP，只适合板卡已经能访问网络或 Internet 的场景；建议在启动 demo、ROS2 节点或任何时间戳敏感采集前先执行。时间戳域和同步边界见 [数据合同](data-contracts.md)。

## 前提条件

- 板卡网络和网关可用，能访问目标 NTP 服务器。
- UDP `123` 可达。
- 以 `root` 执行。
- 先用 `Ctrl+C` 退出前台 demo、ROS2 节点或其他时间戳敏感任务。
- 保持 `cam-service` 运行，不要把它当作常规停止对象。
- 脚本会自行检查所需依赖；缺依赖时直接按脚本输出处理。

## 获取脚本

如果开发机已经有 `RoboBaton_4p_demo` 仓库，可以直接从 `cd` 和 `scp` 开始。

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
scp scripts/env_setup/x5_sync_time.sh root@<x5-ip>:/root/x5_sync_time.sh
```

## 板端执行

```bash
ssh root@<x5-ip>
chmod +x /root/x5_sync_time.sh
/root/x5_sync_time.sh
```

## 默认行为

| 项目 | 默认值 |
|---|---|
| 主 NTP 服务器 | `0.pool.ntp.org` |
| 备用 NTP 服务器 | `202.118.1.81` |
| 运行时 DNS | `223.5.5.5, 223.6.6.6`，默认写到 `/tmp/resolv.conf` |
| `ntpq` 选星验证超时 | `90 s` |
| 时区 | `Asia/Shanghai` |
| RTC | 若存在 `hwclock`，写入并按 UTC 复核；可用 `--no-rtc` 关闭 |
| 服务行为 | `cam-service` 保持运行；脚本会停掉 `phc2sys` 和当前 `ntpd`，除非显式指定 `--stop-ptp4l`，否则不停止 `ptp4l` |

脚本会先用主服务器做一次 `ntpdate -u -b`，失败后再尝试备份服务器；之后启动 `ntpd` 并等待 `ntpq -pn` 看到已选中的 `*` peer。

## 验证

同步完成后检查：

```bash
date
date -u
ntpq -pn
command -v hwclock >/dev/null 2>&1 && hwclock -r -u
```

`date` 和 `date -u` 应该反映新的系统时间；`ntpq -pn` 里应出现被选中的 `*` peer。`hwclock` 命令只在系统存在该工具时执行。

## 自定义服务器

```bash
/root/x5_sync_time.sh \
  --server <ntp-host-or-ip> \
  --fallback-server <ntp-fallback-ip>
```

`--dns` 可改运行时解析服务器，`--ntpq-timeout` 可改 `ntpq` 选星等待时间，`--no-rtc` 可跳过 RTC 写入。完整参数见 `--help`。

```bash
/root/x5_sync_time.sh --help
```

`--allow-unverified` 只是在 `ntpq` 不可用时，允许一次已成功的单次同步返回 `0`；它不等同于持续同步已被验证。`--stop-ptp4l` 只用于你明确选择停止 PTP 守护进程的场景，不建议默认使用。

## 返回码

| 码值 | 含义 |
|---|---|
| `0` | 单次同步成功，且已验证到 `ntpq` 选星；或者显式允许 `--allow-unverified` 时，`ntpq` 不可用但单次同步已成功 |
| `1` | 依赖、服务、网络、NTP 或 RTC 相关操作失败 |
| `2` | 单次同步成功，但 `ntpq` 不可用，持续守护验证未完成 |
| `3` | `ntpq` 可用，但在超时时间内没有出现已选中的 `*` peer |

## 排障

| 现象 | 先看什么 | 处理建议 |
|---|---|---|
| 网络、DNS 或 UDP `123` 不通 | 网关、路由、解析和到 NTP 服务器的连通性 | 先恢复板卡外网/内网连通，再重跑脚本 |
| 提示缺少 `ntpdate` 或 init 脚本 | 脚本依赖检查输出 | 补齐脚本要求的运行环境后重试 |
| 返回码 `2` | `ntpq` 是否存在 | 这是只完成了一次同步但无法验证持续守护的结果；如果只接受单次同步，用户可以显式加 `--allow-unverified` 重新运行，但这仍不证明持续 `ntpd` peer lock |
| 返回码 `3` | `ntpq -pn` 输出 | 说明守护进程还没有选中 peer；检查网络、服务器可达性和超时设置后重试 |
| 执行过程中系统时间跳变 | 当前是否仍有前台采集、ROS2 节点或其他时间敏感任务 | 这是预期行为；先停掉前台任务再执行，执行后重新启动相关任务 |

失败时脚本会尽量恢复之前的服务状态；成功后会让 NTP 继续作为时间来源，并保持 `ntpd` 运行。
