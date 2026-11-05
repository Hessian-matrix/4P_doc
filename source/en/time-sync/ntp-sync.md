# NTP Sync

NTP calibrates the X5 `CLOCK_REALTIME`. Choose persistent boot-time discipline or the manual recovery script; these are separate entry points. Without an RTC battery, UTC does not survive power loss. Saving configuration does not save the current time.

NTP does not require Internet access, but the board must reach a time server over a network. Public sources, private LAN sources, and completely disconnected operation have different limits below. PPS supplies edges, not a date or automatic system-clock discipline. The PTP master still serves system time outward through PHC; see [Time Synchronization](system-time-sync.md).

## Choose a Time Source

| Mode | Board requirements | Time trust |
|---|---|---|
| Public NTP | Route to configured sources, name resolution, and UDP `123` | Depends on upstream and network; default public sources are unauthenticated, without a precision guarantee |
| Private LAN NTP | Network path and UDP `123` to a specified server; numeric IP needs no DNS, and a same-subnet server needs no Internet gateway | Depends on the server; a trusted upstream or GNSS reference can supply UTC |
| Isolated LAN using a local clock | One designated time server and a LAN | Aligns device clocks only; without a trusted reference it is not accurate UTC |
| No network or external source | Manual setting or a separately integrated time reference | Without a battery, time must be supplied again after each power loss; saved configuration cannot recover true UTC |

## Automatic Boot-Time Synchronization

This section applies to systems that provide boot-time NTP. For normal use, connect a network that can reach the time servers. There is no per-board configuration-script installation or manual calibration command to run at each boot.

