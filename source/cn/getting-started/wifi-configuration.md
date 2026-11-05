# Wi-Fi 配置

本页说明 `wifi_setup` 命令的使用方法；支持：

- **AP 模式**：把 X5 变成可选 2.4 GHz 或 5 GHz 的 Wi-Fi 热点，一次只运行一个频段（不支持同时双频），并通过 DHCP 给客户端分配地址；
- **客户端（STA）模式**：扫描可见 Wi-Fi，连接路由器并通过 DHCP 获取地址；
- 查看当前接口、连接和已保存配置状态；
- 停用 Wi-Fi；
- 可选保存当前配置，在设备开机后自动恢复。

```{warning}
切换 AP/STA 或停用 Wi-Fi 时，脚本会停止无线 `hostapd`、`wpa_supplicant`、`udhcpc` 及本工具拥有的 Wi-Fi `dnsmasq`，清空 `wlan0` 地址并重置接口。如果当前 SSH 正通过 `wlan0` 连接，终端会断开。首次配置和恢复操作建议通过有线以太网 SSH，必要时使用产品确认的 `1.8V` DEBUG_UART。
```

(wifi-factory-hotspot)=
## 出厂热点与快速连接

配套新镜像在没有既有 Wi-Fi 状态时，默认初始化并启用以下热点；较旧固件可能没有此策略。文档更新不表示已发布的旧镜像下载已被替换，也不会自动更新已有设备。

| 项目 | 出厂热点配置 |
|---|---|
| 热点名称（SSID） | `RoboBaton-4P` |
| 频段与信道 | 5 GHz，信道 `36`（`AP_CHANNEL=36`），20 MHz、非 DFS |
| 安全方式 | WPA2-PSK / CCMP；使用随设备提供的热点密码，不是开放热点 |
| 板端地址 | `192.168.5.1/24` |
| 客户端 DHCP 范围 | `192.168.5.2–192.168.5.254` |
| DHCP 租期 | `12` 小时，由客户端自动续租；不是连接时长上限 |

1. 等待设备与无线服务就绪，在支持 5 GHz 的电脑或手机选择 `RoboBaton-4P` 并输入交付的热点密码。不支持该频段或受当地法规限制时，通过有线以太网或调试串口运行 `wifi_setup`，手动改选允许的频段和信道；不会自动回退到 2.4 GHz。
2. 客户端选择自动获取地址，确认获得上述网段地址；设备提示“无互联网”不等于本地连接失败。
3. 浏览器直接打开 `http://192.168.5.1/`，查看传感器或控制板端录包；正常使用不需要先 SSH 登录或手动启动应用。网页无身份认证，只在可信隔离网络使用，勿映射到公网。功能说明见{ref}`首次上电网页入口 <first-boot-web>`。

初始化入口 `/etc/init.d/S98wifi_default` 仅在系统分区 `/etc/4p/wifi` 不存在时，从受保护模板准备配置和开机启用标记，再由 `/etc/init.d/S99wifi_setup` 启动热点。普通重启保留该目录内的 AP/STA、所选 AP 频段/信道和停用选择；重烧 system 后按新镜像默认值重新初始化，AP 恢复为 5 GHz 信道 `36`，即使保留 userdata，也不再导入旧 `/userdata/wifi` 配置。出厂 SSID、WPA2 安全方式、热点密码及 IP/DHCP 配置不因频段默认值调整而改变。初始化失败不发布半配置状态，后续开机可重试，不回退开放热点。日常修改使用 `wifi_setup`，不要格式化 userdata 或删除录制数据。

Wi-Fi 与 USB NCM/RNDIS/ECM 网卡使用独立 DHCP 实例，默认子网分别为 `192.168.5.0/24` 与 `192.168.7.0/24`，可以共存。Wi-Fi AP 下发自身地址作为网关/DNS，USB 不下发网关/DNS；AP 不自动提供 NAT 或互联网共享。自定义地址时避免两个接口及客户端已有网络的子网重叠。两者当前租期均为 `12` 小时，正常自动续租可持续使用，不是到时强制断开；续租失败直至租约过期时客户端不能继续使用该租约地址。

以上描述配套镜像配置，不代表实板冷启动、射频连接或任意手机/电脑兼容性验收。

## 1. 前置条件

