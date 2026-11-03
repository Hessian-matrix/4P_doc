# USB 接口功能与切换边界

更新后的匹配 V2 Buildroot 镜像提供 `switch_usb_gadget`，在同一 USB3.0 Type-C 控制器上切换 **Host** 与 **Device（gadget）**；Device 每次只启用 RNDIS、CDC ECM、UVC、ADB、MSD 中的一项。默认仍为 RNDIS，适合电脑直连、SSH、网页预览和文件传输。

USB 功能由匹配的 BSP/系统镜像提供，不随 non-ROS 或 ROS2 应用包安装。旧镜像只有 `x5-usb-rndis` 时，不会因更新文档或应用包自动获得此功能；也不要混用旧 SDK gadget 脚本、GPIO386 路由脚本或旧 `/etc/usb_gadget_default` 文件。

## 1. 先确认镜像与安全条件

在板端执行只读检查：

```bash
command -v switch_usb_gadget
switch_usb_gadget status
cat /usr/share/4p-usb/manifest.json
```

新工具要求匹配的新版底板设备树标记及 Linux USB role-switch 接口；不匹配时拒绝执行。`status` 显示实际角色、请求功能、UDC 绑定、连接状态、协商速度、后端进程身份和开机默认值。请求功能或后端进程存在不等于电脑枚举成功。`not attached` / `UNKNOWN` 表示当前没有建立连接，不能据此认定功能缺失。

```{warning}
切换或停止功能会断开 USB 网络、SSH、网页、ADB 或磁盘。先准备已确认可用的独立以太网或调试串口维护入口；不要在唯一 USB 管理链路上操作。正常收尾录制并退出采集应用，不能直接中断开始、录制或收尾中的会话，也不要停止或重配 `cam-service`。
```

工具拒绝已知采集 owner、其他 gadget owner，以及 Host 下已挂载或被进程打开的 USB 设备。它只正常停止自己启动且进程身份仍匹配的后端，不强杀其他进程。此保护不能识别任意第三方程序或阻止工具外的并发写入，用户仍须保证资源独占。

USB-C 为数据接口，供电、电平与线缆条件见 [硬件连接与安全](../getting-started/hardware-and-safety.md)。Host 软件角色不证明已具备安全的 VBUS 输出或 USB-C/PD 供电能力。切换 Host 前，须按产品支持确认的接线与供电方案检查，禁止与另一有源 Host 直接冲突连接。

## 2. 功能选择

root 可直接执行命令，也可运行不带参数的 `switch_usb_gadget` 输入功能名；空输入取消。Host 与 ADB 的交互选择还会要求安全确认。下列命令均会改变当前 USB 功能，不能把它们当作只读检查连续运行。

| 功能 | 板端命令 | 使用边界 |
|---|---|---|
| Host | `switch_usb_gadget host --host-power-confirmed` | 接入受支持的 USB 外设；先确认 VBUS/线缆安全。离开 Host 前，正常卸载存储并关闭使用该外设的程序 |
| RNDIS | `switch_usb_gadget rndis` | 虚拟网卡，电脑须有匹配 RNDIS 驱动 |
| CDC ECM | `switch_usb_gadget ecm` | CDC ECM 虚拟网卡，电脑须有匹配 ECM 驱动 |
| UVC | `switch_usb_gadget uvc` | 四目真实相机拼为一路 MJPEG，独占相机资源；见下节 |
| ADB | `switch_usb_gadget adb --allow-adb` | 仅可信直连调试；暴露调试访问，不承诺 Android 式授权弹窗 |
| MSD | `switch_usb_gadget msd` | 导出专用 FAT 镜像，默认只读；须先初始化，见下节 |

若通过该 USB 网卡 SSH 操作，工具默认拒绝断链；`--allow-disconnect` 是显式断链许可，不提供自动恢复或回滚。只有独立恢复入口确实可用时才考虑此选项。

### RNDIS / CDC ECM 网络

两种网卡都使用板端 `192.168.7.2/24`，USB 专用 DHCP 给电脑分配 `192.168.7.10–192.168.7.100`，不下发默认网关或 DNS，不自动共享上网。地址与有线以太网独立；电脑选择 USB 网卡自动获取地址，存在同网段路由冲突时先解决冲突。板端 Web 服务运行时可通过此地址访问，实际端口与应用版本仍需匹配，见 [首次上电](../getting-started/first-boot.md)。

