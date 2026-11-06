# USB 接口功能与切换边界

系统已内置 `switch_usb_gadget`，用它选择 USB3 Type-C 接口的用途。配套新镜像的出厂默认是 **CDC NCM 网卡**；较旧固件可能仍默认 RNDIS，或尚不支持 NCM，请先查看 `switch_usb_gadget --help`。每次只能选择一种功能，切到摄像头、ADB 或磁盘后，USB 网卡就不能用了。

## 1. 切换前先做什么

以下命令都在**板卡的 root 终端**执行，不是在电脑 PowerShell 中执行。

```{warning}
切换会断开当前 USB 连接。请通过独立以太网或调试串口操作，不要只靠即将切断的 USB SSH。
```

先在网页停止录制，等保存完成，再按{ref}`启停说明 <non-ros-autostart>`停止采集应用。**只停止录制不够**；手动启动的相机/IMU 程序也要退出，`cam-service` 保持运行。所有手动切换和 `stop` 都会检查采集占用，不会替你关闭其他程序。

(usb-function-selection)=
## 2. 选择功能

只执行需要的一条命令：

| 想做什么 | 板端命令 | 说明 |
|---|---|---|
| USB 直连电脑上网卡 | `switch_usb_gadget ncm` | 配套新镜像的默认功能，用于 SSH、网页和传文件；电脑需支持 CDC NCM |
| 使用 RNDIS 网卡 | `switch_usb_gadget rndis` | 保留的兼容选项，电脑需支持 RNDIS；不会从 NCM 自动回退 |
| 使用 ECM 网卡 | `switch_usb_gadget ecm` | 另一种 USB 网卡协议，电脑需支持 CDC ECM |
| 当作 USB 摄像头 | `switch_usb_gadget uvc` | 四路画面拼成一个摄像头，独占相机 |
| 使用 ADB 调试 | `switch_usb_gadget adb --allow-adb` | 电脑需安装 platform-tools，仅用于可信直连 |
| 当作 USB 磁盘 | `switch_usb_gadget msd` | 默认只读，首次使用需先初始化，见下文 |
| 板卡连接 USB 外设 | `switch_usb_gadget host --host-power-confirmed` | 先确认 VBUS 和线缆供电安全，不能直接连接另一有源 Host；离开前卸载存储并退出使用外设的程序 |

也可以输入 `switch_usb_gadget` 后按提示选择。以 UVC 为例：

```console
# switch_usb_gadget
USB3: host / rndis / ecm / uvc / adb / msd / ncm / ip (configure network)
Mode (blank cancels): uvc
```

`#` 是终端提示符，不用输入。在 `Mode (blank cancels):` 后输入 `uvc` 并回车，空输入则取消。Host 会追加 `VBUS/cable power checked? Type YES:`，ADB 会追加 `Trusted direct debug link? Type YES:`；确认条件满足后才输入 `YES`。直接执行表中的完整命令则不再询问功能。

NCM 追加在原功能列表末尾，既有模式的 VID/PID 标识不变。

查看当前状态用 `switch_usb_gadget status`；重新选择同一功能也会重配 USB。USB-C 是数据接口，供电要求见 [硬件连接与安全](../getting-started/hardware-and-safety.md)。

## 3. 使用 UVC 摄像头

默认输出为 **MJPEG、1280×960、30fps 配置**：四路 `640×480` 按左上 CAM1、右上 CAM2、左下 CAM3、右下 CAM4 拼接。不包含 IMU、音频或录制文件，不能与 Web/RTSP/ROS2 相机采集同时运行。

通过独立以太网或调试串口，先停止默认应用，再切到 UVC：

```bash
cd /root/demo
./start_sensor_demo.sh stop && switch_usb_gadget uvc
```

在电脑的相机软件中选择该 USB 摄像头及 `1280×960` MJPEG 模式，检查四路画面。需要 High-Speed 或 SuperSpeed 链路；配置为 30fps 不等于实际持续达到 30fps。

**关闭电脑预览或拔线不会释放相机。** 用完后先关闭预览，再切回网卡：

```bash
switch_usb_gadget ncm && switch_usb_gadget status
```

确认切换成功、UVC 后端已退出后，按需恢复原应用：

```bash
cd /root/demo
./start_sensor_demo.sh restart
```

不需要网卡时，也可用 `switch_usb_gadget stop` 退出 UVC。切换不会自动重启原应用，也不改变开机默认值。

## 4. 网卡、ADB 和磁盘

