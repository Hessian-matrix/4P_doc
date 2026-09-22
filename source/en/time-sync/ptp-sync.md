# PTP Sync

> **Example note:** This page is an **X5 master + Mid-360 slave** configuration example, used to explain LinuxPTP master configuration, startup, and verification. Other PTP devices that support IEEE 1588v2 UDP/IP can refer to this flow, but must adapt it to the actual network port, address, slave, configuration file, and device-side verification method.
>
> The main body of this document is the X5 acting as a LinuxPTP IEEE1588v2 UDP/IP master. Mid-360 is only the example slave used to verify the master-side configuration.
>
> Example device: X5 board, default PTP subnet address `192.168.1.12/24`.
>
> All commands below use Mid-360 as the example; if you switch to another PTP slave, you usually only need to replace the slave device IP, subnet address, and capture target.

## 1. Conclusion

Mid-360 officially supports three sync modes: PTP, gPTP, and GPS; the official PTP flow is used here. The X5 acts as the sole master, Mid-360 as the slave, and the link must support hardware timestamping.

The X5 board satisfies the basic conditions of this scheme:

| Item | Observed value |
|---|---|
| System | Buildroot 2022.08, kernel `6.1.83-DR-PL5.1_V1.1.2` |
| Network port | `eth0` |
| PTP hardware clock | `/dev/ptp0` |
| Hardware timestamp | `SOF_TIMESTAMPING_TX_HARDWARE`, `SOF_TIMESTAMPING_RX_HARDWARE`, `SOF_TIMESTAMPING_RAW_HARDWARE` |
| Tools | `ptp4l`, `phc2sys`, `pmc`, `tcpdump` |

## 2. Safety Boundaries

1. Do not connect Mid-360's RJ45 to PoE.
2. Only one PTP master is allowed in the same Mid-360 network.
3. Do not mix PTP and gPTP in the same network.
4. The script restarts `ptp4l` and `phc2sys` on the X5 and writes `/etc/linuxptp-mid360-master.cfg`, `/etc/default/ptp4l`, `/etc/default/phc2sys`.
5. The script only confirms/adds the PTP subnet address on `eth0`, default `192.168.1.12/24`; it does not rewrite `/etc/network/interfaces`.

## 3. Recommended Network (Mid-360 Example)

```text
X5 eth0  <---- non-PoE cable / ordinary switch ---->  Mid-360 RJ45
```

Default address convention:

| Device | Address |
|---|---|
| X5 PTP subnet address | `192.168.1.12/24` |
| Mid-360 address | `192.168.1.100` |

If your Mid-360 has been changed to another IP, use `--lidar-ip`; if the LiDAR subnet is not `192.168.1.0/24`, use `--host-lidar-cidr` to specify the X5 subnet address.

## 4. One-Click Configuration and Verification

The script is at `RoboBaton_4p_demo/scripts/env_setup/configure_x5_ptp_master.sh`. If you already have this public repository, copy the script to the device directly:

```bash
X5_IP=192.168.1.12  # change to the actual board address
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
scp scripts/env_setup/configure_x5_ptp_master.sh root@${X5_IP}:/root/configure_x5_ptp_master.sh
```

Then log into the X5 and run on-device:

```sh
X5_IP=192.168.1.12  # change to the actual board address
ssh root@${X5_IP}
chmod 755 /root/configure_x5_ptp_master.sh
sh /root/configure_x5_ptp_master.sh \
  --interface eth0 \
  --host-lidar-cidr 192.168.1.12/24 \
  --lidar-ip 192.168.1.100 \
  --verify-timeout 30
```

If you have no SSH key, first place the script in `/root/` and then run it.

On success the script finally outputs:

```text
RESULT=PASS
```

`RESULT=PASS` only means the X5 master configuration and PTP packet connectivity checks passed:

1. `eth0` supports PTP hardware TX/RX/raw timestamp.
2. The X5 confirmed or added the PTP subnet address `192.168.1.12/24`.
3. `ptp4l` started with the master configuration.
4. `phc2sys` started, making the `eth0` PHC follow `CLOCK_REALTIME`.
5. `pmc` saw `portState MASTER`.
6. `tcpdump` captured PTP UDP 319/320 packets.
7. `tcpdump` captured PTP UDP 319/320 packets involving the target slave IP.

It does not prove that Mid-360 or another slave is locked, nor that the slave offset, sync accuracy, or point-cloud `timestamp_type` has reached expectation. The slave state and business-data time type must be verified independently on the device side per section 6.

If no Mid-360 is connected, or the Mid-360 IP does not match, the script configures the services but may finally return `RESULT=FAIL`; a common failure point is `PTP_LIDAR_PACKET=FAIL`.

## 5. Configuration Written by the Script

### 5.1 `/etc/linuxptp-mid360-master.cfg`

