# X5 PTP Master 配置指南（Mid-360 示例）

> Scope: 本文档的主体是 X5 作为 LinuxPTP IEEE1588v2 UDP/IP master 的配置、启动和验证。Mid-360 仅作为示例 slave 用来验证 master 侧配置。
>
> 示例板端：X5 板端，默认 PTP 网段地址为 `192.168.1.12/24`。
>
> 下面的命令都以 Mid-360 为示例；如果你换成其他 PTP slave，通常只需要替换从设备 IP、网段地址和抓包目标。

## 1. 结论

Mid-360 官方支持 PTP、gPTP、GPS 三种同步方式；这里采用官方 PTP 流程。X5 作为唯一 master，Mid-360 作为 slave，链路需要支持硬件时间戳。

X5 板端实测满足这个方案的基本条件：

| 项目 | 观测值 |
|---|---|
| 系统 | Buildroot 2022.08，kernel `6.1.83-DR-PL5.1_V1.1.2` |
| 网口 | `eth0` |
| PTP 硬件时钟 | `/dev/ptp0` |
| 硬件时间戳 | `SOF_TIMESTAMPING_TX_HARDWARE`、`SOF_TIMESTAMPING_RX_HARDWARE`、`SOF_TIMESTAMPING_RAW_HARDWARE` |
| 工具 | `ptp4l`、`phc2sys`、`pmc`、`tcpdump` |

## 2. 安全边界

1. 不要把 Mid-360 的 RJ45 接 PoE。
2. 同一个 Mid-360 网络里只允许一个 PTP master。
3. 不要把 PTP 和 gPTP 混在同一网络里使用。
4. 脚本会重启 X5 上的 `ptp4l` 和 `phc2sys`，并写入 `/etc/linuxptp-mid360-master.cfg`、`/etc/default/ptp4l`、`/etc/default/phc2sys`。
5. 脚本只会确认/补齐 `eth0` 上的 PTP 网段地址，默认 `192.168.1.12/24`；不会重写 `/etc/network/interfaces`。

## 3. 推荐网络（Mid-360 示例）

```text
X5 eth0  <---- 非 PoE 网线/普通交换机 ---->  Mid-360 RJ45
```

默认地址约定：

| 设备 | 地址 |
|---|---|
| X5 PTP 网段地址 | `192.168.1.12/24` |
| Mid-360 地址 | `192.168.1.100` |

如果你的 Mid-360 已改成别的 IP，用 `--lidar-ip` 指定；如果 LiDAR 网段不是 `192.168.1.0/24`，用 `--host-lidar-cidr` 指定 X5 的网段地址。

## 4. 一键配置和验证

脚本位于 `RoboBaton_4p_demo/scripts/env_setup/configure_x5_ptp_master.sh`。如果你已经有这个公开仓库，直接复制脚本到板端即可：

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
scp scripts/env_setup/configure_x5_ptp_master.sh root@<x5-ip>:/root/configure_x5_ptp_master.sh
```

然后登录 X5，在板端执行：

```sh
ssh root@<x5-ip>
chmod 755 /root/configure_x5_ptp_master.sh
sh /root/configure_x5_ptp_master.sh \
  --interface eth0 \
  --host-lidar-cidr 192.168.1.12/24 \
  --lidar-ip 192.168.1.100 \
  --verify-timeout 30
