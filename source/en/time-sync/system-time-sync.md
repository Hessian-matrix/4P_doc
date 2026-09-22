# Time Synchronization

This chapter uniformly explains the current public time-related configuration methods for RoboBaton 4P. Different methods solve different problems: system clock calibration, external PPS edge input, and external device PTP sync must not be conflated into a single "sync".

## Current Method Overview

| Method | Main purpose | Current public entry | Key boundary |
|---|---|---|---|
| NTP | Calibrate the X5 `CLOCK_REALTIME` through network servers and run `ntpd` | [NTP Sync](ntp-sync.md) | Requires network, DNS/routing, and UDP 123; a system time step may occur during execution |
| PPS | Bring an external PPS edge into Linux `/dev/pps2` through the default UART7 RX | [PPS Sync](pps-sync.md) | Only establishes the Linux PPS input event source; does not automatically discipline the system clock |
| PTP | Use the X5 as a LinuxPTP master, serving time from the X5 system clock via PHC to external PTP slaves | [PTP Sync](ptp-sync.md) | The current page uses X5 master + Livox Mid-360 slave as the example |

## How to Choose

- The X5 can reach an NTP server and the goal is to bring the system time close to network time: use **NTP**.
- An external device provides a physical PPS signal and the goal is for Linux to capture that edge: use **PPS**.
- An external LiDAR or similar device needs the X5 to provide an IEEE 1588v2 PTP master: use **PTP**.

## Common Safety Boundaries

1. The time direction of the current PTP example is `CLOCK_REALTIME -> phc2sys -> eth0 PHC -> ptp4l master -> PTP slave`; PTP does not calibrate the X5 `CLOCK_REALTIME` in reverse.
2. NTP can be an upstream time source for the X5 `CLOCK_REALTIME`, but the current NTP script stops `phc2sys`. After running NTP, if you need to continue providing a PTP master from the X5, you must re-confirm and start `phc2sys`, then re-verify the PTP master and slave state; do not run the two scripts in parallel without checking.
3. The PPS page only covers bringing an external edge into `/dev/pps2`; without an additional PPS consumer/clock-discipline configuration, PPS does not automatically calibrate `CLOCK_REALTIME`.
4. Before running NTP/PTP configuration, exit demos, ROS2 nodes, and other timestamp-sensitive tasks first; keep `cam-service` running.
5. Before switching UART7 RX to PPS, stop programs using UART7 and prepare an SSH or other recovery entry.
6. System time sync is not the same as sampling sync. Camera, IMU, PPS, PTP, and ROS `header.stamp` are different layers; field semantics are in [Data Contracts](../development/data-contracts.md).
7. The current demo freezes the `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset at process startup; changing the system time after process startup does not automatically update the already-frozen mapping. To calibrate the system time, calibrate first, then start the acquisition program.

## Three Sync Methods

```{toctree}
:maxdepth: 1

ntp-sync
pps-sync
ptp-sync
```