- 使用 `root` 登录 X5；
- X5 已识别板载 Wi-Fi 接口，默认接口名为 `wlan0`；
- 系统提供 Bash、`/usr/bin/env`、`ip`、`iw`、`hostapd`、`dnsmasq`、`wpa_supplicant`、`wpa_cli`、`udhcpc`、`killall`、`awk`、`sed`、`flock`、`stat`、`readlink`、`seq` 和常用 BusyBox 命令；
- `/etc/4p` 由可信 root 管理，保存或修改设置需要系统分区可写；`/run` 每次开机清空；
- 系统包含 `/usr/bin/wifi_setup`、`/etc/init.d/S99wifi_setup`，启动入口晚于无线驱动就绪；Wi-Fi 配置不依赖 userdata 挂载；
- 本工具独占无线服务进程；Wi-Fi DHCP 仅按自身 PID 与接口身份停止，不停止配套 USB DHCP。`hostapd`、`wpa_supplicant`、`udhcpc` 仍按进程名停止，不适合与其他接口共享这些无线/客户端服务。

## 2. 使用入口

系统内置 `/usr/bin/wifi_setup` 和 `/etc/init.d/S99wifi_setup`，分别作为 Wi-Fi 配置命令和开机恢复入口。正常使用无需额外上传或安装脚本。可在板端检查入口和帮助：

```bash
command -v wifi_setup
test -x /etc/init.d/S99wifi_setup
test -w /etc
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

在主菜单输入 `1`。以下是**手动创建 AP** 的交互默认值，不是上文的出厂热点配置；交互不会自动沿用出厂 SSID 或密码。脚本依次询问：

| 参数 | 手动配置默认值 | 说明 |
|---|---|---|
| AP SSID | `RoboBaton-X5` | 客户端扫描时看到的热点名称。 |
| AP 密码 | 空 | 留空会建立开放热点；WPA2 密码必须为 8–63 个字符，并需要再次确认。 |
| AP 频段 | `5` | 输入 `2.4` 或 `5`，然后选择该频段的信道；一次只启用一个频段。 |
| AP 信道 | 5 GHz 为 `36`；2.4 GHz 为 `1` | 2.4 GHz 允许 `1–13`；5 GHz 仅允许 `36`、`40`、`44`、`48`、`149`、`153`、`157`、`161`、`165`。 |
| AP IP | `192.168.5.1` | 固定使用 `/24` 掩码。 |
| DHCP 起始地址 | `192.168.5.2` | 分配给 Wi-Fi 客户端。 |
| DHCP 结束地址 | `192.168.5.254` | 分配给 Wi-Fi 客户端。 |

直接按 Enter 可以接受方括号中的默认值。除隔离调试环境外，不建议使用空密码开放热点。

AP 与现有 STA 一样使用 `CN` 国家码。5 GHz 仅支持上述 20 MHz、非 DFS 信道，不支持 DFS 或 40/80 MHz；信道 `36–48` 按适用法规限室内使用。脚本允许列表不替代实际驱动、固件和监管域约束，应以设备实际允许的信道与当地法规为准。信道不可用或热点启动失败时会报错，不自动换信道或回退频段；使用独立的有线/串口入口手动重新配置。

保存格式仍只使用 `AP_CHANNEL` 表示 AP 频段/信道，不新增频段字段：`1–13` 对应 2.4 GHz，上述 5 GHz 信道对应 5 GHz。已有的 2.4 GHz 保存配置继续按原信道恢复，不会在普通重启时升级为 5 GHz。

启动成功时终端会显示类似：

```text
AP 已启动：SSID=RoboBaton-X5, 信道=36, IP=192.168.5.1, DHCP=192.168.5.2-192.168.5.254
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

无论是否启用自启动，配置成功后模式和凭据都会保存到 `/etc/4p/wifi/current.conf`。输入 `y` 创建 `/etc/4p/wifi/autostart.enabled`；否则移除标记。配置文件存在不代表允许开机恢复。设置随普通重启保留，重烧 system 恢复镜像默认值；旧 userdata 配置不再读取。

`/etc/init.d/S99wifi_setup` 在驱动就绪后执行：

```bash
/usr/bin/wifi_setup --boot
```

未启用时不触碰接口；启用但配置缺失时明确失败，不建立默认开放热点。一次开机成功恢复后重复 start 不重置连接；`/run/wifi_setup.boot-applied` 只记录本次恢复，不代表实时连接健康。`--stop` 清除该运行态标记，但不删除持久化启用标记。没有后台重连监督或新增 DHCP 续租服务。