```

如果没有 SSH key，可以先把脚本放进 `/root/`，再执行。

脚本成功时最后输出：

```text
RESULT=PASS
```

`RESULT=PASS` 代表：

1. `eth0` 支持 PTP 硬件 TX/RX/raw timestamp。
2. X5 已确认或追加 PTP 网段地址 `192.168.1.12/24`。
3. `ptp4l` 已按 master 配置启动。
4. `phc2sys` 已启动，使 `eth0` PHC 跟随 `CLOCK_REALTIME`。
5. `pmc` 看到了 `portState MASTER`。
6. `tcpdump` 捕获到了 PTP 报文。
7. Mid-360 侧报文中的 `timestamp_type` 表示 PTP 同步。

如果没有 Mid-360 接入，或 Mid-360 IP 不匹配，脚本会配置服务但最终可能返回 `RESULT=FAIL`，常见失败点是 `PTP_LIDAR_PACKET=FAIL`。

## 5. 脚本写入的配置

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

关键点：

- `masterOnly 1`：X5 只作为 master。
- `network_transport UDPv4`：对应 Mid-360 官方 PTP UDP/IP。
- `delay_mechanism E2E`：对应官方 Delay request-response 机制。
- `time_stamping hardware`：使用 X5 `eth0` 的硬件时间戳。

### 5.2 `/etc/default/ptp4l`

```sh
PTP4L_ARGS="-f /etc/linuxptp-mid360-master.cfg -i eth0"
```

### 5.3 `/etc/default/phc2sys`

```sh
PHC2SYS_ARGS="-c eth0 -s CLOCK_REALTIME -O 0 -S 1.0"
```

含义：

- `-s CLOCK_REALTIME`：X5 系统时间作为源。
- `-c eth0`：同步到 `eth0` 的 PTP hardware clock。
- `-O 0`：不加固定偏移。
- `-S 1.0`：初始差值超过 1 秒时直接 step。

### 5.4 ifupdown 地址钩子

脚本会写入：

```text
/etc/network/if-up.d/mid360-ptp-alias
/etc/network/if-down.d/mid360-ptp-alias
```

用途：网卡 up/down 时自动添加/删除 `192.168.1.12/24` 的 PTP 网段地址。脚本不重写 `/etc/network/interfaces`，避免误伤其他地址、网关和 metric。

## 6. 手工验证命令

脚本已经自动执行了这些检查；需要人工复核时可在板端运行：

```sh
ethtool -T eth0
ip -br addr show eth0
ps w | sed -n '/[p]tp4l\|[p]hc2sys/p'
pmc -u -b 0 'GET PORT_DATA_SET'
tcpdump -i eth0 -nn 'udp port 319 or udp port 320'
tcpdump -i eth0 -nn 'host 192.168.1.100 and (udp port 319 or udp port 320)'
```

期望：

- `ethtool -T eth0` 里有硬件 TX/RX/raw timestamp。
- `pmc` 输出包含 `portState MASTER`。
- 抓包可见 UDP 319/320 PTP 报文。
- 接入 Mid-360 后，抓包可见与 Mid-360 IP 相关的 PTP 报文。

Mid-360 侧最终确认方式：

1. 查看点云包头 `timestamp_type`；官方说明 `timestamp_type == 1` 表示 PTP 同步，时间字段为 `uint64_t`，单位 ns。
2. 或使用 Livox Viewer 的 Settings 查看 Sync Type。

## 7. 失败排查

| 现象 | 优先检查 |
|---|---|
| `eth0 lacks hardware ... timestamping` | 确认参数 `--interface` 是否是接 Mid-360 的有线网口；无线/`can0` 不适合该方案 |
| `ptp4l did not reach MASTER` | 检查 `/etc/linuxptp-mid360-master.cfg`，确认没有其他 PTP master 冲突 |
| `PTP_ANY_PACKET=FAIL` | 检查 `ptp4l` 是否存活、网口是否 up、网卡是否支持硬件 timestamp |
| `PTP_LIDAR_PACKET=FAIL` | 检查 Mid-360 是否上电、IP 是否等于 `--lidar-ip`、线缆是否非 PoE、是否和 X5 在同一二层网络 |
| Livox 数据仍非 PTP | 检查点云包头 `timestamp_type`，确认网络里没有 gPTP/其他 PTP master 干扰 |

## 8. 回滚

脚本每次覆盖已存在文件前都会保留带 run id 的备份，例如：

```text
/etc/linuxptp-mid360-master.cfg.bak.<run-id>
/etc/default/ptp4l.bak.<run-id>
/etc/default/phc2sys.bak.<run-id>
```

手工回滚示例：

```sh
cp -p /etc/default/ptp4l.bak.<run-id> /etc/default/ptp4l
cp -p /etc/default/phc2sys.bak.<run-id> /etc/default/phc2sys
[ -f /etc/linuxptp-mid360-master.cfg.bak.<run-id> ] && \
  cp -p /etc/linuxptp-mid360-master.cfg.bak.<run-id> /etc/linuxptp-mid360-master.cfg
rm -f /etc/network/if-up.d/mid360-ptp-alias /etc/network/if-down.d/mid360-ptp-alias
ip addr del 192.168.1.12/24 dev eth0 2>/dev/null || true
/etc/init.d/S65ptp4l restart
/etc/init.d/S66phc2sys restart
```

## 9. 参考源

- Livox Mid-360 同步方式和 PoE 警告：<https://livox-wiki-en.readthedocs.io/en/latest/tutorials/new_product/mid360/mid360.html>
- LinuxPTP 硬件/软件 timestamp 能力和 `ethtool -T` 检查：<https://raw.githubusercontent.com/richardcochran/linuxptp/master/README.org>
