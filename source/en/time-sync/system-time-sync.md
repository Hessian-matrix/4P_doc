# Time Synchronization

This chapter uniformly explains the current public time-related configuration methods for RoboBaton 4P. Different methods solve different problems: system clock calibration, external PPS edge input, and external device PTP sync must not be conflated into a single "sync".

## Current Method Overview

| Method | Main purpose | Current public entry | Key boundary |
|---|---|---|---|
| NTP | Calibrate X5 `CLOCK_REALTIME` from public or private LAN servers with automatic boot-time `ntpd`; change servers on the board or use manual recovery | [NTP Sync](ntp-sync.md) | Network path and UDP 123 required; DNS only for hostnames, Internet not mandatory; initial correction may step time |
| PPS | Bring edges through the independent IO on the UART7 5-pin connector into Linux PPS, enabled by default | [PPS Sync](pps-sync.md) | Does not automatically discipline the system clock |
| PTP | Use the X5 as a LinuxPTP master, serving time from the X5 system clock via PHC to external PTP slaves | [PTP Sync](ptp-sync.md) | The current page uses X5 master + Livox Mid-360 slave as the example |

## How to Choose

- X5 can reach a public or private LAN NTP server and needs its system time calibrated: use **NTP**. A private server without a trusted upstream only aligns device clocks, not certified UTC; NTP cannot operate without networking.
- An external device provides a physical PPS signal and the goal is for Linux to capture that edge: use **PPS**.
- An external LiDAR or similar device needs the X5 to provide an IEEE 1588v2 PTP master: use **PTP**.

## Common Safety Boundaries

1. The time direction of the current PTP example is `CLOCK_REALTIME -> phc2sys -> eth0 PHC -> ptp4l master -> PTP slave`; PTP does not calibrate the X5 `CLOCK_REALTIME` in reverse.
2. NTP can be upstream of X5 `CLOCK_REALTIME` and must not compete with reverse PHC discipline or another system-clock owner. The manual recovery script stops `phc2sys`. To serve PTP master afterward, separately confirm the system-to-PHC direction and start/verify the PHC/PTP chain. Do not restore an owner that writes system time in reverse or run the scripts together without checking.
3. The PPS page covers Linux PPS input only; identify the enumerated node rather than assume `/dev/pps2`. Without a PPS consumer/clock-discipline configuration, PPS does not calibrate `CLOCK_REALTIME`.
4. Before running NTP/PTP configuration, exit demos, ROS2 nodes, and other timestamp-sensitive tasks first; keep `cam-service` running.
5. Before wiring PPS, confirm the 5-pin order, voltage, and common ground, and wire with power off.
6. System time sync is not the same as sampling sync. Camera, IMU, PPS, PTP, and ROS `header.stamp` are different layers; field semantics are in [Data Contracts](../development/data-contracts.md).
7. Camera, IMU, and bag record times use `CLOCK_REALTIME` system time. Hardware capture/sample times pass through internal RAW mappings and continuously refreshed realtime bridges, not a frozen startup offset. System corrections affect subsequent stamps, including backward steps; internal timeouts stay monotonic. Synchronize the clock before acquisition to avoid encoder/container limitations on backward timestamps. A common domain does not establish FSYNC sample/exposure synchronization, and an uncalibrated system clock is not accurate UTC.
8. IMU `host_timestamp_ns` (producer CLI `fifo_observation_ns`) retains the successful SPI FIFO burst-completion RAW observation converted to realtime using that observation's bridge. Packets may share it; FSYNC-deferred publication never rebridges historical RAW. It is not IRQ, sample, or exposure time, and increasing realtime does not define packet order or identity.
9. These field semantics do not prove persistent RTC, automatic synchronization after power-off/reboot, or absolute UTC accuracy, nor close current LPWM/FSYNC load and long-tail limits. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

## Three Sync Methods

```{toctree}
:maxdepth: 1

ntp-sync
pps-sync
ptp-sync
```
