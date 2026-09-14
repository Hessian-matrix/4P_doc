# 时间同步

本章统一说明 RoboBaton 4P 当前公开的时间相关配置方法。不同方法解决的问题不同：系统时钟校准、外部 PPS 边沿接入和外部设备 PTP 同步不能混为同一个“同步”。

## 当前方法总览

| 方法 | 主要目的 | 当前公开入口 | 关键边界 |
|---|---|---|---|
| NTP | 通过网络服务器校准 X5 `CLOCK_REALTIME`，并运行 `ntpd` | [NTP 同步](ntp-sync.md) | 需要网络、DNS/路由和 UDP 123；执行时可能发生系统时间跳变 |
| PPS | 把外部 PPS 边沿通过默认 UART7 RX 接入 Linux `/dev/pps2` | [PPS 同步](pps-sync.md) | 只建立 Linux PPS 输入事件源，不自动纪律系统时钟 |
| PTP | 让 X5 作为 LinuxPTP master，由 X5 系统时间经 PHC 为外部 PTP slave 提供时间 | [PTP 同步](ptp-sync.md) | 当前页面以 X5 master + Livox Mid-360 slave 为示例 |

## 如何选择

- X5 能访问 NTP server，目标是让系统时间接近网络时间：使用 **NTP**。
- 外部设备提供物理 PPS 信号，目标是让 Linux 捕获该边沿：使用 **PPS**。
- 外部 LiDAR 等设备需要 X5 提供 IEEE 1588v2 PTP master：使用 **PTP**。

## 共通安全边界

1. 当前 PTP 示例的时间方向是 `CLOCK_REALTIME -> phc2sys -> eth0 PHC -> ptp4l master -> PTP slave`；PTP 不会反向校准 X5 的 `CLOCK_REALTIME`。
2. NTP 可以作为 X5 `CLOCK_REALTIME` 的上游时间源，但当前 NTP 脚本会停止 `phc2sys`。执行 NTP 后，如需继续由 X5 提供 PTP master，必须重新确认并启动 `phc2sys`，再复核 PTP master 和从设备状态；不要把两个脚本未经检查地并行运行。
3. PPS 页面只负责外部边沿进入 `/dev/pps2`；没有额外的 PPS consumer/clock discipline 配置时，PPS 不会自动校准 `CLOCK_REALTIME`。
4. 执行 NTP/PTP 配置前，应先退出 demo、ROS2 节点和其他时间戳敏感任务；保持 `cam-service` 运行。
5. UART7 RX 切换 PPS 前，应停止使用 UART7 的程序，并准备 SSH 或其他恢复入口。
6. 系统时间同步不等于采样同步。相机、IMU、PPS、PTP 和 ROS `header.stamp` 属于不同层次，字段语义见[数据合同](data-contracts.md)。
7. 当前 demo 在进程启动时冻结 `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset；进程启动后再改变系统时间不会自动更新已经冻结的映射。需要校准系统时间时，应先校准，再启动采集程序。

## 三种同步方式

```{toctree}
:maxdepth: 1

ntp-sync
pps-sync
ptp-sync
```