“USB3 控制器”不等于协商到 SuperSpeed；以实际连接、`current_speed`、电脑端枚举和收发为准，网卡显示速率不代表持续吞吐。

### UVC 四目预览

`x5-uvc-mosaic` 使用真实 SC132 完整四目组，将四路 `640×480` 画面按 **左上 CAM1、右上 CAM2、左下 CAM3、右下 CAM4** 拼为 `1280×960`，由 X5 硬件 JPEG 编码器输出一路 MJPEG，描述符为 `30fps`。不是四个独立 USB 摄像头，不含 IMU、音频或录制文件，也不与已有 Web/RTSP/ROS2 相机采集同时运行。

先正常停止采集应用，再选择 UVC；电脑使用支持 MJPEG 的相机软件选择相应设备及 `1280×960` 模式。该配置要求 High-Speed 或 SuperSpeed 链路，不承诺 Full-Speed。后端就绪只说明输出节点、事件订阅和采集启动已完成，不证明电脑已收到图像或达到持续 30fps；必须在电脑实际查看四个画面。停止后端及切换功能后，再按需正常启动原应用。

### ADB 调试

电脑需要 Android platform-tools 及匹配驱动。选择 ADB 后在电脑执行 `adb devices`，实际连通后才使用 `adb shell`。ADB 可能提供高权限访问，只用于可信直连；使用完切回 RNDIS 或停止 USB 功能。不要把后端运行或 FunctionFS 挂载当作电脑已连接/已授权的证据。

### MSD 专用磁盘

初始化仅创建新的 `128 MiB` FAT backing image `/root/usb-share.img`，已有文件时拒绝覆盖；不导出根分区、TF 卡或已有录制目录，也不会自动把录包复制进去：

```bash
switch_usb_gadget init-msd
switch_usb_gadget msd
```

需要由电脑写入时，显式执行 `switch_usb_gadget msd --writable`。镜像不能同时在板端挂载或被本地进程使用；工具检查 loop owner 和直接打开者，但不能代替用户维持独占。不要在导出期间本地挂载或修改 backing 文件，即使电脑侧是只读。

结束可写导出时，**先在电脑安全弹出磁盘并等待完成**，再执行：

```bash
switch_usb_gadget rndis --host-ejected
# 或仅停止当前功能：switch_usb_gadget stop --host-ejected
```

`--host-ejected` 是用户对电脑已完成弹出的确认，板端不能自动验证。未弹出不得用该参数绕过保护；拔线或停止服务不是安全弹出的替代。默认只读导出也建议先弹出。

## 3. 开机默认值与停止

仅允许将 Host、RNDIS 或 ECM 设置为开机默认，保存不立即切换当前功能：

```bash
switch_usb_gadget set-default rndis
# 也可选择 ecm；Host 必须确认接线与供电：
# switch_usb_gadget set-default host --host-power-confirmed
```

设置保存到 `/etc/4p-usb-default.json`，由唯一启动入口 `/etc/init.d/S99usb.sh` 调用 `switch_usb_gadget boot` 读取。出厂候选默认 RNDIS；开机网络初始化独立于传感器应用，不接管相机。UVC、ADB、MSD 不作为开机默认，避免意外抢占相机、暴露调试或磁盘。新镜像构建不改变已烧录设备的默认值。

`switch_usb_gadget stop` 解绑并移除本工具拥有的功能、正常停止其后端；可写 MSD 仍须先安全弹出并传 `--host-ejected`。`stop` 不修改持久默认值，也不保证将 Host 角色改为 Device。操作失败会明确报错；已向电脑暴露的切换不会伪称自动恢复了旧功能，应通过独立维护入口检查状态后恢复。

## 4. 验证边界

新增镜像包含工具、后端和匹配依赖，不等于已烧录或完成实板验收。Host 外设枚举、RNDIS/ECM 地址与实际双向收发、UVC 四目收流、ADB 连接、MSD 读写/弹出、反复切换和整机重启后默认值，仍须在匹配板卡和电脑端逐项确认。既有 USB 状态相关/双向不对称吞吐与重新枚举问题不因此自动关闭，不作持续性能保证；见{ref}`能力与验证边界 <capability-verification-boundary>`。
