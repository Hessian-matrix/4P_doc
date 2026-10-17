# USB 接口功能切换

4P 底板的 USB3.0 Type-C 口工作在 USB device（gadget）模式，连接电脑后枚举为对应的 USB 设备。板端通过 `switch_usb_gadget` 命令切换该接口提供的功能，无需重启。

## 1. 可用功能

| 功能 | 作用 | 电脑端表现 |
|---|---|---|
| `rndis` | USB 虚拟网卡（RNDIS） | 枚举为 USB 网卡；板端 `192.168.7.2/24`，向电脑提供 DHCP |
| `ecm` | USB 虚拟网卡（CDC ECM） | 枚举为 USB 网卡 |
| `uvc` | USB 摄像头（UVC） | 枚举为 UVC 摄像头（1920×1080） |
| `adb` | ADB 调试 | 枚举为 ADB 设备 |
| `msd` | U 盘（Mass Storage） | 枚举为 U 盘（128 MB） |

## 2. 使用方法

命令 `switch_usb_gadget` 需要 root 权限（板端默认以 root 登录）。

### 2.1 交互式选择

不带参数运行，终端列出可用功能，输入数字选择；选定功能后再选择生效时机：

```bash
switch_usb_gadget
```

示例输出：

```text
当前功能: USB 网卡（RNDIS，含 DHCP，默认）
默认功能: （待定）
可选功能:
  1) rndis  USB 网卡（RNDIS，含 DHCP，默认）
  2) ecm    USB 网卡（CDC ECM）
  3) uvc    USB 摄像头（UVC 1920x1080）
  4) adb    ADB 调试
  5) msd    U 盘（Mass Storage，128MB）
请选择 [1-5]（回车退出）: 3
立即生效 [1] 还是 重启启动 [2]（回车取消）: 1
```

生效时机：

- **立即生效 [1]**：立即切换到所选功能；切换时 USB 连接会短暂断开并重新枚举。
- **重启启动 [2]**：把所选功能设为开机默认，下次开机生效，不改变当前运行状态。

### 2.2 直接切换（立即生效）

```bash
switch_usb_gadget rndis    # 切到 RNDIS 网卡
switch_usb_gadget uvc      # 切到 UVC 摄像头
switch_usb_gadget msd      # 切到 U 盘
```

直接指定功能名等价于交互式选择后选「立即生效」。

### 2.3 查看状态与功能列表

```bash
switch_usb_gadget status   # 查看当前功能、默认功能、GPIO 路由与网络
switch_usb_gadget list     # 列出可用功能
```

## 3. 默认功能

开机默认功能通过交互式选择的「重启启动」选项设置，存于板端 `/etc/usb_gadget_default`，下次开机生效。

| 项目 | 值 |
|---|---|
| 开机默认功能 | （待定） |
