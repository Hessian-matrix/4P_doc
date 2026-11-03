# Wi-Fi 配置

本页说明 `wifi_setup` 命令的使用方法；支持：

- **AP 模式**：把 X5 变成 2.4 GHz Wi-Fi 热点，并通过 DHCP 给客户端分配地址；
- **客户端（STA）模式**：扫描可见 Wi-Fi，连接路由器并通过 DHCP 获取地址；
- 查看当前接口、连接和已保存配置状态；
- 停用 Wi-Fi；
- 可选保存当前配置，在设备开机后自动恢复。

```{warning}
切换 AP/STA 或停用 Wi-Fi 时，脚本会停止现有 `hostapd`、`wpa_supplicant`、`udhcpc` 和 `dnsmasq`，清空 `wlan0` 地址并重置接口。如果当前 SSH 正通过 `wlan0` 连接，终端会断开。首次配置和恢复操作建议通过有线以太网 SSH，必要时使用产品确认的 `1.8V` DEBUG_UART。
```

## 1. 前置条件

- 使用 `root` 登录 X5；
- X5 已识别板载 Wi-Fi 接口，默认接口名为 `wlan0`；
- 系统提供 Bash、`/usr/bin/env`、`ip`、`iw`、`hostapd`、`dnsmasq`、`wpa_supplicant`、`wpa_cli`、`udhcpc`、`killall`、`awk`、`sed`、`flock`、`mountpoint`、`seq` 和常用 BusyBox 命令；
- `/userdata` 是已挂载的持久化分区，`/run` 是每次开机清空的运行态目录；
- 系统包含 `/usr/bin/wifi_setup`、`/etc/init.d/S99wifi_setup`，启动入口晚于 userdata 挂载和无线驱动就绪；
- 本工具独占无线服务进程。现有全局停止操作不适合与其他接口的 DHCP/DNS 管理器共用。

## 2. 使用入口

系统内置 `/usr/bin/wifi_setup` 和 `/etc/init.d/S99wifi_setup`，分别作为 Wi-Fi 配置命令和开机恢复入口。正常使用无需额外上传或安装脚本。可在板端检查入口和帮助：

```bash
command -v wifi_setup
test -x /etc/init.d/S99wifi_setup
mountpoint /userdata
wifi_setup --help
```

## 3. 启动交互配置

需要保留交互式终端，因此推荐使用 `ssh -t`：

```bash
X5_IP='BOARD_IP'  # 将 BOARD_IP 替换为实际板卡地址
ssh -t root@${X5_IP} "wifi_setup"
```

也可以先登录板端再运行：

```bash
X5_IP='BOARD_IP'  # 将 BOARD_IP 替换为实际板卡地址
ssh root@${X5_IP}
wifi_setup
```

主菜单：

```text
1) AP 模式：把板子变成热点
2) 客户端模式：扫描并连接路由器 WiFi
3) 查看状态
4) 停用 WiFi（停止服务并关闭 wlan0）
5) 退出
```

## 4. 配置 AP 热点

在主菜单输入 `1`。脚本依次询问：

| 参数 | 默认值 | 说明 |
|---|---|---|
| AP SSID | `RoboBaton-X5` | 客户端扫描时看到的热点名称。 |
| AP 密码 | 空 | 留空会建立开放热点；WPA2 密码必须为 8–63 个字符，并需要再次确认。 |
| 2.4 GHz 信道 | `1` | 支持 `1–13`。 |
| AP IP | `192.168.5.1` | 固定使用 `/24` 掩码。 |
| DHCP 起始地址 | `192.168.5.2` | 分配给 Wi-Fi 客户端。 |
| DHCP 结束地址 | `192.168.5.254` | 分配给 Wi-Fi 客户端。 |

直接按 Enter 可以接受方括号中的默认值。除隔离调试环境外，不建议使用空密码开放热点。

启动成功时终端会显示类似：

```text
AP 已启动：SSID=RoboBaton-X5, IP=192.168.5.1, DHCP=192.168.5.2-192.168.5.254
```

客户端连接热点后，确认获得 `192.168.5.0/24` 网段地址，并测试板端 AP 地址：

```bash
ping 192.168.5.1
```

```{note}
AP 模式只配置本地热点、板端地址和 DHCP，不配置 NAT、IP forwarding 或上游互联网共享。客户端能连接热点不代表能够通过 X5 访问 Internet。
```

## 5. 配置客户端（STA）模式

在主菜单输入 `2`。脚本会：

1. 拉起并重置 `wlan0`；
2. 扫描当前可见 SSID；
3. 显示编号列表；
4. 等待输入 Wi-Fi 编号；
5. 隐藏输入密码；开放网络可以留空；
6. 等待关联完成；
7. 使用 `udhcpc` 获取 DHCP 地址；
8. 打印 `wlan0` 地址。

SSID 选择提示中：

- 输入编号选择网络；
- 输入 `r` 重新扫描；
- 输入 `q` 退出。

交互菜单只允许选择扫描到的可见 SSID；隐藏 SSID 不在当前交互流程支持范围内。

连接成功后检查：

```bash
wifi_setup --status
ip -4 addr show dev wlan0
iw dev wlan0 link
ip route
```

脚本在关联成功但 DHCP 失败时会输出警告。此时先检查路由器 DHCP、地址池和接入控制，不要仅凭 `iw ... link` 已关联就认为网络已经可用。

## 6. 开机自动恢复

AP 或 STA 启动成功后，脚本会询问：

```text
是否保存/更新为开机自动启动当前 WiFi 配置？ [y/N]
```

