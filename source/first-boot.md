# 首次上电与开机使用

本页帮助第一次拿到 RoboBaton 4P 的用户完成开机前检查、登录 X5、确认最小系统状态，并选择 [快速开始](quick-start.md) 中的 non-ROS 或 ROS2 路径。部署、升级和回滚细节见 [部署、升级与回滚](deployment-and-upgrade.md)，完整排障见 [故障排查](troubleshooting.md)。

## 1. 开机前检查

供电、相机线缆、UART 和散热边界以 [硬件连接与安全](hardware-and-safety.md) 为准。上电前确认：

- 相机 FPC/同轴线已经在断电状态下插好；相机/FPC/同轴线不支持热插拔，插拔前必须断电。
- 供电为 DC `12V ~ 24V`（3S-6S），供电电流建议不低于 `600 mA`。
- 散热器、风扇和风道无遮挡；风扇会在通电时启动，待系统启动完成会停止，后续风扇温控会在 CPU 温度 `> 55°C` 时启动，在温度降到`< 50°C` 时停止。
- 如使用 UART1/UART7，只连接匹配的 `3.3V` TX/RX/GND 并共地，通用 USB-UART 适配器默认不接 VCC。
- UART1/UART7 两个 3.3V 供电脚对外设供电合计额定边界为 `500 mA`；超过时使用独立电源、保持共地，并防止反向灌入板端 3.3V 电源轨。
- DEBUG_UART 仅用于系统控制台/调试，必须使用 `1.8V` USB-UART 适配器；禁止把 `3.3V` 或 `5V` 逻辑接到 DEBUG_UART。

## 2. 连接并上电

在断电状态下完成相机、供电、网络和可选 UART 调试线连接，然后使用配套的 DC 12V 适配器给设备上电等待系统启动，系统上电时风扇会启动，靠外边的绿色 LED 灯会常亮，等到系统启动完成风扇会停止，靠里面的绿色 LED 会闪烁。启动过程中不要插拔相机/FPC/同轴线，不要停止或重配 `cam-service`，也不要同时启动多个占用相机资源的应用。

## 3. 网络和登录

首次登录建议使用有线以太网。需要把板载 Wi-Fi 配置成 AP 热点或连接路由器时，见 [板载 Wi-Fi 配置](wifi-configuration.md)；切换 Wi-Fi 模式会重置 `wlan0`，不要依赖同一条 Wi-Fi SSH 会话完成切换。

| 项目 | 出厂默认值 |
|---|---|
| IP | `192.168.1.12` |
| 用户 | `root` |
| 密码 | `root` |

```{warning}
首次登录前只在可信、本地、隔离网络中连接设备；修改密码前不要把出厂默认设备暴露到不可信 LAN 或公网。
```

### 配置开发机以太网

设备出厂地址为 `192.168.1.12/24`。直连设备或通过隔离交换机连接时，开发机以太网网卡需要使用 `192.168.1.0/24` 内未被占用的地址，例如 `192.168.1.100/24`。不要把开发机地址设为 `192.168.1.12`，也不要使用该网络中已经被其他设备占用的地址；直连或隔离网络不需要配置网关和 DNS。若开发机已有其他活动网卡或路由占用 `192.168.1.0/24`，先避免路由冲突再测试。

Linux 临时配置示例：

```bash
ip link
sudo ip addr add 192.168.1.100/24 dev <ethernet-iface>
sudo ip link set <ethernet-iface> up
ping -c 4 192.168.1.12
```

`ip addr add` 设置是临时地址，重启或网络服务重启后会消失；如果该地址已经配置在网卡上，不要重复添加。

Windows 图形界面配置：

- Settings -> Network & Internet -> Ethernet -> IP assignment -> Edit -> Manual -> IPv4。
- IP 填 `192.168.1.100`，subnet mask 填 `255.255.255.0`，直连或隔离网络下 gateway/DNS 留空。
- 在 PowerShell 或 cmd 中执行 `ping 192.168.1.12` 验证连通性。

### 修改设备 IP 地址

需要调整设备 IP 时，先用当前 IP SSH 登录设备，再修改系统网络配置：

```bash
ssh root@<x5-ip>
```

登录后先备份当前配置：

```bash
cp -a /etc/network/interfaces /etc/network/interfaces.bak
```

编辑网络配置：

```bash
vi /etc/network/interfaces
```

在对应的已有 interface 配置段中修改 `address` 和 `gateway`。除非部署明确要求变更，否则保留 interface 名称和其他设置。保存前确认新 IP、gateway 与开发机路由兼容，并确认新 IP 未被其他设备占用。

重启使配置生效：

```bash
reboot
```

重启期间当前 SSH 会断开，这是预期行为。设备启动后，使用新 IP 重新 SSH 登录。

