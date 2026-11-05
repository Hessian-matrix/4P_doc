# 系统烧录

(system-flashing)=

```{warning}
当前镜像支持 **按住 SW1 上电/复位，通过 USB 进入 Fastboot 烧录**，无需连接 DEBUG_UART。烧录可能覆盖板载 eMMC 系统与用户数据，操作前先备份，并核对镜像适用硬件及交付校验值。镜像下载入口见下表；本页暂未提供发布包 SHA-256，不使用来源不明或不匹配的镜像。
```

## V2 镜像发布状态

| 项目 | 状态 |
|---|---|
| V2 出厂系统镜像 | 已完成制作，已在烧录设备上检查启动后的系统与预装应用；不等于全部整机验收 |
| 镜像包标识与下载 | `V2.0.0`：[4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz)；镜像包标识与软件、文档版本分别识别 |
| SHA-256 与适用硬件 | 本页暂未提供发布包 SHA-256；烧录前向产品支持核对校验值与适用硬件 |
| 烧录工具与连接 | XBurn；SW1 按键＋USB 3.0 数据线，无需 DEBUG_UART |
| 烧录步骤与配置图 | 见下文；截图中的镜像路径为示例，以实际交付目录为准 |

从上表下载完整镜像包，烧录前核对适用硬件与发布方提供的 SHA-256。无法确认匹配、取得校验值或进入烧录模式时联系[产品支持](../release-and-support.md)。

## 按键＋USB 烧录

### 1. 准备镜像与连接

1. 准备 Windows 电脑、XBurn、可传数据的 USB 3.0 线，以及匹配本板的完整镜像包。电脑须已安装 XBurn 所需的 USB 驱动。
2. 校验下载包的 SHA-256 后完整解压；若包内提供 `SHA256SUMS`，继续核对文件清单。不要从压缩包内直接选择文件，不混用不同镜像包的分区文件。
3. 正常结束采集和保存，备份所需数据，再关闭设备电源。用 USB 数据线连接电脑与板卡 USB3 接口；板卡仍须使用配套电源供电。
4. **先按住 SW1，再给板卡上电或复位；保持按住，直到电脑/XBurn 识别 Fastboot 设备后松开。** 不需要调试串口线。正常开机后的 NCM/RNDIS/ECM 网络设备不是 Fastboot 烧录设备。

### 2. 配置 XBurn

下图按操作顺序标出需要核对的配置项；图中路径仅作示例。

```{figure} ../../image/flash_config.png
:alt: XBurn 按键加 USB 烧录配置，突出 X5、USB、Fastboot、Emmc、secure、镜像目录、USB 3.0 和 Start Burn

按键＋USB 烧录配置（XBurn v1.2.1 原始窗口布局，800 × 882）
```

| 图中编号 | 配置项 | 设置或操作 |
|---|---|---|
| 1 | Product Type | `X5` |
| 2 | Link Type | **`USB`** |
| 3 | Download Mode | **`Fastboot`** |
| 4 | Storage | `Emmc`（eMMC） |
| 5 | Firmware Type | `secure` |
| 6 | Image Directories / Browse | 选择解压后的完整镜像目录；若交付包使用 `package` 子目录，选择该目录，不选压缩包或单个 `.img` |
| 7 | Enable USB 3.0 Mode | **勾选**，使用 USB 3.0 烧录模式 |
| 8 | Start Burn | 确认设备已识别、配置与镜像目录无误后点击 |

```{warning}
`Full eMMC erase` 不要默认勾选。分区备份/恢复、指定分区烧录等选项仅按匹配镜像的交付说明设置；未选择全盘擦除也不等于保证用户数据保留。写入期间保持电源和 USB 连接稳定，不拔线、不按复位键。
```

### 3. 烧录与重新启动

1. 点击 **Start Burn**，等待 XBurn 报告烧录成功；未成功时不要将进度条或部分分区完成当作整包成功。
2. 图示已勾选 `Reboot after burning`，成功后设备会自动重启。若未勾选，则在烧录成功后按工具提示重新启动；**正常启动时不要按住 SW1**，否则会再次进入 Fastboot。
3. 等待系统启动，按[首次上电](../getting-started/first-boot.md)检查网络、预装应用和版本。重新烧录后使用镜像默认配置，不假定旧网络设置或用户数据仍在。
4. 未识别设备时，先核对供电、USB 数据线/接口、USB 驱动及“先按住 SW1 再上电”的顺序；仍失败时停止写入并联系[产品支持](../release-and-support.md)。