配套新镜像仅在上文所述无既有状态时初始化出厂热点并启用恢复；以后按保存标记执行，不会每次开机重置。要关闭当前 Wi-Fi 并取消后续开机恢复，运行 `wifi_setup`，选择“停用 WiFi”，再对“是否同时关闭开机自动启动 WiFi？”输入 `y`。仅执行 `--stop` / `--disable` 不取消下次开机恢复。

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
| `/etc/init.d/S98wifi_default` | 配套新镜像的首次出厂热点初始化入口，先于 S99 恢复。 |
| `/etc/default/4p-wifi-ap` | 受保护的出厂 AP 模板，root:root、`600`；含密码，不得公开分享。 |
| `/etc/4p/wifi/autostart.enabled` | 系统分区开机启用标记，权限 `600`。 |
| `/etc/4p/wifi/current.conf` | 已保存模式和凭据，权限 `600`。 |
| `/run/4p-wifi/hostapd.conf` | AP 运行配置，重启清空。 |
| `/run/4p-wifi/wpa_supplicant.conf` | STA 运行配置，重启清空。 |
| `/run/4p-wifi/scan_ssids.txt` | 最近一次扫描到的 SSID。 |
| `/run/4p-wifi/logs/hostapd.log` | 本次开机的 AP 启动日志。 |
| `/run/4p-wifi/logs/dnsmasq.log` | 本次开机的 DHCP 服务日志。 |
| `/run/4p-wifi/logs/wpa_supplicant.log` | 本次开机的 STA 连接日志。 |
| `/run/4p-wifi/boot.log` | 本次开机的自动恢复日志。 |
| `/run/wifi_setup.boot-applied` | 本次开机恢复成功标记，重启后清空。 |
| `/run/wifi_setup.lock` | 防止并行配置的操作锁。 |
| `/etc/init.d/S41eth0-route-fallback` | 保留静态有线配置，仅忽略 eth0 IPv4 断线路由。 |

`/etc/4p/wifi/` 和 `/run/4p-wifi/` 默认权限为 `700`。运行配置与日志在重启后清空；旧 userdata 中的日志不自动删除。排查问题时可读取日志，对外提供前应删除 SSID、密码、IP 和其他现场网络信息。

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
cat /run/4p-wifi/logs/wpa_supplicant.log
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
cat /run/4p-wifi/logs/hostapd.log
cat /run/4p-wifi/logs/dnsmasq.log
```

确认信道属于所选频段的允许范围：2.4 GHz 为 `1–13`，5 GHz 仅为 `36`、`40`、`44`、`48`、`149`、`153`、`157`、`161`、`165`；同时核对实际驱动/监管域、`CN` 国家码和适用的室内限制。5 GHz 使用 20 MHz、非 DFS，不自动回退；通过有线/串口手动改选允许的信道或频段。确认客户端支持该频段，AP IP 和 DHCP 地址在同一 `/24` 网段，并避免与板端其他接口或当前网络重复。

### 上电后没有看到出厂热点

先通过有线以太网或调试串口确认安装的是配套镜像，再运行 `wifi_setup --status` 并检查 `/etc/4p/wifi` 与本次开机日志。出厂默认是 5 GHz 信道 `36`，确认客户端支持且当地法规允许使用；不支持时手动配置 2.4 GHz，不自动回退。普通重启不会覆盖已保存设置；设备可能正在使用 STA、不同 SSID/频段/信道或已关闭开机恢复。重烧 system 则恢复镜像默认值，不读取旧 userdata 配置。使用交互菜单明确配置 AP 和是否开机恢复，不删除录制数据，不对外发送模板、凭据或带密码日志。无线驱动、天线及关联问题仍按 AP 排障处理。

### 开机后没有恢复 Wi-Fi

检查：

```bash
ls -l /etc/4p/wifi/autostart.enabled /etc/4p/wifi/current.conf
cat /run/4p-wifi/boot.log
wifi_setup --status
```

确认专用启动入口在驱动就绪之后执行；未启用恢复时没有 boot.log 属正常。应在实际设备上确认冷启动恢复，手动 start 不代替整机重启。若沿用静态有线路由，`S41eth0-route-fallback` 在 `S40network` 后设置 `net.ipv4.conf.eth0.ignore_routes_with_linkdown=1`；不改变地址、网关或 metric，只处理无载波的 IPv4 路由，不检测上游故障或 IPv6。

### 停止 Wi-Fi

通过有线以太网或 `1.8V` DEBUG_UART 登录后执行：

```bash
wifi_setup --disable
```

该命令关闭 `wlan0`，但不会卸载板载 Wi-Fi 内核驱动，也不会改动有线网络配置。