### NCM / RNDIS / ECM 网卡

出厂板端地址为 `192.168.7.2/24`，电脑选择自动获取地址，分配范围为 `192.168.7.10–192.168.7.100`。不下发默认网关或 DNS，不自动共享上网；与有线以太网地址独立，避免电脑上已有相同网段的路由冲突。网页入口见 [首次上电](../getting-started/first-boot.md)。

电脑端必须支持所选协议；NCM 要求 CDC NCM 支持，本页不认证 Windows 兼容性。需要旧协议时可手动选择 RNDIS 或 ECM，不会自动回退。NCM 使用镜像已有的 `usb_f_ncm.ko`，本次默认值调整不重编或更换内核，也不代表已完成实板或电脑端兼容性验收。

(usb-network-address)=
### 修改 USB 网卡 IPv4 地址

配套新镜像中的 `switch_usb_gadget` 提供 `ip` 子命令；较旧固件可能没有，请先查看 `switch_usb_gadget --help`。以下命令在**板端 root 终端**执行，仅配置 NCM/RNDIS/ECM 共用的 USB 网卡地址，不修改有线以太网或 Wi-Fi 地址，也不通过 `/etc/network/interfaces` 配置 USB。

```bash
switch_usb_gadget ip
```

交互界面会显示固定的出厂值（`192.168.7.2/24`，DHCP `192.168.7.10–192.168.7.100`）、已保存值和当前配置。地址提示处直接回车接受默认值：已有保存地址时使用它，首次使用则采用出厂地址。只输入 IPv4 地址时按 `/24` 处理，也可输入带 `/8` 至 `/30` 前缀的 CIDR。最后选择保存、立即应用或取消，**默认仅保存**；选择立即应用还需显式确认。

也可直接指定地址或恢复出厂网络配置，以下命令都**仅保存**：

```bash
switch_usb_gadget ip --address 192.168.8.2/24
switch_usb_gadget ip --reset
```

按需执行其中一条。工具自动生成不包含板端地址的 DHCP 范围；如需指定，必须同时提供 `--dhcp-start` 和 `--dhcp-end`，范围须在同一子网内且不包含板端地址。不下发默认网关或 DNS。

**仅保存不重配 USB、不打断链路，无需停止采集，在任意 USB 功能下都可执行。** 配置保存到 `/etc/4p-usb-network.json`，在下次开机启用网卡或再次进入 NCM/RNDIS/ECM 时使用。该文件重启后保留，但重新烧录固件不保证保留；`/etc/4p-usb-default.json` 仍只保存开机功能选择，不保存网络地址。

USB 子网须避开板端以太网、Wi-Fi 等其他接口的 IPv4 子网。立即应用或进入网卡功能前会拒绝已检测到的板端子网重叠，避免把独立维护链路的回包改路由到 USB；仅保存不检查在线接口，仍须在实际启用前消除冲突。电脑端已有路由冲突需另行检查。

需要立即应用时，在地址命令或 `--reset` 后追加 `--apply`，例如按需选择一条：

```bash
switch_usb_gadget ip --address 192.168.8.2/24 --apply
switch_usb_gadget ip --reset --apply
```

```{warning}
`--apply` 仅允许当前功能为 NCM、RNDIS 或 ECM，保留当前模式并走原有管理器切换流程，会重配 USB、断开现有连接。须通过独立以太网或调试串口操作，按本页切换前说明正常停止录制、等保存完成并退出采集应用，保持 `cam-service` 运行。USB SSH 下默认拒绝立即应用，除非显式加 `--allow-disconnect`；该参数只是接受断线，不保证恢复连接，也不绕过停采检查。
```

应用后，电脑使用 DHCP 时需续租地址，或禁用再启用该 USB 网卡；使用静态地址时，改为与板端同子网且不同的地址，网关和 DNS 留空。随后用新的板端地址重新连接网页或 SSH。`status` 中的 `network.saved` 与 `network.active` 可区分保存配置和最近成功配置的 profile；后者不保证电脑可达。以上不代表新增硬件验证或远端版本已发布。

### ADB

切到 ADB 后，在电脑执行 `adb devices`，识别到设备后再用 `adb shell`。不要假定有 Android 式授权弹窗；用完切回网卡或停止 USB 功能。

### MSD 磁盘

首次使用先创建专用 `128 MiB` FAT 镜像 `/root/usb-share.img`；已有文件时不会覆盖：