无论是否启用自启动，配置成功后模式和凭据都会保存到 `/userdata/wifi/current.conf`。输入 `y` 创建 `/userdata/wifi/autostart.enabled`；否则移除标记。配置文件存在不代表允许开机恢复。

`/etc/init.d/S99wifi_setup` 在 userdata 挂载与驱动就绪后执行：

```bash
/usr/bin/wifi_setup --boot
```

未启用时不触碰接口；启用但配置缺失时明确失败，不建立默认开放热点。一次开机成功恢复后重复 start 不重置连接；`/run/wifi_setup.boot-applied` 只记录本次恢复，不代表实时连接健康。`--stop` 清除该运行态标记，但不删除持久化启用标记。没有后台重连监督或新增 DHCP 续租服务。

脚本会把 `current.conf`、`hostapd.conf` 和 `wpa_supplicant.conf` 设置为仅 root 可读写，但 Wi-Fi 密码仍以明文形式保存在板端。不要上传、分享或提交这些文件。

手动验证已保存配置：

```bash
wifi_setup --apply-saved
wifi_setup --status
```

## 7. 常用命令

```bash
# 进入交互菜单
wifi_setup

# 应用已保存配置
wifi_setup --apply-saved

# 查看接口、连接、保存配置和开机启动状态
wifi_setup --status

# 停止 Wi-Fi 进程、清空地址并关闭 wlan0；不卸载内核驱动
wifi_setup --stop
wifi_setup --disable

# 显示帮助
wifi_setup --help
```

交互菜单选择“停用 Wi-Fi”后，还会询问是否同时关闭本脚本管理的开机自动启动。直接运行 `--stop` 或 `--disable` 只停用当前运行状态，不删除已保存配置，也不自动修改开机启动设置。

## 8. 文件和日志

| 路径 | 内容 |
|---|---|
| `/usr/bin/wifi_setup` | Wi-Fi 配置程序。 |
| `/etc/init.d/S99wifi_setup` | 专用开机恢复入口。 |
| `/userdata/wifi/autostart.enabled` | 持久化开机启用标记。 |
| `/userdata/wifi/current.conf` | 已保存模式和凭据，权限为 `600`。 |
| `/userdata/wifi/hostapd.conf` | AP 模式配置。 |
| `/userdata/wifi/wpa_supplicant.conf` | STA 模式配置。 |
| `/userdata/wifi/scan_ssids.txt` | 最近一次扫描到的 SSID。 |
| `/userdata/wifi/logs/hostapd.log` | AP 启动日志。 |
| `/userdata/wifi/logs/dnsmasq.log` | DHCP 服务日志。 |
| `/userdata/wifi/logs/wpa_supplicant.log` | STA 连接日志。 |
| `/userdata/wifi/boot.log` | 开机自动恢复日志。 |
| `/run/wifi_setup.boot-applied` | 本次开机恢复成功标记，重启后清空。 |
| `/run/wifi_setup.lock` | 防止并行配置的操作锁。 |
| `/etc/init.d/S41eth0-route-fallback` | 保留静态有线配置，仅忽略 eth0 IPv4 断线路由。 |

`/userdata/wifi/` 默认权限为 `700`。排查问题时可以读取日志，但对外提供日志前应删除 SSID、密码、IP 和其他现场网络信息。

## 9. 故障排查

### 提示缺少命令

脚本启动时会检查全部 AP/STA 依赖。出现 `缺少命令` 时，说明当前系统不包含完整 Wi-Fi 用户态工具；不要从未知来源覆盖系统命令，应记录缺失命令和系统版本并联系产品支持。

### STA 未扫描到 SSID

检查：

```bash
ip link show wlan0
iw dev wlan0 info
iw dev wlan0 scan
```

确认天线、距离、路由器广播和频段兼容性。当前交互流程不能手工输入隐藏 SSID。

### STA 认证失败

重新运行脚本并确认 SSID、密码和信号；查看：

```bash
cat /userdata/wifi/logs/wpa_supplicant.log
```

### STA 已关联但没有 IP

检查：

```bash
iw dev wlan0 link
ip -4 addr show dev wlan0
ip route
```

确认路由器 DHCP 已启用且地址池未耗尽。脚本不会在 DHCP 失败后自动配置静态地址。

### AP 无法启动或客户端获取不到地址

检查：

```bash
wifi_setup --status
cat /userdata/wifi/logs/hostapd.log
cat /userdata/wifi/logs/dnsmasq.log
```

确认信道为 `1–13`，AP IP 和 DHCP 地址在同一 `/24` 网段，并避免与板端其他接口或当前网络重复。

### 开机后没有恢复 Wi-Fi

检查：

```bash
ls -l /userdata/wifi/autostart.enabled /userdata/wifi/current.conf
cat /userdata/wifi/boot.log
wifi_setup --status
```

确认专用启动入口在 userdata 挂载和驱动就绪之后执行；首次未配置时没有 boot.log 属正常。应在实际设备上确认冷启动恢复，手动 start 不代替整机重启。若沿用静态有线路由，`S41eth0-route-fallback` 在 `S40network` 后设置 `net.ipv4.conf.eth0.ignore_routes_with_linkdown=1`；不改变地址、网关或 metric，只处理无载波的 IPv4 路由，不检测上游故障或 IPv6。

### 停止 Wi-Fi

通过有线以太网或 `1.8V` DEBUG_UART 登录后执行：

```bash
wifi_setup --disable
```

该命令关闭 `wlan0`，但不会卸载板载 Wi-Fi 内核驱动，也不会改动有线网络配置。