- `ntpd` starts at boot and continuously disciplines system time using the servers in `/etc/ntp.conf`. Defaults are `0.pool.ntp.org` through `3.pool.ntp.org`, not discovery of arbitrary LAN servers.
- Hostname sources need working DNS. All sources need a network route and reachable UDP `123`; numeric IP addresses need no DNS. A same-subnet private source needs no Internet access.
- The system remains usable when booting without networking. After connectivity returns, synchronization follows the daemon's polling/resolution retry schedule, not an immediate-sync guarantee.
- Without an RTC battery, UTC does not survive power loss. Recheck synchronization after every boot; without an available time source, the displayed date is not evidence of accurate UTC.
- Acquisition does not wait for synchronization, and the first correction can step system time. Before timestamp-sensitive recording, [check synchronization status](#check-synchronization-status). Do not manually calibrate time or restart discipline during acquisition.

Check the service and synchronization tool on the board:

```bash
pidof ntpd
command -v ntpq
```

A running process is not proof of synchronization. If the system lacks these tools or the boot service, contact technical support to confirm feature availability. Copying the Demo is not an NTP-enablement step.

The current flashed image starts `ntpd` at boot and provides `ntpq`. Without a usable time source, a board may still show year `2000`, no association in `ntpq -pn`, and `leap_alarm` / `sync_unspec` / `stratum=16` in `ntpq -c rv`. This means unsynchronized time, not failed sensor acquisition. Check networking, DNS, and the chosen source, or configure a trusted LAN source below. Synchronize before recording, not by manually setting time during acquisition.

## Change NTP Servers

Run the following on the board as `root`. Exit demos, ROS2 nodes, and other timestamp-sensitive tasks first; keep `cam-service` running. Do not run another service disciplining `CLOCK_REALTIME` at the same time. See [Time Synchronization](system-time-sync.md) for the PTP direction.

Back up the current configuration, then edit `/etc/ntp.conf`:

```bash
cp -p /etc/ntp.conf "/root/ntp.conf.$(date +%s).bak"
vi /etc/ntp.conf
```

Keep access restrictions, drift settings, and other configuration. Replace the existing `server`/`pool` sources with your servers. `192.0.2.10` below is a documentation address; replace it with the actual fixed reachable server address:

```text
server 192.0.2.10 iburst
```

Add multiple `server` lines for consistent trusted sources. To avoid all public access, remove every public `server`/`pool` and check that includes or dynamic source configuration do not load public sources. Adding one private source while retaining public fallback is not sufficient.

Save, restart NTP, and check synchronization:

```bash
/etc/init.d/S49ntp restart
ntpq -pn
ntpq -c rv
```

Peer selection can take time; a restart does not guarantee an immediate selected peer. Configuration is saved in `/etc/ntp.conf` for subsequent boots. If editing fails because the configuration is read-only or cannot be saved, stop and ask technical support for the supported configuration entry point. Do not force mount changes or edit startup files. Restarting NTP can step system time; resume acquisition only after synchronization.


## Provide Your Own NTP Server

Prefer a Linux host on the LAN with a stable clock and fixed address. Keep X5 as a client; it need not become a server. The following chrony example runs on a separate Ubuntu server, not as a second clock owner on X5. The host should have only one system-clock discipline service; switch services during a maintenance window. Client subnet `192.0.2.0/24` is also an example to replace. Do not expose UDP `123` to the entire Internet.

### With a Trusted Upstream or Reference Clock

Install chrony on the server, retain the actual trusted upstream or reference-clock settings in `/etc/chrony/chrony.conf`, and allow the client subnet:

```bash
sudo apt install chrony
```

```text
allow 192.0.2.0/24
```

GNSS/reference clocks require separate configuration and verification; one PPS input alone does not establish UTC. Restrict the server firewall/switch policy to requests from allowed clients to UDP `123` and return traffic, then activate the service and check its upstream and listener:

```bash
sudo systemctl enable --now chrony
sudo systemctl restart chrony
chronyc tracking
chronyc sources -v
sudo ss -lunp 'sport = :123'
```

Once the server itself is synchronized, configure X5 using “Change NTP Servers” above. A UDP listener does not prove trusted UTC.

### No Internet: Align LAN Clocks Only

Without GNSS or another trusted reference, explicitly choose chrony's local mode on a dedicated isolated server only if devices need to follow one local clock. Back up configuration, stop conflicting owners, and set the server time first. Then use this minimal `/etc/chrony/chrony.conf`; do not retain other `pool`/`server` entries or public sources loaded by includes/dynamic source configuration:

```text
driftfile /var/lib/chrony/chrony.drift
local stratum 10
allow 192.0.2.0/24
```

Enable/restart and check the service as above. `local stratum 10` makes clients accept a server without a real upstream; **it does not establish accurate or traceable UTC**. Do not use it to hide a lost upstream on a server that should have one. Server power loss/drift affects every client; provide a battery, continuous power, or a time-reset procedure. Official references: [chrony access control](https://chrony-project.org/doc/4.6/chrony.conf.html#allow) and [isolated-network local mode](https://chrony-project.org/doc/4.6/chrony.conf.html#local).

## Temporarily Stop or Resume Synchronization

To temporarily stop automatic discipline, exit timestamp-sensitive tasks first and run as `root`:

```bash
/etc/init.d/S49ntp stop
```

Stopping does not clear current system time, but the clock will drift freely. This stops the current service only; it does not disable the next boot's automatic start. Resume with:

```bash
/etc/init.d/S49ntp start
```

Recheck synchronization before acquisition. NTP cannot operate without networking. If switching time sources, ensure only one service disciplines the system clock. PPS alone supplies no date, and this page's PTP master does not discipline the system in reverse. Without a battery or trusted external source, true UTC during power loss cannot be recovered automatically.

## Check Synchronization Status

Run on the board:

```bash
cat /etc/ntp.conf
cat /etc/default/ntpd
pidof ntpd
date -u
ntpq -pn
ntpq -c rv
```

Verify the intended selected server (`*`), a synchronized system state, and sustained offset, jitter, and reach. Measure accuracy separately against the application target. Recheck after an offline boot, network loss, or reconnection. Without an available source, neither the displayed date nor a running process establishes UTC readiness.

## Manual Recovery Calibration

There is no need to run this script when automatic synchronization works. The following covers manual recovery with `x5_sync_time.sh`; it immediately changes the clock and handles resolver/timezone/RTC settings and service switching. Do not loop it as a boot job.

### Prerequisites

- The board can reach the target NTP server; a same-subnet numeric IP needs neither Internet nor DNS, while other subnets need routing;
- UDP `123` is reachable;
- Run as `root`;
- Exit foreground demos, ROS2 nodes, or other timestamp-sensitive tasks first with `Ctrl+C`;
- Keep `cam-service` running;
- The script checks required dependencies and handles missing dependencies per its error output.

### Get the Script

The script is in the public non-ROS demo repository:

```text
scripts/env_setup/x5_sync_time.sh
```

Upload from the host:

```bash
X5_IP=192.168.1.12  # change to the actual board address
git clone --branch V2_main https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
scp scripts/env_setup/x5_sync_time.sh root@${X5_IP}:/root/x5_sync_time.sh
```

### Run On-Device

```bash
X5_IP=192.168.1.12  # change to the actual board address
ssh root@${X5_IP}
chmod +x /root/x5_sync_time.sh
/root/x5_sync_time.sh
```

### Default Behavior

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

### Verify

```bash
date
date -u
ntpq -pn
command -v hwclock >/dev/null 2>&1 && hwclock -r -u
```

`date` and `date -u` should reflect the new system time; `ntpq -pn` should show a selected `*` peer. The `*` only proves that `ntpd` selected a peer, not a guarantee of sync accuracy, offset, or jitter. `hwclock` runs only when the tool exists on the system.

### Custom Server

```bash
NTP_SERVER=0.pool.ntp.org  # change to the actual primary NTP server
NTP_FALLBACK_SERVER=202.118.1.81  # change to the actual fallback NTP server
/root/x5_sync_time.sh \
  --server ${NTP_SERVER} \
  --fallback-server ${NTP_FALLBACK_SERVER}
```

These two server parameters select the one-shot `ntpdate` only. For persistent peers, edit `/etc/ntp.conf` as described in “Change NTP Servers”. On isolated networks, point both one-shot arguments at actual internal sources to avoid the default public fallback. The manual script still handles runtime DNS; use `--dns` and `--resolv-file` for an approved resolver when needed. Numeric-IP calibration needs no DNS, but that does not mean the manual script leaves the resolver untouched. `--ntpq-timeout` changes the wait time and `--no-rtc` skips RTC writes; writing RTC without a battery does not preserve time over power loss. Full options:

```bash
/root/x5_sync_time.sh --help
```

`--allow-unverified` only means that when `ntpq` is unavailable, a successful one-shot sync may return `0`; it does not prove a persistent `ntpd` peer lock. `--stop-ptp4l` is only for scenarios where stopping PTP is explicitly chosen and is not recommended by default.

### Return Codes

| Code | Meaning |
|---:|---|
| `0` | One-shot sync succeeded and `ntpq` peer selection was verified; or with explicit `--allow-unverified`, one-shot sync succeeded but `ntpq` was unavailable |
| `1` | Dependency, service, network, NTP, or RTC operation failed |
| `2` | One-shot sync succeeded but `ntpq` was unavailable and the persistent daemon verification did not complete; earlier system time, RTC, timezone, resolver, and service changes may already have taken effect |
| `3` | `ntpq` is available but no selected `*` peer appeared within the timeout; earlier system time, RTC, timezone, resolver, and service changes may already have taken effect |

### Troubleshooting

| Symptom | First check | Handling |
|---|---|---|
| Network, DNS, or UDP 123 unreachable | Gateway, route, resolution, and NTP server reachability | Retry after restoring the network |
| Missing `ntpdate` or init script | Script dependency-check output | Provide the runtime environment required by the target system |
| Return code `2` | Whether `ntpq` exists | Only a one-shot sync completed; do not treat it as a persistent lock |
| Return code `3` | `ntpq -pn` | Check server, network, and timeout settings |
| System time steps during execution | Whether acquisition/ROS2 tasks are still running | Stop timestamp-sensitive tasks, restart them after NTP completes |

The script only tries to restore prior services on the failure path before the one-shot calibration completes. Once the one-shot calibration completes and enters the persistent daemon verification phase, the system time step, RTC/timezone/resolver changes, and service switch may already have taken effect; therefore return codes `2` or `3` do not mean the pre-execution state was restored. After success or entering the above verification-failure state, `phc2sys` may remain stopped; to continue PTP master, re-confirm and start the PHC/PTP link per [PTP Sync](ptp-sync.md).