```bash
switch_usb_gadget init-msd
switch_usb_gadget msd
```

这不是整块 eMMC、TF 卡或录制目录，也不会自动放入录包。需要电脑写入时使用 `switch_usb_gadget msd --writable`；导出期间，板端不得挂载或修改该镜像。

结束写入后，**先在电脑安全弹出并等待完成**，再执行：

```bash
switch_usb_gadget ncm --host-ejected
```

只想停止时用 `switch_usb_gadget stop --host-ejected`。`--host-ejected` 是确认已弹出，不是代替弹出；只读磁盘也建议先弹出。

## 5. 开机默认与停止

```bash
switch_usb_gadget set-default ncm
```

也可保存 `rndis` 或 `ecm`；保存 `host` 必须加 `--host-power-confirmed`。只影响下次启动，不立即切换。UVC、ADB 和 MSD 不能设为开机默认。

设置保存在 `/etc/4p-usb-default.json`，由 `/etc/init.d/S99usb.sh` 读取。安装更新时保留已有的开机选择；配套新镜像候选显式设置出厂默认值为 NCM，不表示已有设备的保存值被改写，也不表示已发布的旧镜像下载内容发生变化。正常使用不需要手动执行 `boot` 或重跑启动脚本；`boot` 会实际重配 USB，不是查询。

`switch_usb_gadget stop` 停止当前功能及本工具启动的后端，不修改默认值，也不保证把 Host 改成 Device。

## 6. 状态与排错

```bash
switch_usb_gadget status
switch_usb_gadget --help
```

| 状态字段 | 怎么看 |
|---|---|
| `role` / `requested` | 当前 Host/Device 角色 / 请求的功能 |
| `bound` | Device 通常绑定到 `35100000.usb`；Host 不需要绑定 |
| `udc_state` | `configured` 表示电脑已选择配置；`not attached` 表示未连接 |
| `speed` | `super-speed` 是协商速率，`UNKNOWN` 表示未确认；都不是持续吞吐 |
| `backend` / `default.mode` | 关联后端进程 / 已保存的开机默认值 |
| `network.saved` | 已保存的 USB IPv4/DHCP 配置，下次进入网卡功能时使用 |
| `network.active` | 最近一次成功配置的网络 profile，不是实时连通性或电脑可达性断言 |

切换失败按报错处理：退出占用程序、改用独立管理入口、核对供电，或先弹出磁盘。后端日志在 `/run/4p-usb/backend.log`，重启后不保留。不要强杀、删占用记录或手写 GPIO 绕过检查；失败后用 `status` 确认实际状态，不要假定已恢复原功能。

`--allow-disconnect` 仅表示接受 USB SSH 断线，不提供自动恢复，也不绕过其他检查；仍须准备独立维护入口。

NCM 默认值与内核模块已集成不代表电脑端枚举、收流、磁盘操作、持续吞吐、反复切换或重启验收；既有 RNDIS 检查不能认证 NCM。见{ref}`能力与验证边界 <capability-verification-boundary>`。

(usb-uvc-development)=
## 7. 修改与重编 UVC

**相机采集、拼图和 JPEG 编码在板端应用层，不在内核里。** 独立程序 `/usr/bin/x5-uvc-mosaic` 负责 USB 出图；网页只能提供控制界面，不能代替它。源码和工具位于公开 non-ROS Demo 仓的 `scripts/env_setup/x5_usb/`：

