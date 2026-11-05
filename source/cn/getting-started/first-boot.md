# 首次上电与开机使用

本页帮助第一次拿到 RoboBaton 4P 的用户完成开机前检查、上电后通过网页查看传感器数据和录包，以及按需登录 X5。发布版系统预先烧录在板端，开机自动启动 `sensor_demo`；正常预览与录包不需要手动启动程序。需要命令行或 ROS2 时，再进入 [快速开始](../quick-start.md)。部署、升级和回滚细节见 [部署、升级与回滚](../development/deployment-and-upgrade.md)，完整排障见 [故障排查](../troubleshooting.md)。

## 1. 开机前检查

供电、相机线缆、UART 和散热边界以 [硬件连接与安全](hardware-and-safety.md) 为准；接口位置、线序和对插关系见{ref}`接口接线示意图 <wiring-diagram>`。上电前确认：

- 相机 FPC/同轴线已经在断电状态下插好；相机/FPC/同轴线不支持热插拔，插拔前必须断电。
- XT30 输入为已确认的 `9~27V DC`，先核对实物正负极；USB-C 为数据接口，不将其视为供电输入。满负载电流、USB-C 电源角色和风扇阈值仍待确认，只使用产品支持确认匹配的电源与系统。
- 风扇出厂已接好；保持散热器、风扇与风道畅通，依实际系统状态检查是否就绪。
- UART1 为 GH1.25 4pin，UART7 为 GH1.25 5pin，逻辑电平保持 `3.3V`；DEBUG_UART 为 SH1.0 3pin、`1.8V`、`921600`。按接线图和实物标识核实线序；通用 USB-UART 不接 VCC，核实共地后断电连接。
- UART 供电脚额定值与热插拔条件尚待确认，默认断电接线，不向外设供电或反灌。

## 2. 连接并上电

先确认 V2 电源、线束和实际 pinout，再断电完成相机、供电、网络及可选调试线连接。上电后依实际系统状态检查就绪；不要带电插拔相机线束，不要停止或重配 `cam-service`，不要同时启动多个相机应用。

发布版系统随板预烧录，并已配置 `sensor_demo` 开机自启动。等待系统、网络和传感器就绪后，即可通过下文网页入口使用；正常使用无需重新烧录、安装运行包或再次执行自启动 `enable`。默认启动用于采集与预览，不会自动录包；需要保存时在网页中开始录制。不要再手动启动第二个 `sensor_demo`、`cam_demo` 或 ROS2 相机节点。

当前匹配镜像同时预装 `/root/demo`、`/root/ros2_demo/install` 和 `/opt/ros/humble`；ROS2 不自启，也不需要首次开机解压安装。开机默认是四路 `1280x1088@30fps`、IMU `800Hz`、Web 开、RTSP 关、observer/host 赋时。镜像组成与公开下载状态见 [系统烧录](../ops/system-flashing.md)。

## 3. 网络和登录

配套新镜像在没有既有 Wi-Fi 状态时默认开启 `RoboBaton-4P` WPA2 热点，使用 5 GHz 信道 `36`（20 MHz、非 DFS）；支持 5 GHz 的电脑或手机使用随设备提供的热点密码连接，并自动获取地址后，可打开 `http://192.168.5.1/` 预览和录包。AP 可手动选择 2.4 GHz 或 5 GHz，一次只运行一个频段，不自动回退；客户端或法规不允许当前频段时，通过有线以太网或调试串口重新配置。普通重启保留已有 AP/STA、频段/信道或手动关闭选择，重烧 system 恢复新镜像的 5 GHz 默认值；较旧固件可能没有此策略，本说明不表示已发布下载已替换。完整信道、监管限制、`12` 小时 DHCP 租期、配置与恢复方法见{ref}`出厂热点与快速连接 <wifi-factory-hotspot>`。切换 Wi-Fi 模式会断开同一条 Wi-Fi SSH，不要依赖它完成切换。