```ini
[global]
twoStepFlag             1
masterOnly              1
network_transport       UDPv4
delay_mechanism         E2E
time_stamping           hardware
step_threshold          1.0

[eth0]
```

Key points:

- `masterOnly 1`: the X5 acts only as master.
- `network_transport UDPv4`: matches Mid-360's official PTP UDP/IP.
- `delay_mechanism E2E`: matches the official delay request-response mechanism.
- `time_stamping hardware`: uses the X5 `eth0` hardware timestamp.

### 5.2 `/etc/default/ptp4l`

```sh
PTP4L_ARGS="-f /etc/linuxptp-mid360-master.cfg -i eth0"
```

### 5.3 `/etc/default/phc2sys`

```sh
PHC2SYS_ARGS="-c eth0 -s CLOCK_REALTIME -O 0 -S 1.0"
```

Meaning:

- `-s CLOCK_REALTIME`: the X5 system time is the source.
- `-c eth0`: sync to the `eth0` PTP hardware clock.
- `-O 0`: no fixed offset.
- `-S 1.0`: step directly when the initial difference exceeds 1 second.

### 5.4 ifupdown Address Hook

The script writes:

```text
/etc/network/if-up.d/mid360-ptp-alias
/etc/network/if-down.d/mid360-ptp-alias
```

Purpose: automatically add/remove the `192.168.1.12/24` PTP subnet address on interface up/down. The script does not rewrite `/etc/network/interfaces`, to avoid harming other addresses, gateways, and metrics.

## 6. Manual Verification Commands

The script already ran these checks; run them on-device when manual re-verification is needed:

```sh
ethtool -T eth0
ip -br addr show eth0
ps w | sed -n '/[p]tp4l\|[p]hc2sys/p'
pmc -u -b 0 'GET PORT_DATA_SET'
tcpdump -i eth0 -nn 'udp port 319 or udp port 320'
tcpdump -i eth0 -nn 'host 192.168.1.100 and (udp port 319 or udp port 320)'
```

Expect:

- `ethtool -T eth0` shows hardware TX/RX/raw timestamp.
- `pmc` output includes `portState MASTER`.
- The capture shows UDP 319/320 PTP packets.
- With Mid-360 connected, the capture shows PTP packets related to the Mid-360 IP.

Final confirmation on the Mid-360 side:

1. Check the point-cloud header `timestamp_type`; officially, `timestamp_type == 1` means PTP sync, with the time field as `uint64_t` in ns.
2. Or use Livox Viewer's Settings to view the Sync Type.

## 7. Failure Troubleshooting

| Symptom | Check first |
|---|---|
| `eth0 lacks hardware ... timestamping` | Confirm `--interface` is the wired port connected to Mid-360; wireless/`can0` are not suitable for this scheme |
| `ptp4l did not reach MASTER` | Check `/etc/linuxptp-mid360-master.cfg`, confirm no other PTP master conflict |
| `PTP_ANY_PACKET=FAIL` | Check whether `ptp4l` is alive, the port is up, and the NIC supports hardware timestamp |
| `PTP_LIDAR_PACKET=FAIL` | Check whether Mid-360 is powered, its IP equals `--lidar-ip`, the cable is non-PoE, and it is on the same L2 network as the X5 |
| Livox data still not PTP | Check the point-cloud header `timestamp_type`, confirm no gPTP/other PTP master interference in the network |

## 8. Rollback

Before overwriting an existing file, the script keeps a backup with a run id, e.g.:

```text
/etc/linuxptp-mid360-master.cfg.bak.<run-id>
/etc/default/ptp4l.bak.<run-id>
/etc/default/phc2sys.bak.<run-id>
```

Manual rollback example:

```sh
RUN_ID=20260910_120000_1234  # change to the actual backup run id from the script output
cp -p /etc/default/ptp4l.bak.${RUN_ID} /etc/default/ptp4l
cp -p /etc/default/phc2sys.bak.${RUN_ID} /etc/default/phc2sys
[ -f /etc/linuxptp-mid360-master.cfg.bak.${RUN_ID} ] && \
  cp -p /etc/linuxptp-mid360-master.cfg.bak.${RUN_ID} /etc/linuxptp-mid360-master.cfg
rm -f /etc/network/if-up.d/mid360-ptp-alias /etc/network/if-down.d/mid360-ptp-alias
ip addr del 192.168.1.12/24 dev eth0 2>/dev/null || true
/etc/init.d/S65ptp4l restart
/etc/init.d/S66phc2sys restart
```

## 9. References

- Livox Mid-360 sync modes and PoE warning: <https://livox-wiki-en.readthedocs.io/en/latest/tutorials/new_product/mid360/mid360.html>
- LinuxPTP hardware/software timestamp capability and `ethtool -T` check: <https://raw.githubusercontent.com/richardcochran/linuxptp/master/README.org>
