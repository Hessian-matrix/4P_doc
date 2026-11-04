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
7. Startup camera `observer|official` and IMU `host|tmst` selectors are independent, default observer/host; all four pairs use the same binary and IIO capture/owner, changing only timestamp axes. Stop/restart to change. Observer retains `500µs` SIF admission; official uses same-frame RAW IRQ `timestamps − (tv − trig_tv) × 1000` (AON `tv`/`trig_tv` in µs), never starts the observer, and has validity0/uncertainty `UINT32_MAX` (unknown physical bound). See [non-ROS Usage](../usage/non-ros-demo.md) and [ROS2 Usage](../usage/ros2-demo.md).
8. Both IMU modes retain `sample_monotonic_ns` and `observation_monotonic_ns` as kernel MONOTONIC host evidence; `burst_complete_raw_ns` is independent RAW and must not be directly subtracted. Host sample RAW is zero/uncertainty unknown. TMST unwraps kernel-owned FIFO/UI transition evidence into bounded affine RAW `sample_raw_ns`; its `200µs` computational admission is not physical precision. Saving/ROS2 bridge host MONOTONIC→REALTIME or tmst RAW→REALTIME per burst, retaining separate `bridge_monotonic_ns`/`bridge_raw_ns` and the bridge bracket half-width. Bag record time independently reads realtime; wall-clock steps remain visible without frozen offsets or fabricated monotonic time. Synchronize before acquisition. Neither mode restores FSYNC, spidev, or fallback; both require matched kernel IIO V3 (V2 incompatible).
9. These semantics do not certify persistent RTC, automatic synchronization after reboot, absolute UTC, or physical synchronization. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

## Three Sync Methods

```{toctree}
:maxdepth: 1

ntp-sync
pps-sync
ptp-sync
```