需要 USB 直连电脑时，配套新镜像出厂默认配置 USB3 CDC NCM 网卡，出厂板端地址为 `192.168.7.2/24`，电脑选择自动获取地址。电脑必须支持 CDC NCM，Windows 兼容性尚未认证；RNDIS/ECM 仍可手动选择，不自动回退。较旧固件可能仍默认 RNDIS 或不支持 NCM，先查看 `switch_usb_gadget --help`；安装更新保留已有的开机选择。USB 地址与有线以太网独立，不是默认 USB 摄像头或 U 盘。修改地址见下文[修改设备 IP 地址](#修改设备-ip-地址)；切换 Host/Device 和具体 USB 功能见 [USB 接口功能与切换边界](../usage/usb-gadget-switch.md)。不要在唯一 USB 管理链路上切换。

V2 保持有线以太网出厂地址 `192.168.1.12/24` 和 `root` 账号/密码，有线以太网配置继续使用 `/etc/network/interfaces`。这是公开出厂设置，不是实验设备的实际地址或凭据。

| 项目 | 出厂默认值 |
|---|---|
| 有线以太网 IP | `192.168.1.12` |
| 用户 | `root` |
| 密码 | `root` |


### 配置开发机以太网

设备出厂地址为 `192.168.1.12/24`。直连设备或通过隔离交换机连接时，开发机以太网网卡需要使用 `192.168.1.0/24` 内未被占用的地址，例如 `192.168.1.100/24`。不要把开发机地址设为 `192.168.1.12`，也不要使用该网络中已经被其他设备占用的地址；直连或隔离网络不需要配置网关和 DNS。若开发机已有其他活动网卡或路由占用 `192.168.1.0/24`，先避免路由冲突再测试。

Linux 临时配置示例：

```bash
ETHERNET_IFACE=enp1s0  # 改成实际开发机以太网接口
ip link
sudo ip addr add 192.168.1.100/24 dev ${ETHERNET_IFACE}
sudo ip link set ${ETHERNET_IFACE} up
ping -c 4 192.168.1.12
```

`ip addr add` 设置是临时地址，重启或网络服务重启后会消失；如果该地址已经配置在网卡上，不要重复添加。

Windows 图形界面配置：

- Settings -> Network & Internet -> Ethernet -> IP assignment -> Edit -> Manual -> IPv4。
- IP 填 `192.168.1.100`，subnet mask 填 `255.255.255.0`，直连或隔离网络下 gateway/DNS 留空。
- 在 PowerShell 或 cmd 中执行 `ping 192.168.1.12` 验证连通性。

(first-boot-web)=

### 通过网页查看传感器与录包

网络连通后，在开发机浏览器地址栏输入当前连接对应的板端 HTTP 地址：出厂热点为 `http://192.168.5.1/`，有线以太网为 `http://192.168.1.12/`，出厂 USB 网卡为 `http://192.168.7.2/`。已修改地址或使用 STA 时，使用实际板端地址；HTTP 默认端口为 `80`，显式修改后使用实际端口。网页资源随程序内嵌，不需要互联网、插件或摄像头/麦克风权限；在线文档链接需要互联网。**无需先 SSH 登录或手动启动程序。**

**使用手机或平板进行效果预览**：

1. 直接连接板卡出厂热点；也可将板卡接入局域网，手机或平板连接同一路由器的 Wi-Fi。后者无需板卡自身开启 Wi-Fi，但须能互访；访客网络或 AP 客户端隔离可能阻止连接。
2. 连接板卡出厂热点时打开 `http://192.168.5.1/`；经局域网访问时使用板卡当前局域网地址，出厂有线地址为 `http://192.168.1.12/`。地址或端口已修改时使用实际值。无需专用 App 或 SSH 登录。
3. 等待四路画面和 IMU 更新；手机窄屏纵向排列面板，可上下滚动，横屏可获得更宽的预览。若自动播放被阻止，点击画面中的“点击播放”。

移动预览用于查看效果，不是手机本机录像或同步/性能验收。实际播放流畅度取决于无线网络、设备性能和浏览器 WebRTC/H.264 解码支持，不保证所有手机或浏览器四路同时流畅。录制操作仍在板端执行，关闭网页不会停录；只在可信局域网使用，不要将无认证页面映射到公网。

```{figure} ../../image/4P_overview.png
:alt: RoboBaton 4P 网页设备总览，包含 CAM1 至 CAM4、惯性姿态、六轴原始遥测及录制与保存
:width: 100%
:align: center

开机网页效果图（中文界面）：四路相机、惯性姿态、六轴原始遥测和录制与保存集中在同一首页；右上角可切换 `CH` / `EN`。画面、数值和录制状态以当前设备为准。
```

1. **查看传感器数据**：确认 CAM1～CAM4 画面持续更新，并查看惯性姿态、加速度、角速度及温度。姿态为浏览器六轴融合预览，不代表绝对航向或硬件同步验收。
2. **选择录包选项**：在右侧“录制与保存”选择 `ROS bag` 或 `MP4 · 四路 H.264`，以及“运行目录 / eMMC”或“TF 卡”。TF 必须已挂载，缺卡不会自动退回 eMMC；网页录包使用固定目录，不支持自定义路径。
3. **开始录制**：点击“开始录制”，等待设备确认，观察实际状态、设备计时时长及已写入量。状态未就绪或报错时，先查看提示，不要反复点击。
4. **停止并确认结果**：点击“停止录制”，等待排空与封装完成，再展开“录制详情与使用说明”检查输出路径和最终结果。只有 `published_complete`、`data_complete=true`、`cleanup_complete=true` 才表示会话完整发布；停止请求被接受不等于文件已经完成。路径位于板端，不是浏览器下载目录。

网页选择“运行目录 / eMMC”时固定保存到 `/root/demo/save_data`，不随可执行文件位置变化：bag 为 `/root/demo/save_data/session-<id>.bag`，MP4 为 `/root/demo/save_data/session-<id>`；TF 目录仍为 `/mnt/sdcard/recordings`，会话名由设备生成。关闭网页、刷新或断网**不会停止设备录制**；重新打开后使用“查询状态”确认。停止录制不会停止相机、IMU 与预览；切换应用时还须正常停止整个 `sensor_demo`。操作细节见 [网页控制录制](../usage/non-ros-demo.md#网页控制录制) 和 [数据保存](../usage/save-data-guide.md)。需要 UTC 时间的录包，开始前先按 [NTP 同步](../time-sync/ntp-sync.md) 确认授时。

```{warning}
网页没有身份认证，能够访问设备的人都可以查看传感器和开始/停止录制。只在可信隔离局域网内使用，不要开放到公网或不可信网络。
```

### 修改设备 IP 地址

先区分需要修改的接口：USB 网卡和有线以太网地址独立，使用不同的配置方式。USB 配置命令须在**板端 root 终端**执行，不是在电脑终端直接执行。

#### USB 网卡（NCM / RNDIS / ECM）

配套新镜像提供 `ip` 子命令，旧固件先用 `switch_usb_gadget --help` 确认是否支持。通过当前可达的地址 SSH 登录板端后，执行交互配置：

```bash
switch_usb_gadget ip
```

地址和 DHCP 提示处回车接受显示的默认值；已有保存配置时使用它，首次使用采用出厂值。最后在 `save / apply / cancel [save]` 提示处回车为**仅保存**。也可直接保存指定地址，例如：

```bash
switch_usb_gadget ip --address 192.168.8.2/24
```

仅保存不打断当前 USB 连接或采集；配置写入 `/etc/4p-usb-network.json`，重启后保留，在下次启用 NCM/RNDIS/ECM 时使用，**不修改 `/etc/network/interfaces`**。新子网须与板端以太网、Wi-Fi 及电脑已有路由避开冲突。

立即生效会断开 USB，须先正常停采，并使用独立以太网或调试串口；不要在唯一 USB SSH 链路上选择 `apply`。完整的 `--apply`、DHCP 范围、恢复出厂地址、状态查看和电脑续租/重连方法见{ref}`修改 USB 网卡 IPv4 地址 <usb-network-address>`。

#### 有线以太网

需要调整有线以太网 IP 时，先用当前可达地址 SSH 登录设备，再修改系统网络配置：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
ssh root@${X5_IP}
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

如果用户修改过 IP 且需要通过调试口进入系统查看地址，只能使用 DEBUG_UART：`1.8V` 逻辑，调试终端波特率设置为 `921600`，板端 TX 接适配器 RX，板端 RX 接适配器 TX，并共地。禁止在 DEBUG_UART 使用 `3.3V` 或 `5V` USB-UART。

```{note}
随板的发布版系统提供上述开机使用流程，无需先重新烧录。需要重刷时，可下载 [4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz)；发布包 SHA-256 与适用硬件须在烧录前向产品支持核对。当前固件支持按住 SW1 上电或复位，再通过 USB3 Fastboot 使用 XBurn 烧录，无需调试串口；操作、镜像与硬件匹配要求见[系统烧录](../ops/system-flashing.md)。烧录前须备份数据；正式烧录会覆盖板载 eMMC 与用户数据，不是正常开机使用的前置步骤。
```

### 调试串口免密登录

已集成该功能的系统镜像提供 `uart-autologin`。以 `root` 执行：

```bash
uart-autologin status    # 查看状态
uart-autologin disable   # 下次调试串口登录要求用户名和密码
uart-autologin enable    # 下次调试串口登录免密进入 root
```

配套新实现缺省启用免密登录；能接触 DEBUG_UART 的人可直接获得 root，仅适用于可信物理环境。选择保存在系统分区 `/etc/4p/uart-autologin/state`：普通重启保留，重烧 system 恢复镜像默认值，不导入旧 userdata 策略。不影响已有会话、SSH 或 UART1/UART7。旧固件可能仍使用 userdata；命令不存在时联系产品支持，仅复制 Demo 脚本不会启用该功能。

## 4. 最小系统检查

登录 X5 后执行：

```bash
hostname
date
df -h /
pgrep -a cam-service
```

期望 `hostname`、`date` 和根文件系统空间可正常返回，且能看到 `cam-service` 进程。若 `cam-service` 缺失或异常，先按 [故障排查](../troubleshooting.md) 收集现象，不把停止服务作为常规恢复步骤。

如果板卡可以访问公网或自建局域网 NTP 服务器，应在开始录包或其他时间戳敏感操作前确认系统已完成授时；开机预览已经运行不代表授时完成。具体步骤见 [NTP 同步](../time-sync/ntp-sync.md)。NTP 不强制要求互联网。

## 5. 确认版本

只在对应目录已经部署时查询版本；这些命令不应启动相机或 IMU。

non-ROS `/root/demo`：

```bash
/root/demo/cam_demo --version
/root/demo/sensor_demo --version
```

ROS2 `/root/ros2_demo/install`：

```bash
/root/ros2_demo/install/robobaton_ros2_env.bash \
  /root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_sensors_node --version
/root/ros2_demo/install/robobaton_ros2_env.bash \
  /root/ros2_demo/install/lib/robobaton_4p_ros2_demo/robobaton_imu_rate_monitor --version
```

ROS2 即使只查询版本也需加载 underlay/overlay 依赖。不要在未加载环境的 shell 直接运行 install 内 ELF；缺少 `libimage_transport.so` 等库时，先使用上述 wrapper，不从其他包复制单个 SO。

软件查询结果以已部署包为准，可能不带 `v` 前缀；当前软件发布版本见 [发布、授权与支持](../release-and-support.md)。文档修订号按该页的 [文档版本政策](../release-and-support.md#文档版本政策) 独立维护，不要求与软件查询结果相等。

## 6. 选择 non-ROS 或 ROS2

| 目标 | 运行目录 | 下一步 |
|---|---|---|
| 网页查看四路相机、IMU 与录包 | 开机自启的 `/root/demo/sensor_demo` | 直接使用上文{ref}`网页入口 <first-boot-web>`，不重复启动应用。 |
| 四路 RTSP、IMU、UART 示例 | `/root/demo` | 进入 [快速开始](../quick-start.md) 的 non-ROS 路径，或阅读 [non-ROS Demo 使用](../usage/non-ros-demo.md)。 |
| ROS2 raw/compressed 图像、CameraInfo、IMU、温度 topic | `/root/ros2_demo/install` | 进入 [快速开始](../quick-start.md) 的 ROS2 路径，或阅读 [ROS2 Demo 使用](../usage/ros2-demo.md)。 |

两条路径不要混用目录、头文件或 `.so`。同一时间只运行一个占用相机资源的应用；切换到其他 demo 或 ROS2 前，先停止录制并等待完整收尾，再按下节正常停止开机自启的 `sensor_demo`，保持 `cam-service` 运行。

## 7. 停止应用

发布版开机自启的程序在后台运行。需要切换到其他相机应用时，先在网页停止录制并确认最终结果，再通过 X5 SSH 终端执行：

```bash
cd /root/demo
./start_sensor_demo.sh stop
```

等待命令成功返回；失败时先检查提示，不要强杀或继续启动另一实例。此命令不取消下次开机自启，也不操作 `cam-service`。需要恢复网页使用时，执行 `./start_sensor_demo.sh restart` 并检查实际页面；完整说明见{ref}`启停与开机自启动 <non-ros-autostart>`。网页“停止录制”只停止保存，关闭网页也不会退出应用。

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
| 网页无法打开或没有实时数据 | 当前 IP、HTTP `80`（或实际端口）、媒体 UDP/TCP `8189`、自启状态 | 登录后执行 `/root/demo/start_sensor_demo.sh status`，检查 `/userdata/sensor_demo_autostart.log`；不要重复启动或停止 `cam-service`，见 [局域网预览无画面或 IMU 失效](../troubleshooting.md#局域网预览无画面或-imu-失效)。 |
| SSH 无法登录 | `ping 192.168.1.12`（按实际板卡地址修改）、SSH 错误文本 | 见 [故障排查](../troubleshooting.md#ssh-无法连接)。 |
| 相机应用启动失败 | 是否已有相机应用占用资源 | 正常退出旧应用；见 [故障排查](../troubleshooting.md#相机服务或资源冲突)。 |
| 单路无图 | camera ID、线缆和供电状态 | 断电后检查连接；不要带电插拔。 |
| UART 无数据 | UART1/UART7 的 `3.3V` TX/RX/GND、共地、未接适配器 VCC | 见 [硬件连接与安全](hardware-and-safety.md)。 |
