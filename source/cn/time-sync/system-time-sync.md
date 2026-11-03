# 时间同步

本章统一说明 RoboBaton 4P 当前公开的时间相关配置方法。不同方法解决的问题不同：系统时钟校准、外部 PPS 边沿接入和外部设备 PTP 同步不能混为同一个“同步”。

## 当前方法总览

| 方法 | 主要目的 | 当前公开入口 | 关键边界 |
|---|---|---|---|
| NTP | 通过公网或自建局域网服务器校准 X5 `CLOCK_REALTIME`，使用 `ntpd` 开机自动授时；支持板端更换服务器与手动恢复 | [NTP 同步](ntp-sync.md) | 需要到时间源的网络和 UDP 123；域名源才需要 DNS，不强制互联网；首次校正可能跳变 |
| PPS | 经 UART7 5pin 接口的独立 IO 接入 Linux PPS，系统默认启用 | [PPS 同步](pps-sync.md) | 不自动纪律系统时钟 |
| PTP | 让 X5 作为 LinuxPTP master，由 X5 系统时间经 PHC 为外部 PTP slave 提供时间 | [PTP 同步](ptp-sync.md) | 当前页面以 X5 master + Livox Mid-360 slave 为示例 |

## 如何选择

- X5 能访问公网或自建局域网 NTP server，目标是校准系统时间：使用 **NTP**。自建服务器无可信上游时只能统一设备时钟，不能认证 UTC；完全无网络时 NTP 不适用。
- 外部设备提供物理 PPS 信号，目标是让 Linux 捕获该边沿：使用 **PPS**。
- 外部 LiDAR 等设备需要 X5 提供 IEEE 1588v2 PTP master：使用 **PTP**。

## 共通安全边界

1. 当前 PTP 示例的时间方向是 `CLOCK_REALTIME -> phc2sys -> eth0 PHC -> ptp4l master -> PTP slave`；PTP 不会反向校准 X5 的 `CLOCK_REALTIME`。
2. NTP 可以作为 X5 `CLOCK_REALTIME` 的上游时间源，不应与反向 PHC 授时等其他系统时钟 owner 竞争。手动恢复脚本会停止 `phc2sys`。之后如需由 X5 提供 PTP master，必须另行确认系统→PHC方向、启动并验证 PHC/PTP 链路，不直接恢复反向写系统时间的 owner；不要把两个脚本未经检查地并行运行。
3. PPS 页面只负责外部边沿进入 Linux PPS；节点按系统枚举识别，不固定 `/dev/pps2`。没有额外 PPS consumer/clock discipline 时，不自动校准 `CLOCK_REALTIME`。
4. 执行 NTP/PTP 配置前，应先退出 demo、ROS2 节点和其他时间戳敏感任务；保持 `cam-service` 运行。
5. PPS 接线前确认 5pin 线序、电平和共地，断电操作。
6. 系统时间同步不等于采样同步。相机、IMU、PPS、PTP 和 ROS `header.stamp` 属于不同层次，字段语义见[数据合同](../development/data-contracts.md)。
7. 相机、IMU 和 bag record time 均输出 `CLOCK_REALTIME` 系统时间；硬件触发/采样时间经内部 RAW 映射并持续刷新 realtime 桥接，不冻结启动 offset。系统校时会改变后续时间戳，允许回拨；内部超时仍使用单调时钟。先校时再采集，避免编码/容器遇到不支持的时间回退。统一时间域不代表 FSYNC 样本或曝光已同步；系统时间未校准时也不代表准确 UTC。
8. IMU `host_timestamp_ns`（producer CLI `fifo_observation_ns`）保留成功 SPI FIFO burst 完成时 RAW 观测按当次桥接转换的 realtime；同 burst 可共享，FSYNC 延迟发布不重新桥接旧 RAW。它不是 IRQ、样本或曝光时间；包序和身份不由 realtime 递增定义。
9. 上述字段语义不证明持久 RTC、断电/重启后自动校时或绝对 UTC 精度，也不关闭当前 LPWM/FSYNC 的负载与长尾限制；见{ref}`能力与验证边界 <capability-verification-boundary>`。

## 三种同步方式

```{toctree}
:maxdepth: 1

ntp-sync
pps-sync
ptp-sync
```