| 公开文件 | 修改入口与职责 |
|---|---|
| [`uvc_mosaic.cpp`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp) | [`Source::Start()`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp#L146-L164) 配置采集；[`Compose()`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp#L266-L298) 拼接四路；[`Encoder`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/uvc_mosaic.cpp#L340-L423) 调用硬件 JPEG 编码；`FixedControl()` / `Gadget` 处理 UVC 协商和输出 |
| [`build_uvc.sh`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/build_uvc.sh) | 独立交叉编译入口，不重编 producer 库 |
| [`switch_usb_gadget`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/switch_usb_gadget) | USB 功能管理和后端启停；[`uvc()`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/switch_usb_gadget#L384-L415) 创建 UVC 描述符并启动程序 |
| [`install.py`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/install.py) | `install(root, package)` 将已暂存工件安装到离线 rootfs，并生成 USB 清单 |
| [`S98rootfs.sh`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/S98rootfs.sh) / [`S99usb.sh`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/blob/V2_main/scripts/env_setup/x5_usb/S99usb.sh) | 根文件系统准备 / 按保存的默认值启动 USB |

在线源码链接指向 `V2_main`，需在该分支及对应 Demo 源码修订推送后才可访问；本地文件入口见 Demo README。这些文件不属于根 CMake 目标，重编 `sensor_demo`、网页或其他拼图示例不会更新 UVC。

### 独立构建

在开发机的 **`RoboBaton_4p_demo` 根目录**执行，不需要 Web 服务的 Rust 工具链：

```bash
SDK_ROOT=/path/to/platform_source_code # 改为匹配目标系统的 X5 SDK 源码树
USB_DIR=scripts/env_setup/x5_usb
OUTPUT_DIR=build_uvc
mkdir -p "$OUTPUT_DIR"
bash "$USB_DIR/build_uvc.sh" "$SDK_ROOT" "$OUTPUT_DIR/x5-uvc-mosaic" \
  --sc132-include "$PWD/include" --producer-lib "$PWD/lib"
```

必须有匹配 SDK 的 `hbre/libmm/inc`（含 `hb_media_codec.h`）、真实 AArch64 `libmultimedia.so.1` / `libhbmem.so.1`，以及 Demo 配套的 ABI3 头文件和 `libsc132.so.3`。SDK 库不在默认搜索位置时加 `--sdk-lib-dir /path/to/sdk/lib`；可用 `--cxx /path/to/aarch64-linux-gnu-g++` 和 `--sysroot /path/to/sysroot` 指定工具链。**编译器与 sysroot 必须相互匹配**，不能任意混用不同工具链的头文件和库。脚本不下载 SDK、不重编或复制 producer，也不部署板卡；一般应用编译见[公开 Demo 源码编译](../development/open-source-build.md)。

### 安装到离线系统镜像

在同一终端把三个运行脚本暂存到二进制旁，再调用安装器：

```bash
cp "$USB_DIR/switch_usb_gadget" "$USB_DIR/S98rootfs.sh" \
  "$USB_DIR/S99usb.sh" "$OUTPUT_DIR/"
python3 "$USB_DIR/install.py" \
  --rootfs /path/to/OFFLINE-rootfs --package "$OUTPUT_DIR"
```

将示例 rootfs 路径改为已解包的**离线 SDK rootfs**；`--package` 指向包含二进制和上述三个脚本的目录，不是二进制文件。安装器拒绝 `/`，不可用于正在运行的系统，也不自动上传、烧录或重启板卡。离线镜像须已具备 Python3、`adbd`、`dnsmasq`、完整 `/root/demo/lib` 及 SDK 运行依赖；安装器不代替这些依赖的交付。SDK hbre 分区库、SONAME 相对链接和配套依赖须保留。

### 更新已有板卡

| 改什么 | 需要更新什么 |
|---|---|
| 拼图顺序、图像处理，保持输出规格不变 | 重编并替换 `x5-uvc-mosaic`；拼图逻辑编在执行文件里，不是独立 SO |
| 相机库内部实现 | ABI 和依赖兼容时，成套更新 `/root/demo/lib` 下匹配的 `libsc132.so.3` 实体、链接及依赖；其他相机应用也使用该库 |
| 分辨率、帧率或格式 | 同步修改后端采集、拼图/编码缓冲和 UVC 协商、管理器 `uvc()` 的描述符，以及安装器和运行清单中的 UVC profile；不能只换 SO |

**输出规格不变且现有内核/设备树已支持所需功能时，修改应用逻辑通常不用重新烧录。** 通过独立以太网或调试串口操作，先停止录制并等保存完成，正常退出其他采集应用，再用 `switch_usb_gadget stop` 停止 UVC；确认后端已退出，保持 `cam-service` 运行。

备份旧程序、脚本、库和清单；新文件先放在目标同一文件系统的临时位置，核对架构、依赖和 SHA-256 后通过原子重命名替换，不能原地覆盖在用的执行文件或 SO。保留完整库及 SONAME 链接，同步 `/usr/share/4p-usb/manifest.json` 和受影响的应用包清单/来源记录，使其与实际工件及 profile 一致，不能只手改哈希。管理器固定启动 `/usr/bin/x5-uvc-mosaic`，迁移目录也须修改启动路径。

更新后重新启动 UVC，让电脑重新识别，检查输出格式、四路画面及切回原应用，失败时恢复备份。内核驱动或设备树支持的变化须单独更新对应系统组件。本节不代表已完成远端发布、板端部署、收流或模式切换验收。