如果新配置导致网络无法访问，按已确认的 `1.8V` DEBUG_UART 恢复路径进入系统，恢复备份并重启：

```bash
cp -a /etc/network/interfaces.bak /etc/network/interfaces
reboot
```

### 登录并修改出厂密码

配置好网络后，在开发机登录：

```bash
ssh root@192.168.1.12
```

首次 SSH 登录后可以修改密码：

```bash
passwd
```

`passwd` 是交互式命令，按提示输入新密码。建议到最后生产流程再统一修改root密码，测试过程保持出厂密码即可。

如果用户修改过 IP 且需要通过调试口进入系统查看地址，只能使用 DEBUG_UART：`1.8V` 逻辑，板端 TX 接适配器 RX，板端 RX 接适配器 TX，并共地。禁止在 DEBUG_UART 使用 `3.3V` 或 `5V` USB-UART。

```{note}
忘记密码、系统无法启动和出厂系统镜像恢复步骤暂未公开。恢复介质、恢复范围和凭据重置行为将在产品流程定版后补充；在此之前请联系 [发布、授权与支持](release-and-support.md#授权与支持)，不要刷写未经确认的系统镜像。
```

## 4. 最小系统检查

登录 X5 后执行：

```bash
hostname
date
df -h /
pgrep -a cam-service
```

期望 `hostname`、`date` 和根文件系统空间可正常返回，且能看到 `cam-service` 进程。若 `cam-service` 缺失或异常，先按 [故障排查](troubleshooting.md) 收集现象，不把停止服务作为常规恢复步骤。

如果板卡可以访问 Internet，建议在启动 demo、ROS2 节点或其他时间戳敏感采集前先做 NTP 同步，具体步骤见 [系统时间同步](system-time-sync.md)。

## 5. 确认版本

只在对应目录已经部署时查询版本；这些命令不应启动相机或 IMU。

non-ROS `/root/demo`：

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
```

ROS2 `/root/ros2_demo/install`：

```bash
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

当前发布集合为文档 `v1.0.0`、non-ROS `v1.0.0`、ROS2/package `v1.0.0`；文件和包版本查询结果可能显示不带 `v` 前缀的 `1.0.0`。

## 6. 选择 non-ROS 或 ROS2

| 目标 | 运行目录 | 下一步 |
|---|---|---|
| 四路 RTSP、IMU、UART 示例 | `/root/demo` | 进入 [快速开始](quick-start.md) 的 non-ROS 路径，或阅读 [non-ROS Demo 使用](non-ros-demo.md)。 |
| ROS2 raw/compressed 图像、CameraInfo、IMU、温度 topic | `/root/ros2_demo/install` | 进入 [快速开始](quick-start.md) 的 ROS2 路径，或阅读 [ROS2 Demo 使用](ros2-demo.md)。 |

两条路径不要混用目录、头文件或 `.so`。同一时间只运行一个占用相机资源的应用；切换路径前先用 `Ctrl+C` 正常退出旧应用，并保持 `cam-service` 运行。

## 7. 停止应用

前台运行的 demo、ROS2 launch 或节点使用 `Ctrl+C` 正常退出，然后确认进程已结束：

```bash
pgrep -af 'sensor_demo|cam_demo|robobaton_sensors_node' || true
```

## 8. 正常关机

需要关闭设备时，在 X5 终端执行：

```bash
poweroff
```

不需要先执行 `sync`。等待系统完全退出：原本闪烁的绿色状态 LED 变为常亮，风扇保持转动；确认到这个状态后再断开外部电源。应用停止或文件系统活动期间不要直接拔电。

## 9. 故障处理

常见第一步处理：

| 现象 | 首先检查 | 下一步 |
|---|---|---|
| 无法确认地址 | 网络拓扑、开发机网段、交换机或直连链路 | 默认网口 IP 地址为 `192.168.1.12`；如果用户自行修改过 IP 地址，可通过 DEBUG_UART 进入系统查看，DEBUG_UART 必须使用 `1.8V` USB-UART 适配器。修改流程见[修改设备 IP 地址](#修改设备-ip-地址)。 |
| SSH 无法登录 | `ping <x5-ip>`、SSH 错误文本 | 见 [故障排查](troubleshooting.md#ssh-无法连接)。 |
| 相机应用启动失败 | 是否已有相机应用占用资源 | 正常退出旧应用；见 [故障排查](troubleshooting.md#相机服务或资源冲突)。 |
| 单路无图 | camera ID、线缆和供电状态 | 断电后检查连接；不要带电插拔。 |
| UART 无数据 | UART1/UART7 的 `3.3V` TX/RX/GND、共地、未接适配器 VCC | 见 [硬件连接与安全](hardware-and-safety.md)。 |
