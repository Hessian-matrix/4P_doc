# NTP Sync

This page explains how to calibrate the X5 system time via NTP. This method applies to scenarios where the board can reach the target NTP server; it is recommended to run it before starting demos, ROS2 nodes, or any timestamp-sensitive acquisition.

The script on this page calibrates the system `CLOCK_REALTIME` via NTP. The current PTP master example instead syncs `CLOCK_REALTIME` to the `eth0` PHC through `phc2sys`, then serves it to external slaves through `ptp4l`. The two can be layered architecturally, but the current NTP script stops `phc2sys`; after running NTP, if you need to continue providing a PTP master, you must re-establish and verify the PHC/PTP link. PPS is a separate edge-input mechanism and does not automatically replace NTP. For the three methods see [Time Synchronization](system-time-sync.md).

## Prerequisites

- The board network and gateway are available and can reach the target NTP server;
- UDP `123` is reachable;
- Run as `root`;
- Exit foreground demos, ROS2 nodes, or other timestamp-sensitive tasks first with `Ctrl+C`;
- Keep `cam-service` running;
- The script checks required dependencies and handles missing dependencies per its error output.

## Get the Script

The script is in the public non-ROS demo repository:

```text
scripts/env_setup/x5_sync_time.sh
```

Upload from the host:

```bash
X5_IP=192.168.1.12  # change to the actual board address
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
scp scripts/env_setup/x5_sync_time.sh root@${X5_IP}:/root/x5_sync_time.sh
```

## Run On-Device

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh root@${X5_IP}
chmod +x /root/x5_sync_time.sh
/root/x5_sync_time.sh
```

## Default Behavior

| Item | Default |
|---|---|
| Primary NTP server | `0.pool.ntp.org` |
| Fallback NTP server | `202.118.1.81` |
| Runtime DNS | `223.5.5.5, 223.6.6.6`, written to `/tmp/resolv.conf` by default |
| `ntpq` peer-selection verification timeout | `90 s` |
| Timezone | `Asia/Shanghai` |
| RTC | If `hwclock` exists, write and re-verify in UTC; can disable with `--no-rtc` |
| Service behavior | Keep `cam-service`; stop `phc2sys` and the current `ntpd`; do not stop `ptp4l` unless `--stop-ptp4l` is explicitly used |

The script first runs one `ntpdate -u -b` against the primary server, then falls back to the fallback server on failure; after that it starts the `ntpd` matching the board's existing configuration and waits for `ntpq -pn` to show a selected `*` peer. `--server` and `--fallback-server` only select the one-shot `ntpdate` calibration source and do not rewrite the persistent `ntpd` configuration; the peer selected by `ntpq` is governed by the board's existing `ntpd` configuration.

## Verify

```bash
date
date -u
ntpq -pn
command -v hwclock >/dev/null 2>&1 && hwclock -r -u
```

`date` and `date -u` should reflect the new system time; `ntpq -pn` should show a selected `*` peer. The `*` only proves that `ntpd` selected a peer, not a guarantee of sync accuracy, offset, or jitter. `hwclock` runs only when the tool exists on the system.

## Custom Server

```bash
NTP_SERVER=0.pool.ntp.org  # change to the actual primary NTP server
NTP_FALLBACK_SERVER=202.118.1.81  # change to the actual fallback NTP server
/root/x5_sync_time.sh \
  --server ${NTP_SERVER} \
  --fallback-server ${NTP_FALLBACK_SERVER}
```

The two server parameters above are only used for the one-shot `ntpdate`. The persistently running `ntpd` still reads the board's existing configuration; to fix persistent peers, confirm and modify the target system's NTP configuration per its own flow rather than relying only on these two parameters. `--dns` changes the runtime DNS, `--ntpq-timeout` changes the wait time, and `--no-rtc` skips the RTC write. Full parameters:

```bash
/root/x5_sync_time.sh --help
```

`--allow-unverified` only means that when `ntpq` is unavailable, a successful one-shot sync may return `0`; it does not prove a persistent `ntpd` peer lock. `--stop-ptp4l` is only for scenarios where stopping PTP is explicitly chosen and is not recommended by default.

## Return Codes

| Code | Meaning |
|---:|---|
| `0` | One-shot sync succeeded and `ntpq` peer selection was verified; or with explicit `--allow-unverified`, one-shot sync succeeded but `ntpq` was unavailable |
| `1` | Dependency, service, network, NTP, or RTC operation failed |
| `2` | One-shot sync succeeded but `ntpq` was unavailable and the persistent daemon verification did not complete; earlier system time, RTC, timezone, resolver, and service changes may already have taken effect |
| `3` | `ntpq` is available but no selected `*` peer appeared within the timeout; earlier system time, RTC, timezone, resolver, and service changes may already have taken effect |

## Troubleshooting

| Symptom | First check | Handling |
|---|---|---|
| Network, DNS, or UDP 123 unreachable | Gateway, route, resolution, and NTP server reachability | Retry after restoring the network |
| Missing `ntpdate` or init script | Script dependency-check output | Provide the runtime environment required by the target system |
| Return code `2` | Whether `ntpq` exists | Only a one-shot sync completed; do not treat it as a persistent lock |
| Return code `3` | `ntpq -pn` | Check server, network, and timeout settings |
| System time steps during execution | Whether acquisition/ROS2 tasks are still running | Stop timestamp-sensitive tasks, restart them after NTP completes |

The script only tries to restore prior services on the failure path before the one-shot calibration completes. Once the one-shot calibration completes and enters the persistent daemon verification phase, the system time step, RTC/timezone/resolver changes, and service switch may already have taken effect; therefore return codes `2` or `3` do not mean the pre-execution state was restored. After success or entering the above verification-failure state, `phc2sys` may remain stopped; to continue PTP master, re-confirm and start the PHC/PTP link per [PTP Sync](ptp-sync.md).