## 当前镜像与开机行为

当前匹配镜像使用 Buildroot `2022.08`、Linux `6.1.83-DR-PL5.1_V1.1.2`（AArch64）。可先用以下只读命令识别实际系统；`/etc/version` 是镜像构建标识，不是 Demo 软件版本或公开下载包版本：

```bash
cat /etc/version
cat /etc/os-release
uname -r
cat /usr/share/4p-applications/manifest.json
```

| 组成 | 当前镜像行为 |
|---|---|
| 网络与登录 | 有线出厂 IP 为 `192.168.1.12/24`，账号/密码为 `root` / `root`；修改地址后使用实际地址，不改变其他设备的出厂默认值 |
| non-ROS | `/root/demo` 已预装，开机自动启动 `sensor_demo`；默认四路 `1280x1088@30fps`、IMU `800Hz`、Web 开、RTSP 关、不自动录制，时间戳组合为 observer/host |
| ROS2 | `/root/ros2_demo/install` 与 `/opt/ros/humble` 已预装，不依赖首次启动解压，不自动启动采集；使用包内环境脚本，运行前先正常退出 non-ROS |
| 系统依赖 | 镜像提供 Python `3.10.12`、C++/SDK 运行库，以及 Wi-Fi、调试串口策略、温控与 USB 管理工具；不是仅复制两个应用目录即可补齐的内容 |
| USB | 配套新镜像候选的出厂开机默认是 USB3 Device/CDC NCM；较旧固件可能仍默认 RNDIS 或不支持 NCM，不能据此认定上方已发布下载已更新。板端 USB 地址 `192.168.7.2/24` 与有线独立；电脑须支持 CDC NCM，Windows 兼容性尚未认证，RNDIS/ECM 可手动选择而不自动回退。详见 [USB 使用与切换](../usage/usb-gadget-switch.md) |
| Wi-Fi | 配套新镜像在系统分区 `/etc/4p/wifi` 无状态时初始化 `RoboBaton-4P` WPA2 热点，默认 5 GHz 信道 `36`（`AP_CHANNEL=36`，20 MHz、非 DFS），沿用随设备提供的密码；板端 `192.168.5.1/24`，DHCP `192.168.5.2–192.168.5.254`、租期 `12` 小时并自动续租，连接后打开 `http://192.168.5.1/`。AP 可选 2.4/5 GHz，一次一个频段，不自动回退；实际驱动与监管限制为准。普通重启保留 AP/STA、频段/信道与停用选择，重烧 system 恢复镜像的 5 GHz 默认值，不读取旧 userdata 配置；USB DHCP 独立。较旧固件可能没有此策略，不表示上方旧下载已更新或新增实板验收。信道与限制详见{ref}`出厂热点与快速连接 <wifi-factory-hotspot>` |
| 系统时间 | `ntpd` 开机运行不代表已同步。无可达时间源时日期可能仍为初始值，录制前按 [NTP 同步](../time-sync/ntp-sync.md) 检查 |
| 配置生命周期 | 配套新实现将 Wi-Fi、串口免密和 Demo 自启设置存入 `/etc/4p`；USB、DNS、有线及应用 YAML 原本位于 system。普通重启保留手动设置，重烧 system 后均以镜像内容为准；即使保留 userdata，也不导入旧 Wi-Fi、串口或自启注册状态。数据保存路径不变，不为重置配置删除 bag、MP4 或日志。旧镜像行为以其交付说明为准；仅替换 Demo 包不足以完成系统入口切换。 |

先按 [首次上电](../getting-started/first-boot.md) 使用预装应用，不重复安装或启动第二实例。当前烧录设备已检查 non-ROS/ROS2 哈希清单、实际 non-ROS 加载库和 ROS2 环境下版本查询；这些检查不替代 ROS2 topic/DDS、全部 USB 模式、保存、长测或反复重启验收。镜像是否适配以实际交付说明和校验值为准，不根据软件或文档版本推测。

## 运行包更新

只更新 non-ROS 或 ROS2 运行包不需要烧录系统，使用[部署、升级与回滚](../development/deployment-and-upgrade.md)。软件版本、文档修订号与系统镜像版本分别识别，不因本页说明自动改变。
